#include <google/protobuf/stubs/common.h>
#include <signal.h>
#include <unistd.h>  // For debug sleep()

#include <atomic>
#include <chrono>
#include <iostream>
#include <mutex>
#include <thread>
#include <vector>
#include <zmq.hpp>

#include "AV_TO_GCS_DATA_1.hpp"
#include "AV_TO_GCS_DATA_1.pb.h"
#include "AV_TO_GCS_DATA_2.hpp"
#include "AV_TO_GCS_DATA_2.pb.h"
#include "AV_TO_GCS_DATA_3.hpp"
#include "AV_TO_GCS_DATA_3.pb.h"
#include "FlightState.pb.h"
#include "GCS_TO_AV_STATE_CMD.hpp"
#include "GCS_TO_GSE_STATE_CMD.hpp"
#include "GSE_TO_GCS_DATA_1.hpp"
#include "GSE_TO_GCS_DATA_2.hpp"
#include "sequence.hpp"
#include "subprocess_logging.hpp"
#include "test_interface.hpp"
#include "uart_interface.hpp"

// This file hosts the ZeroMQ IPC server stuff

std::atomic<bool> running{true};
volatile bool debugger_attached = false;

// Thread safe signal handler
void signal_handler(int) {
  slogger::info("Signal received, stopping server");
  running = false;
}

inline void set_thread_name([[maybe_unused]] const char *name) {
#ifdef __APPLE__
  pthread_setname_np(name);
#endif
}

std::string vectorToHexString(const std::vector<uint8_t> &data,
                              const ssize_t BUFFER_BYTE_COUNT) {
  std::ostringstream oss;
  oss << std::uppercase << std::hex << std::setfill('0');
  if (BUFFER_BYTE_COUNT == 0) {
    return "Empty vector";
  }
  if (BUFFER_BYTE_COUNT > 255) {
    return "Vector too long: " + std::to_string(BUFFER_BYTE_COUNT);
  }
  if (BUFFER_BYTE_COUNT < 0) {
    return "Vector too short: " + std::to_string(BUFFER_BYTE_COUNT);
  }
  for (ssize_t i = 0; i < BUFFER_BYTE_COUNT; ++i) {
    oss << std::setw(2) << static_cast<int>(data[i]);
    if (i != BUFFER_BYTE_COUNT - 1) oss << " ";
  }
  return oss.str();
}

template <typename PacketType>
std::unique_ptr<PacketType> process_packet(const ssize_t BUFFER_BYTE_COUNT,
                                           std::vector<uint8_t> &buffer,
                                           zmq::socket_t &pub_socket) {
  // SIZE does not include ID byte that's already been read
  if (BUFFER_BYTE_COUNT >= PacketType::SIZE + 1) {
    try {
      // Construct the packet object (skipping the ID byte)
      std::unique_ptr<PacketType> payload =
          std::make_unique<PacketType>(&buffer[1]);

      // Convert to protobuf and serialize to a string
      auto proto_msg = payload->toProtobuf();
      if (!proto_msg.IsInitialized()) {
        std::string missing_info = proto_msg.InitializationErrorString();
        slogger::warning(std::string(PacketType::PACKET_NAME) +
                         ": Not all fields are initialized in the protobuf "
                         "message. Missing: " +
                         missing_info);
      }
      // Run sequence related updates
      std::string serialized;
      if (proto_msg.SerializeToString(&serialized)) {
        zmq::message_t msg(serialized.data(), serialized.size());
        pub_socket.send(msg, zmq::send_flags::none);
      } else {
        slogger::error(
            std::string(PacketType::PACKET_NAME) +
            ": Failed to serialize and send to string with protobuf");
        return nullptr;
      }
      return payload;
    } catch (const std::exception &e) {
      slogger::error(std::string(PacketType::PACKET_NAME) +
                     ": Error processing payload: " + e.what());
    } catch (...) {
      slogger::error("Caught unknown exception while processing payload");
    }
  } else {
    // This may be fixed 32 bytes every time. Not sure if can be different
    slogger::error(std::string(PacketType::PACKET_NAME) +
                   ": Incorrect packet size. Expected: " +
                   std::to_string(PacketType::SIZE + 1) + " bytes, got: " +
                   std::to_string(BUFFER_BYTE_COUNT) + " bytes");
    slogger::debug("Buffer contents: " +
                   vectorToHexString(buffer, BUFFER_BYTE_COUNT));
  }
  return nullptr;
}

