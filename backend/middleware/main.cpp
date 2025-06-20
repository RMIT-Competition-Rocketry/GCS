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
#include "GSE_TO_GCS_DATA_1.hpp"
#include "GSE_TO_GCS_DATA_2.hpp"
#include "debug_functions.hpp"
#include "sequence.hpp"
#include "subprocess_logging.hpp"
#include "test_interface.hpp"
#include "test_uart_interface.hpp"
#include "uart_interface.hpp"

// This file hosts the ZeroMQ IPC server stuff

std::atomic<bool> running{true};
volatile bool debugger_attached = false;

// Thread safe signal handler
void signal_handler(int) { running = false; }

inline void set_thread_name([[maybe_unused]] const char *name) {
#ifdef __APPLE__
  pthread_setname_np(name);
#endif
}

template <typename PacketType>
std::unique_ptr<PacketType> process_packet(const ssize_t BUFFER_BYTE_COUNT,
                                           std::vector<uint8_t> &buffer,
                                           zmq::socket_t &pub_socket,
                                           const auto READER_BOOT_TIME,
                                           Sequence &sequence) {
  // SIZE does not include ID byte that's already been read
  if (BUFFER_BYTE_COUNT >= PacketType::SIZE + 1) {
    try {
      // Construct the packet object (skipping the ID byte)
      std::unique_ptr<PacketType> payload =
          std::make_unique<PacketType>(&buffer[1]);

      // Convert to protobuf and serialize to a string
      float TIMESTAMP = std::chrono::duration<float>(
                            std::chrono::steady_clock::now() - READER_BOOT_TIME)
                            .count();
      auto proto_msg =
          payload->toProtobuf(TIMESTAMP, sequence.get_packet_count_av(),
                              sequence.get_packet_count_gse());
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
                   debug::vectorToHexString(buffer, BUFFER_BYTE_COUNT));
  }
  return nullptr;
}

void post_process_av(Sequence &sequence,
                     const common::FlightState FLIGHT_STATE) {
  sequence.received_av();
  if (FLIGHT_STATE == common::FlightState::LAUNCH) {
    sequence.current_state = Sequence::ONCE_AV_DETERMINING_LAUNCH;
  }
  switch (FLIGHT_STATE) {
    case common::FlightState::OH_NO:
    case common::FlightState::PRE_FLIGHT_NO_FLIGHT_READY:
    case common::FlightState::PRE_FLIGHT_FLIGHT_READY:
      break;
    case common::FlightState::LAUNCH:
    case common::FlightState::COAST:
    case common::FlightState::APOGEE:
    case common::FlightState::DESCENT:
    case common::FlightState::LANDED:
      sequence.set_start_sending_broadcast_flag(true);
    default:
      break;
  }
}

