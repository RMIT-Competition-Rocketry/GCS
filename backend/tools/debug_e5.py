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
                         "AT+TEST=RFCFG,915,SF9,500,12,16,14,OFF,OFF,OFF",
                         "AT+TEST=RXLRPKT"]

    try:
        for command in at_setup_commands:
            # Send the AT command
            ser.write((command + '\r\n').encode())
            print(f"Sent: {command}")
            time.sleep(1)

            response = ser.read_all().decode('utf-8', errors='ignore')
            print(f">: {response}")

        print("Continuous read started")
        while True:
            response = ser.read_all().decode('utf-8', errors='ignore')
            if response:
                print(f">: {response}")

    except Exception as e:
        print(f"Error during communication: {e}")
    finally:
        # Close the serial port
        ser.close()
        print("Serial port closed.")


if __name__ == "__main__":
    send_at_commands()