void post_process_av(Sequence &sequence,
                     const common::FlightState FLIGHT_STATE) {
  sequence.received_av();
  if (FLIGHT_STATE == common::FlightState::LAUNCH) {
    sequence.current_state = Sequence::ONCE_AV_DETERMINING_LAUNCH;
  }
}

void input_read_loop(std::shared_ptr<LoraInterface> interface,
                     zmq::socket_t &pub_socket, Sequence &sequence) {
  set_thread_name("input_read_loop");
  std::vector<uint8_t> buffer(1024);
  auto last_read_time = std::chrono::steady_clock::now();
  auto last_timeout_warning_time = std::chrono::steady_clock::now();

  while (running) {
    ssize_t count = interface->read_data(buffer);
    if (count > 0) {
      last_read_time = std::chrono::steady_clock::now();
      // Check if we have enough bytes for the ID
      if (count >= 1) {
        int8_t packet_id = static_cast<int8_t>(buffer[0]);

        // Send packet ID to receiving ends so they know which proto file to use
        std::string packet_id_string(1, packet_id);
        zmq::message_t msg(packet_id_string.data(), sizeof(int8_t));
        pub_socket.send(msg, zmq::send_flags::none);

        // Note that some packet types are observed can be skipped if not meant
        // for GCS
        switch (packet_id) {
          case AV_TO_GCS_DATA_1::ID: {  // 3
            std::unique_ptr<AV_TO_GCS_DATA_1> proto_msg =
                process_packet<AV_TO_GCS_DATA_1>(count, buffer, pub_socket);
            if (proto_msg == nullptr) {
              // Yeah we got it, so you can just continue talking to other
              // devices. But we assume it was garbage and the information in it
              // is fucked
              sequence.received_av();
              break;
            }
            post_process_av(sequence, proto_msg->flight_state());
            if (proto_msg->broadcast_flag()) {
              sequence.current_state = Sequence::LOOP_AV_DATA_TRANSMISSION_BURN;
            }
            break;
          }
          case AV_TO_GCS_DATA_2::ID: {  // 4
            std::unique_ptr<AV_TO_GCS_DATA_2> proto_msg =
                process_packet<AV_TO_GCS_DATA_2>(count, buffer, pub_socket);
            if (proto_msg == nullptr) {
              sequence.received_av();
              break;
            }
            post_process_av(sequence, proto_msg->flight_state());
          } break;
          case AV_TO_GCS_DATA_3::ID: {  // 5
            std::unique_ptr<AV_TO_GCS_DATA_3> proto_msg =
                process_packet<AV_TO_GCS_DATA_3>(count, buffer, pub_socket);
            if (proto_msg == nullptr) {
              sequence.received_av();
              break;
            }
            post_process_av(sequence, proto_msg->flight_state());
            break;
          }
          // Electronically impossible to recieve own packet
          case GCS_TO_AV_STATE_CMD::ID: {  // 1
            // process_packet<GCS_TO_AV_STATE_CMD>(count, buffer, pub_socket);
            slogger::error("Somehow received GCS_TO_AV_STATE_CMD");
            break;
          }
          case GCS_TO_GSE_STATE_CMD::ID: {  // 2
            // process_packet<GCS_TO_GSE_STATE_CMD>(count, buffer,
            // pub_socket);
            slogger::error("Somehow received GCS_TO_GSE_STATE_CMD");
            break;
          }
          case GSE_TO_GCS_DATA_1::ID: {  // 6
            process_packet<GSE_TO_GCS_DATA_1>(count, buffer, pub_socket);
            sequence.received_gse();
            break;
          }
          case GSE_TO_GCS_DATA_2::ID: {  // 7
            process_packet<GSE_TO_GCS_DATA_2>(count, buffer, pub_socket);
            sequence.received_gse();
            break;
          }
          default: {
            std::string numeric_val =
                std::to_string(static_cast<int>(packet_id));
            slogger::error("Unknown packet ID: " + std::to_string(packet_id) +
                           " numeric: " + numeric_val);
            break;
          }
        }
      }
    } else {
      // CPU sleeper
      std::this_thread::sleep_for(std::chrono::milliseconds(1));
      // Timeout warning
      auto now = std::chrono::steady_clock::now();
      // Amount of seconds since last read total
      int seconds_waited =
          std::chrono::duration_cast<std::chrono::seconds>(now - last_read_time)
              .count();
      int seconds_waited_timeout =
          std::chrono::duration_cast<std::chrono::seconds>(
              now - last_timeout_warning_time)
              .count();
      if (seconds_waited >= 3 && seconds_waited_timeout >= 3) {
        slogger::warning("No data received for " +
                         std::to_string(seconds_waited) + " seconds.");
        last_timeout_warning_time = now;  // Wait another 3 seconds
      }
    }
  }
}

