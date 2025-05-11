import serial
import time


def send_at_commands():
    try:
        ser = serial.Serial('/dev/ttyAMA0', baudrate=230400, timeout=1)
        if ser.is_open:
            print("Serial port opened successfully.")
    except Exception as e:
        print(f"Failed to open serial port: {e}")
        return

    at_setup_commands = ["AT",
                         "AT+MODE=TEST",
                         "AT+TEST=RFCFG,915,SF9,500,12,16,22,OFF,OFF,OFF",
                         "AT+TEST=?"]

    try:
        for command in at_setup_commands:
            # Send the AT command
            ser.write((command + '\r\n').encode())
            print(f"Sent: {command}")
            time.sleep(0.5)

            response = ser.read_all().decode('utf-8', errors='ignore')
            for line in response.splitlines():
                print(f"> {line}")

        PAYLOAD = "01"*32
        TX_COMMAND = f"AT+TEST=TXLRPKT, \"{PAYLOAD}\""
        print(f"TX_COMMAND: {TX_COMMAND}")
        print("Continuous write starting")
        packet_num = 0
        execution_wait_time_ms = time.monotonic()
        prev_time = time.monotonic()
        while True:
            ser.write((TX_COMMAND + '\r\n').encode())
            response = ""
            while "+TEST: TX DONE" not in response:
                response += ser.read_all().decode('utf-8', errors='ignore')

            packet_num += 1
            now = time.monotonic()

            delta_ms = (now - prev_time) * 1000
            prev_time = now

            print(f"\rSent packet {packet_num:<4d} | diff = {delta_ms:7.2f} ms",
                  end='', flush=True)
    except Exception as e:
        print(f"Error during communication: {e}")
    finally:
        # Close the serial port
        ser.close()
        print("Serial port closed.")


if __name__ == "__main__":
    send_at_commands()
