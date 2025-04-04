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
#include "AV_TO_GCS_DATA_2.hpp"
#include "AV_TO_GCS_DATA_3.hpp"
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

template <typename PacketType>
void process_packet(const ssize_t BUFFER_BYTE_COUNT,
                    std::vector<uint8_t> &buffer, zmq::socket_t &pub_socket) {
  // SIZE does not include ID byte that's already been read
  slogger::debug("Processing packet: " + std::string(PacketType::PACKET_NAME) +
                 " ID: " + std::to_string(PacketType::ID));
  if (BUFFER_BYTE_COUNT == PacketType::SIZE + 1) {
    try {
      // Construct the packet object (skipping the ID byte)
      PacketType payload(&buffer[1]);

      // Convert to protobuf and serialize to a string
      auto proto_msg = payload.toProtobuf();
      if (!proto_msg.IsInitialized()) {
        std::string missing_info = proto_msg.InitializationErrorString();
        slogger::warning(std::string(PacketType::PACKET_NAME) +
                         ": Not all fields are initialized in the protobuf "
                         "message. Missing: " +
                         missing_info);
      }
      std::string serialized;
      if (proto_msg.SerializeToString(&serialized)) {
        // Has to be At LEAST bigger than the input size with proto
        // slogger::debug("NAME: " + std::string(PacketType::PACKET_NAME));
        // slogger::debug("ID  : " + std::to_string(PacketType::ID));
        zmq::message_t msg(serialized.data(), serialized.size());
        pub_socket.send(msg, zmq::send_flags::none);
      } else {
        slogger::error(std::string(PacketType::PACKET_NAME) +
                       ": Failed to serialize to string for protobuf");
      }
    } catch (const std::exception &e) {
      slogger::error(std::string(PacketType::PACKET_NAME) +
                     ": Error processing payload: " + e.what());
    }
  } else {
    slogger::error(std::string(PacketType::PACKET_NAME) +
                   ": Incorrect packet size. Expected: " +
                   std::to_string(PacketType::SIZE + 1) + " bytes, got: " +
                   std::to_string(BUFFER_BYTE_COUNT) + " bytes");
    return;  // TODO: Test what the leftover data will do after this
  }
}

void input_read_loop(std::shared_ptr<LoraInterface> interface,
                     zmq::socket_t &pub_socket, Sequence &sequence) {
  set_thread_name("input_read_loop");
  std::vector<uint8_t> buffer(256);
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
          case AV_TO_GCS_DATA_1::ID:  // 3
            process_packet<AV_TO_GCS_DATA_1>(count, buffer, pub_socket);
            break;
          case AV_TO_GCS_DATA_2::ID:  // 4
            process_packet<AV_TO_GCS_DATA_2>(count, buffer, pub_socket);
            break;
          case AV_TO_GCS_DATA_3::ID:  // 5
            process_packet<AV_TO_GCS_DATA_3>(count, buffer, pub_socket);
            break;
          // TODO GCS should never recieve its own packets.
          // Electronically impossible
          case GCS_TO_AV_STATE_CMD::ID:  // 1
            process_packet<GCS_TO_AV_STATE_CMD>(count, buffer, pub_socket);
            break;
          case GCS_TO_GSE_STATE_CMD::ID:  // 2
            process_packet<GCS_TO_GSE_STATE_CMD>(count, buffer, pub_socket);
            break;
          case GSE_TO_GCS_DATA_1::ID:  // 6
            process_packet<GSE_TO_GCS_DATA_1>(count, buffer, pub_socket);
            sequence.received_gse();
            break;
          case GSE_TO_GCS_DATA_2::ID:  // 7
            process_packet<GSE_TO_GCS_DATA_2>(count, buffer, pub_socket);
            sequence.received_gse();
            break;
          default:
            std::string numeric_val =
                std::to_string(static_cast<int>(packet_id));
            slogger::error("Unknown packet ID: " + std::to_string(packet_id) +
                           "numeric: " + numeric_val);
            break;
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

// ./file <interface type> <device path> <socket path>
int main(int argc, char *argv[]) {
  GOOGLE_PROTOBUF_VERIFY_VERSION;

  // Pick interface based on the first argument
  if (argc < 4) {
    slogger::error("Not enough arugments provided.");
    slogger::error("Usage: ./file <socket type> <device path> <socket path>");
    // Throw error silenced by main
    throw std::runtime_error("Error: Not enough arugments provided");
    return EXIT_FAILURE;
  } else if (argc > 4) {
    slogger::warning("Too many arugments provided");
  }

  signal(SIGINT, signal_handler);
  signal(SIGTERM, signal_handler);

  try {
    // Create an interface
    const std::string DEVICE_PATH = std::string(argv[2]);
    const std::string SOCKET_PATH = std::string(argv[3]);
    std::shared_ptr<LoraInterface> interface =
        create_interface(std::string(argv[1]), DEVICE_PATH);

    interface->initialize();
    slogger::info("Interface initialised for type: " + std::string(argv[1]));

    // Create sequence handler singleton
    Sequence sequence;

    // ZeroMQ setup
    zmq::context_t context(1);

    // PUB socket for broadcasting incoming data
    zmq::socket_t pub_socket(context, ZMQ_PUB);
    pub_socket.bind("ipc:///tmp/" + SOCKET_PATH + "_pub.sock");

    // PULL socket for fowarding commands to LoRa
    zmq::socket_t pendant_pull_socket(context, ZMQ_PULL);
    pendant_pull_socket.bind("ipc:///tmp/" + SOCKET_PATH +
                             "_pendant_pull.sock");

    // Start interface reading thread
    std::thread reader(input_read_loop, interface, std::ref(pub_socket),
                       std::ref(sequence));

    // http://api.zeromq.org/3-0:zmq-poll
    // Can add multiple push pull sockets here. Useful for when front end is
    // integrated
    zmq::pollitem_t items[] = {{pendant_pull_socket, 0, ZMQ_POLLIN, 0}};
    zmq::message_t last_pendant_msg;

    // Main command loop
    while (running) {
      zmq::poll(items, 1, std::chrono::milliseconds(300));  // 300ms timeout

      // items[0].revents represents items[0] which is the pendant data
      // In future with multiple polls, just copy this block with a different
      // items index
      if (items[0].revents & ZMQ_POLLIN) {
        // Data to be dequeued
        zmq::recv_result_t result =
            pendant_pull_socket.recv(last_pendant_msg, zmq::recv_flags::none);
        if (result) {
          std::vector<uint8_t> cmd_data = collect_pull_data(last_pendant_msg);
          if (!sequence.waiting_for_gse()) {
            // TODO Should I just internalise writing data inside
            // sequence so the locking part is not required to be
            // written manually each time?
            // ctrl+f "race condition" annotation on master design
            interface->write_data(cmd_data);
            sequence.await_gse();
          }
        }
      }
      // Check if it's our turn to send data to GSE
    }

    // Cleanup
    reader.join();
  } catch (const std::exception &e) {
    slogger::error("Generic error on main: " + std::string(e.what()));
    return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;
}