std::shared_ptr<LoraInterface> create_interface(
    const std::string INTERFACE_NAME, const std::string DEVICE_PATH) {
  std::shared_ptr<LoraInterface> interface;

  if (INTERFACE_NAME == "UART") {
    // This will sent AT setup commands as well in constructor
    interface = std::make_shared<UartInterface>(DEVICE_PATH);
  } else if (INTERFACE_NAME == "TEST") {
    interface = std::make_shared<TestInterface>(DEVICE_PATH);
  } else {
    throw std::runtime_error("Error: Invalid interface type");
  }

  return interface;
}

std::vector<uint8_t> collect_pull_data(const zmq::message_t &last_pendant_msg) {
  // Process command (echo bytes verbatim to LoRa)
  // slogger::critical("HELLO DATA IS STILL COMING THROUGH");
  std::vector<uint8_t> cmd_data(
      static_cast<const uint8_t *>(last_pendant_msg.data()),
      static_cast<const uint8_t *>(last_pendant_msg.data()) +
          last_pendant_msg.size());
  return cmd_data;
}

// Packet creator for GCS -> AV
std::vector<uint8_t> create_GCS_TO_AV_data(const bool BROADCAST) {
  // DEBUG
  // For debug only, just send garbage
  std::vector<uint8_t> data;
  data.push_back(0x01);        // ID
  data.push_back(0b10100000);  // From excel sheet here and below
  data.push_back(0b01011111);
  if (BROADCAST) {
    data.push_back(0b10101010);
  } else {
    data.push_back(0b00000000);
  }

  return data;
}

