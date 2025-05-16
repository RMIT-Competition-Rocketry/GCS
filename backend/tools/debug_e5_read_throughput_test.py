import serial
import time
import re


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
                         "AT+TEST=?",
                         "AT+TEST=RXLRPKT"]
    try:
        for command in at_setup_commands:
            # Send the AT command
            ser.write((command + '\r\n').encode())
            print(f"Sent: {command}")
            time.sleep(0.5)

            response = ser.read_all().decode('utf-8', errors='ignore')
            print(f">: {response}")

        print("Continuous read started")
        packet_num = 0
        prev_time = time.monotonic()
        start_time = time.monotonic()
        buffer = ""
        restring = r'\+TEST: LEN:\d+, RSSI:-?\d+, SNR:-?\d+\s\+TEST: RX\s?"[0-9A-F]+"\s'
        REGEX = re.compile(restring, re.DOTALL)
        while True:
            response = ser.read_all().decode('utf-8', errors='ignore')
            buffer += response
            if re.match(REGEX, buffer):
                packet_num += 1
                now = time.monotonic()

                delta_s = now - prev_time
                delta_ms = delta_s * 1000
                prev_time = now
                total_s = now - start_time

                pps = packet_num / total_s if total_s > 0 else 0

                print(f">: {buffer}")
                print(
                    f"\rPkt #{packet_num:<4d} | Δ={delta_ms:4.3f} ms | total PPS={pps:6.2f}",
                    end='', flush=True
                )
                buffer = ""

    except Exception as e:
        print(f"Error during communication: {e}")
    finally:
        # Close the serial port
        ser.close()
        print("Serial port closed.")


if __name__ == "__main__":
    send_at_commands()