void input_read_loop(std::shared_ptr<LoraInterface> interface,
                     zmq::socket_t &pub_socket, Sequence &sequence) {
  set_thread_name("input_read_loop");
  std::vector<uint8_t> buffer(1024);
  auto READER_BOOT_TIME = std::chrono::steady_clock::now();
  auto last_read_time = READER_BOOT_TIME;
  auto last_timeout_warning_time = READER_BOOT_TIME;

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
            sequence.increment_packet_count_av();
            std::unique_ptr<AV_TO_GCS_DATA_1> proto_msg =
                process_packet<AV_TO_GCS_DATA_1>(count, buffer, pub_socket,
                                                 READER_BOOT_TIME, sequence);
            if (proto_msg == nullptr) {
              // Yeah we got it, so you can just continue talking to other
              // devices. But we assume it was garbage and the information in it
              // is fucked
              sequence.received_av();
              break;
            }
            post_process_av(sequence, proto_msg->flight_state());
            if (proto_msg->broadcast_flag()) {
              sequence.set_broadcast_flag_recieved(true);
              sequence.current_state = Sequence::LOOP_AV_DATA_TRANSMISSION_BURN;
            }
            break;
          }
          case AV_TO_GCS_DATA_2::ID: {  // 4
            sequence.increment_packet_count_av();
            std::unique_ptr<AV_TO_GCS_DATA_2> proto_msg =
                process_packet<AV_TO_GCS_DATA_2>(count, buffer, pub_socket,
                                                 READER_BOOT_TIME, sequence);
            if (proto_msg == nullptr) {
              sequence.received_av();
              break;
            }
            post_process_av(sequence, proto_msg->flight_state());
          } break;
          case AV_TO_GCS_DATA_3::ID: {  // 5
            sequence.increment_packet_count_av();
            std::unique_ptr<AV_TO_GCS_DATA_3> proto_msg =
                process_packet<AV_TO_GCS_DATA_3>(count, buffer, pub_socket,
                                                 READER_BOOT_TIME, sequence);
            if (proto_msg == nullptr) {
              sequence.received_av();
              break;
            }
            post_process_av(sequence, proto_msg->flight_state());
            break;
          }
          case GSE_TO_GCS_DATA_1::ID: {  // 6
            sequence.increment_packet_count_gse();
            process_packet<GSE_TO_GCS_DATA_1>(count, buffer, pub_socket,
                                              READER_BOOT_TIME, sequence);
            sequence.received_gse();
            break;
          }
          case GSE_TO_GCS_DATA_2::ID: {  // 7
            sequence.increment_packet_count_gse();
            process_packet<GSE_TO_GCS_DATA_2>(count, buffer, pub_socket,
                                              READER_BOOT_TIME, sequence);
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
  } else if (INTERFACE_NAME == "TEST_UART") {
    interface = std::make_shared<TestUartInterface>(DEVICE_PATH);
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

std::vector<uint8_t> create_GCS_TO_AV_data(const bool BROADCAST,
                                           Sequence &sequence) {
  std::vector<uint8_t> data;

  const bool camera_power = sequence.get_camera_power();

  // Byte 0: Packet ID
  data.push_back(0x01);  // ID

  // Byte 1: camera_power command
  // [7:5] type = 0b101
  // [4]   value = camera_power
  // [3:0] padding/reserved = 0
  uint8_t byte1 = (0b101 << 5) | (camera_power << 4);
  data.push_back(byte1);

  // Byte 2: camera_power disable command
  // [7:5] type = 0b010
  // [4]   value = !camera_power
  // [3:0] padding/reserved = 0b1111
  uint8_t byte2 = (0b010 << 5) | ((!camera_power) << 4) | 0b1111;
  data.push_back(byte2);

  // Byte 3: broadcast flag
  // Set broadcast indicator
  data.push_back(BROADCAST ? 0b10101010 : 0b00000000);

  return data;
}

int main(int argc, char *argv[]) {
  GOOGLE_PROTOBUF_VERIFY_VERSION;

  slogger::info("Starting middleware server");

  // Pick interface based on the first argument
  if (argc < 5) {
    slogger::error("Not enough arugments provided.");
    // Optional modes (string):
    // -  --GSE_ONLY
    slogger::error(
        "Usage: ./file <interface type> <device path> <pendent socket path> "
        "<web control socket path> <optional mode>");
    // Throw error silenced by main
    throw std::runtime_error("Error: Not enough arugments provided");
    return EXIT_FAILURE;
  } else if (argc > 6) {
    slogger::warning("Too many arugments provided: " + std::to_string(argc));
  }

  signal(SIGINT, signal_handler);
  signal(SIGTERM, signal_handler);

  // Create an interface
  const std::string DEVICE_PATH = std::string(argv[2]);
  const std::string PENDANT_SOCKET_PATH = std::string(argv[3]);
  const std::string WEB_CONTROL_SOCKET_PATH = std::string(argv[4]);
  // One per device object. If you're using 2 devices, best to have 2
  // interfaces
  std::shared_ptr<LoraInterface> interface =
      create_interface(std::string(argv[1]), DEVICE_PATH);

  interface->initialize();
  slogger::info("Interface initialised for type: " + std::string(argv[1]));

  // Create sequence handler singleton
  Sequence sequence;

  if (argc == 6) {
    std::string mode = std::string(argv[5]);
    sequence.set_gse_only_mode(mode == "--GSE_ONLY");
  }

  zmq::context_t context(1);

  // PUB socket for broadcasting incoming data
  zmq::socket_t pub_socket(context, ZMQ_PUB);
  pub_socket.bind("ipc:///tmp/" + PENDANT_SOCKET_PATH + "_pub.sock");

  // PULL socket for fowarding commands to LoRa
  zmq::socket_t pendant_pull_socket(context, ZMQ_PULL);
  constexpr int PENDANT_HWM = 1;  // Only keep 1 message in buffer
  pendant_pull_socket.set(zmq::sockopt::rcvhwm, PENDANT_HWM);
  // Only keep last message
  pendant_pull_socket.set(zmq::sockopt::conflate, 1);
  pendant_pull_socket.bind("ipc:///tmp/" + PENDANT_SOCKET_PATH +
                           "_pendant_pull.sock");

  zmq::socket_t web_control_pull_socket(context, ZMQ_PULL);
  constexpr int WEB_CONTROL_HWM = 1;  // Only keep 1 message in buffer
  web_control_pull_socket.set(zmq::sockopt::rcvhwm, WEB_CONTROL_HWM);
  // Only keep last message
  web_control_pull_socket.set(zmq::sockopt::conflate, 1);
  web_control_pull_socket.bind("ipc://" + WEB_CONTROL_SOCKET_PATH);

  // Start interface reading thread
  std::thread reader(input_read_loop, interface, std::ref(pub_socket),
                     std::ref(sequence));

  // http://api.zeromq.org/3-0:zmq-poll
  // Can add multiple push pull sockets here. Useful for when front end is
  // integrated
  std::vector<zmq::pollitem_t> items = {
      {static_cast<void *>(pendant_pull_socket), 0, ZMQ_POLLIN, 0},
      {static_cast<void *>(web_control_pull_socket), 0, ZMQ_POLLIN, 0}};
  std::vector<uint8_t> pendant_data;
  std::vector<uint8_t> web_control_data;

  const std::vector<uint8_t> FALLBACK_PENDANT_DATA = {0x02, 0x00, 0xFF, 0x00};
  auto last_pendant_receival = std::chrono::steady_clock::now();
  auto last_timeout_warning_time = std::chrono::steady_clock::now();
  // TODO I think this is redundant now?
  const bool SUPPRESS_PENDANT_WARNING = std::getenv("CONFIG_PATH") == nullptr;
  // Main command loop
  slogger::info("Middleware server started successfully");
  try {
    while (running) {
      zmq::poll(items, std::chrono::milliseconds(300));  // 300ms timeout

      int pendant_socket_more_intbool =
          1;  // http://api.zeromq.org/2-2:zmq-getsockopt
      // items[0].revents represents items[0] which is the pendant data
      if (items[0].revents & ZMQ_POLLIN) {
        do {  // Data to be dequeued
          last_pendant_receival = std::chrono::steady_clock::now();
          zmq::message_t pendant_msg;
          zmq::recv_result_t pendant_result =
              pendant_pull_socket.recv(pendant_msg, zmq::recv_flags::none);
          if (pendant_result) {
            pendant_data = collect_pull_data(pendant_msg);
            pendant_socket_more_intbool =
                pendant_pull_socket.get(zmq::sockopt::rcvmore);
          }
        } while (pendant_socket_more_intbool);
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
        // Fallback data should be present anyway
        continue;
      }

      // http://api.zeromq.org/2-2:zmq-getsockopt
      int web_control_socket_more_intbool = 1;
      if (items[1].revents & ZMQ_POLLIN) {
        do {  // Data to be dequeued
          zmq::message_t web_control_msg;
          zmq::recv_result_t web_control_result = web_control_pull_socket.recv(
              web_control_msg, zmq::recv_flags::none);
          if (web_control_result) {
            web_control_data = collect_pull_data(web_control_msg);
            web_control_socket_more_intbool =
                web_control_pull_socket.get(zmq::sockopt::rcvmore);
          }
        } while (web_control_socket_more_intbool);
        // Get rid of this shit when you refactor all IPC comms
        if (!web_control_data.empty()) {
          slogger::debug("server got values from web control: " +
                         debug::vectorToHexString(web_control_data,
                                                  web_control_data.size()));
          uint8_t packet_byte_prefix = web_control_data.front();
          web_control_data.erase(
              web_control_data.begin());  // remove that first byte
          // fucking stupid check because grpc didn't get done in time
          // fuck
          if (packet_byte_prefix == 123) {
            // Yeah you're trying to activate power
            if (sequence.get_camera_power() != true) {
              slogger::warning("Camera power ON");
            }
            sequence.set_camera_power(true);
          } else if (packet_byte_prefix == 100) {
            if (sequence.get_camera_power() != false) {
              slogger::warning("Camera power OFF");
            }
            sequence.set_camera_power(false);
          } else {
            bool manual_control = packet_byte_prefix == 0xFF;
            if (manual_control != sequence.manual_control_mode()) {
              // manual control state value has changed
              if (manual_control) {
                slogger::warning("Manual control ENABLED");
              } else {
                slogger::warning("Manual control DISABLED");
              }
            }
            sequence.set_manual_control_mode(manual_control);
          }
        }
      }

      // Are we sending manual packets or pendant controlled packets?
      // You have to pick something to continue the networking sequence and not
      // timeout the GSE
      std::vector<uint8_t> gse_data;
      if (sequence.manual_control_mode()) {
        gse_data = web_control_data;  // Last updated value
      } else {
        gse_data = pendant_data;
      }

      if (sequence.gse_only_mode()) {
        interface->write_data(gse_data);
        sequence.start_await_gse();
        sequence.sit_and_wait_for_gse();
        continue;
      }

      bool broadcast = sequence.start_sending_broadcast_flag() &&
                       !sequence.have_received_broadcast_flag();

      // After getting data, continue with main logic loop
      switch (sequence.get_state()) {
        case Sequence::State::LOOP_PRE_LAUNCH:
          // Send data to GSE
          interface->write_data(gse_data);
          sequence.start_await_gse();
          // Wait for data from GSE (blocking rest of this loop, or timeout)
          sequence.sit_and_wait_for_gse();  // Let read thread unlock this
          // Send data to AV
          interface->write_data(create_GCS_TO_AV_data(broadcast, sequence));
          sequence.start_await_av();
          // Wait for data from AV (blocking rest of this loop, or timeout)
          sequence.sit_and_wait_for_av();
          break;
        case Sequence::State::LOOP_IGNITION:
          // This stage is identical to pre-launch for GCS
          if (broadcast) {
            interface->write_data(create_GCS_TO_AV_data(broadcast, sequence));
          }
          break;
        // It says once, but it's a conditional loop anyway.
        case Sequence::State::ONCE_AV_DETERMINING_LAUNCH:
          interface->write_data(gse_data);
          sequence.start_await_gse();
          sequence.sit_and_wait_for_gse();
          interface->write_data(create_GCS_TO_AV_data(broadcast, sequence));
          sequence.start_await_av();
          sequence.sit_and_wait_for_av();
          break;
        case Sequence::State::LOOP_AV_DATA_TRANSMISSION_BURN:
          // Just listen. This thread can just close bassically
          if (broadcast) {
            interface->write_data(create_GCS_TO_AV_data(broadcast, sequence));
          }
          break;
        case Sequence::State::LOOP_AV_DATA_TRANSMISSION_APOGEE:
          // Just listen. This thread can just close bassically
          if (broadcast) {
            interface->write_data(create_GCS_TO_AV_data(broadcast, sequence));
          }
          break;
        case Sequence::State::LOOP_AV_DATA_TRANSMISSION_LANDED:
          // Just listen. This thread can just close bassically
          if (broadcast) {
            interface->write_data(create_GCS_TO_AV_data(broadcast, sequence));
          }
          break;
      }
    }
    slogger::info("Middleware shutdown starting");
  } catch (const zmq::error_t &e) {
    // EINTR (signal interrupt) is expected on shutdown
    if (e.num() != EINTR) {
      slogger::error("ZeroMQ.1 error (" + std::to_string(e.num()) +
                     "): " + std::string(e.what()));
      throw;
    }
  } catch (const std::runtime_error &e) {
    slogger::error("Runtime error: " + std::string(e.what()));
    throw;
  } catch (const std::exception &e) {
    slogger::error("Generic error on main: " + std::string(e.what()));
    throw;
  }
  try {
    // Cleanup
    reader.join();
    pub_socket.close();
    pendant_pull_socket.close();
    web_control_pull_socket.close();
    context.close();
    google::protobuf::ShutdownProtobufLibrary();
  } catch (const std::exception &e) {
    slogger::error("Error during cleanup");
    slogger::error(std::string(e.what()));
  }
  slogger::info("Middleware shutdown complete");
  return EXIT_SUCCESS;
}