// ./file <interface type> <device path> <socket path> <optional mode>
// Optional modes (string):
// -  --GSE_ONLY
int main(int argc, char *argv[]) {
  GOOGLE_PROTOBUF_VERIFY_VERSION;

  slogger::info("Starting middleware server");

  // Pick interface based on the first argument
  if (argc < 4) {
    slogger::error("Not enough arugments provided.");
    slogger::error(
        "Usage: ./file <socket type> <device path> <socket path> <optional "
        "mode>");
    // Throw error silenced by main
    throw std::runtime_error("Error: Not enough arugments provided");
    return EXIT_FAILURE;
  } else if (argc > 5) {
    slogger::warning("Too many arugments provided: " + std::to_string(argc));
  }

  signal(SIGINT, signal_handler);
  signal(SIGTERM, signal_handler);

  try {
    // Create an interface
    const std::string DEVICE_PATH = std::string(argv[2]);
    const std::string SOCKET_PATH = std::string(argv[3]);
    // One per device object. If you're using 2 devices, best to have 2
    // interfaces
    std::shared_ptr<LoraInterface> interface =
        create_interface(std::string(argv[1]), DEVICE_PATH);

    interface->initialize();
    slogger::info("Interface initialised for type: " + std::string(argv[1]));

    // Create sequence handler singleton
    Sequence sequence;

    if (argc == 5) {
      std::string mode = std::string(argv[4]);
      sequence.set_gse_only_mode(mode == "--GSE_ONLY");
    }

    // ZeroMQ setup
    zmq::context_t context(1);

    // PUB socket for broadcasting incoming data
    zmq::socket_t pub_socket(context, ZMQ_PUB);
    pub_socket.bind("ipc:///tmp/" + SOCKET_PATH + "_pub.sock");

    // PULL socket for fowarding commands to LoRa
    zmq::socket_t pendant_pull_socket(context, ZMQ_PULL);
    constexpr int PENDANT_HWM = 1;  // Only keep 1 message in buffer
    pendant_pull_socket.set(zmq::sockopt::rcvhwm, PENDANT_HWM);
    pendant_pull_socket.set(zmq::sockopt::conflate,
                            1);  // Only keep last message
    pendant_pull_socket.bind("ipc:///tmp/" + SOCKET_PATH +
                             "_pendant_pull.sock");

    // Start interface reading thread
    std::thread reader(input_read_loop, interface, std::ref(pub_socket),
                       std::ref(sequence));

    // http://api.zeromq.org/3-0:zmq-poll
    // Can add multiple push pull sockets here. Useful for when front end is
    // integrated
    zmq::pollitem_t items[] = {{pendant_pull_socket, 0, ZMQ_POLLIN, 0}};
    std::vector<uint8_t> pendant_data;

    const std::vector<uint8_t> FALLBACK_PENDANT_DATA = {0x02, 0x00, 0xFF, 0x00};
    auto last_pendant_receival = std::chrono::steady_clock::now();
    auto last_timeout_warning_time = std::chrono::steady_clock::now();
    // TODO I think this is redundant now?
    const bool SUPPRESS_PENDANT_WARNING = std::getenv("CONFIG_PATH") == nullptr;
    // Main command loop
    slogger::info("Middleware server started successfully");
    while (running) {
      zmq::poll(items, 1, std::chrono::milliseconds(300));  // 300ms timeout

      int socket_more_intbool = 1;  // http://api.zeromq.org/2-2:zmq-getsockopt
      // items[0].revents represents items[0] which is the pendant data
      // In future with multiple polls, just copy this block with a different
      // items index
      if (items[0].revents & ZMQ_POLLIN) {
        do {  // Data to be dequeued
          last_pendant_receival = std::chrono::steady_clock::now();
          zmq::message_t pendant_msg;
          zmq::recv_result_t pendant_result =
              pendant_pull_socket.recv(pendant_msg, zmq::recv_flags::none);
          if (pendant_result) {
            pendant_data = collect_pull_data(pendant_msg);
            socket_more_intbool =
                pendant_pull_socket.get(zmq::sockopt::rcvmore);
          }
        } while (socket_more_intbool);
      } else {
        auto now = std::chrono::steady_clock::now();
        int seconds_waited = std::chrono::duration_cast<std::chrono::seconds>(
                                 now - last_pendant_receival)
                                 .count();
        int seconds_waited_timeout =
            std::chrono::duration_cast<std::chrono::seconds>(
                now - last_timeout_warning_time)
                .count();
        constexpr int PENDANT_FALLBACK_TIMEOUT_SECONDS = 5;
        if (seconds_waited >= PENDANT_FALLBACK_TIMEOUT_SECONDS &&
            seconds_waited_timeout >= 3) {
          if (!SUPPRESS_PENDANT_WARNING) {
            slogger::warning(
                "Failed to get any new pendant data from pendant service "
                "for " +
                std::to_string(seconds_waited) + " seconds");
          }
          pendant_data = FALLBACK_PENDANT_DATA;
          last_timeout_warning_time = now;  // Wait another 3 seconds
        }
      }

      if (pendant_data.empty()) {
        // No data to send, continue and try polling again
        // This will only be empty while the pendant software boots
        continue;
      }

      if (sequence.gse_only_mode()) {
        interface->write_data(pendant_data);
        sequence.start_await_gse();
        sequence.sit_and_wait_for_gse();
        continue;
      }

      // After getting data, continue with main logic loop
      switch (sequence.get_state()) {
        case Sequence::State::LOOP_PRE_LAUNCH:
          // Send data to GSE
          interface->write_data(pendant_data);
          sequence.start_await_gse();
          // Wait for data from GSE (blocking rest of this loop, or timeout)
          sequence.sit_and_wait_for_gse();  // Let read thread unlock this
          // Send data to AV
          interface->write_data(create_GCS_TO_AV_data(false));
          sequence.start_await_av();
          // Wait for data from AV (blocking rest of this loop, or timeout)
          sequence.sit_and_wait_for_av();
          break;
        case Sequence::State::LOOP_IGNITION:
          // This stage is identical to pre-launch for GCS
          break;
        // It says once, but it's a conditional loop anyway.
        case Sequence::State::ONCE_AV_DETERMINING_LAUNCH:
          interface->write_data(pendant_data);
          sequence.start_await_gse();
          sequence.sit_and_wait_for_gse();
          interface->write_data(create_GCS_TO_AV_data(true));
          sequence.start_await_av();
          sequence.sit_and_wait_for_av();
          break;
        case Sequence::State::LOOP_AV_DATA_TRANSMISSION_BURN:
          // Just listen. This thread can just close bassically
          break;
        case Sequence::State::LOOP_AV_DATA_TRANSMISSION_APOGEE:
          // Just listen. This thread can just close bassically
          break;
        case Sequence::State::LOOP_AV_DATA_TRANSMISSION_LANDED:
          // Just listen. This thread can just close bassically
          break;
      }
    }

    // Cleanup
    reader.join();
    pub_socket.close();
  } catch (const zmq::error_t &e) {
    slogger::error("ZeroMQ error: " + std::string(e.what()));
  } catch (const std::runtime_error &e) {
    slogger::error("Runtime error: " + std::string(e.what()));
  } catch (const std::exception &e) {
    slogger::error("Generic error on main: " + std::string(e.what()));
    return EXIT_FAILURE;
  }
  google::protobuf::ShutdownProtobufLibrary();
  return EXIT_SUCCESS;
}
