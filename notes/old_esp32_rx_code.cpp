#include <ArduinoJson.h>
// #include <ESP32Servo.h>

static int led = 2;
static char recv_buf[512];

static int at_send_check_response(char *p_ack, int timeout_ms, char *p_cmd) {
  if (p_ack == NULL) {
    return 0;
  }

  memset(recv_buf, 0, sizeof(recv_buf));  // Clear return buffer
  Serial1.print(p_cmd);                   // Send command to E5
  Serial.print(p_cmd);  // Log command being executed in console

  int index = 0;
  int startMillis = millis();

  // Read response from E5 into receive buffer
  while (millis() - startMillis < timeout_ms) {
    while (Serial1.available() && index < 512) {
      int ch = Serial1.read();
      recv_buf[index++] = ch;
    }
  }

  // Return 1 if command acknowledged
  if (strstr(recv_buf, p_ack) != NULL) {
    Serial.println(recv_buf);
    return 1;
  }

  // Otherwise, return 0
  return 0;
}

static void recv_prase(char *p_msg) {
  if (p_msg == NULL) {
    return;
  }
  char *p_start = NULL;
  char data[128];  // To hold the received bytes as characters

  int bytes_len = 0;
  p_start = strstr(p_msg, "RX");

  if (p_start && (1 == sscanf(p_start, "RX \"%s\"", &data))) {
    for (int i = 0; i < sizeof(data); i++) {
      if (int(data[i + 1]) == 0) {
        bytes_len = i;
        break;
      }
    }

    // Convert the characters to a byteArray
    int message_len = bytes_len / 2 + 1;
    byte out[message_len];

    auto getNum = [](char c) { return c > '9' ? c - 'A' + 10 : c - '0'; };

    for (int x = 0, y = 0; x < bytes_len; ++x, ++y)
      out[y] = (getNum(data[x++]) << 4) + getNum(data[x]);

    out[message_len] = '\0';

    uint8_t ID = out[0];

    // AV Packet 1
    if (ID == 0x4) {
      // flightstate
      float flightstate = out[1] & 0b00000111;
      ;
      // PL Connection
      float pl_connection_status = (out[1] & 0b00001000) >> 3;
      // AB Connection
      float ab_connection_status = (out[1] & 0b00010000) >> 4;
      // Future Development
      float future_dev_connection_1 = (out[1] & 0b00100000) >> 5;
      // Future Development
      float future_dev_connection_2 = (out[1] & 0b01000000) >> 6;
      // Future Development
      float future_dev_connection_3 = (out[1] & 0b10000000) >> 7;

      float low_accel_x =
          (int16_t)(((uint16_t)out[2] << 8) | (uint16_t)out[3]) / 2048.0f;
      float low_accel_y =
          (int16_t)(((uint16_t)out[4] << 8) | (uint16_t)out[5]) / 2048.0f;
      float low_accel_z =
          (int16_t)(((uint16_t)out[6] << 8) | (uint16_t)out[7]) / -2048.0f;
      float high_accel_x =
          (int16_t)(((uint16_t)out[8] << 8) | (uint16_t)out[9]) / -1024.0f;
      float high_accel_y =
          (int16_t)(((uint16_t)out[10] << 8) | (uint16_t)out[11]) / -1024.0f;
      float high_accel_z =
          (int16_t)(((uint16_t)out[12] << 8) | (uint16_t)out[13]) / 1024.0f;

      float gyro_x =
          (int16_t)(((uint16_t)out[14] << 8) | (uint16_t)out[15]) * 0.00875f;
      float gyro_y =
          (int16_t)(((uint16_t)out[16] << 8) | (uint16_t)out[17]) * 0.00875f;
      float gyro_z =
          (int16_t)(((uint16_t)out[18] << 8) | (uint16_t)out[19]) * 0.00875f;

      float altitude;
      memcpy(&altitude, &out[20], sizeof(float));

      float velocity;
      memcpy(&velocity, &out[24], sizeof(float));

      // Print Out Data
      Serial.print("Flight State: ");
      Serial.println(flightstate);

      Serial.print("Payload Connection State: ");
      Serial.println(pl_connection_status);

      Serial.print("AB Connection State: ");
      Serial.println(ab_connection_status);

      Serial.print("Low Accel X: ");
      Serial.println(low_accel_x, 3);

      Serial.print("Low Accel Y: ");
      Serial.println(low_accel_y, 3);

      Serial.print("Low Accel Z: ");
      Serial.println(low_accel_z, 3);

      Serial.print("High Accel X: ");
      Serial.println(high_accel_x, 3);

      Serial.print("High Accel Y: ");
      Serial.println(high_accel_y, 3);

      Serial.print("High Accel Z: ");
      Serial.println(high_accel_z, 3);

      Serial.print("Gyro X: ");
      Serial.println(gyro_x, 3);

      Serial.print("Gyro Y: ");
      Serial.println(gyro_y, 3);

      Serial.print("Gyro Z: ");
      Serial.println(gyro_z, 3);

      Serial.print("Altitude: ");
      Serial.println(altitude, 3);
      Serial.print("Velocity: ");
      Serial.println(velocity, 3);
    }

    // AV GPS Packet
    else if (ID == 0x5) {
      float gps_fix = (out[31] && 0x01);
      float flightstate = (out[31] >> 4);

      Serial.print("Flight State: ");
      Serial.println(flightstate, 3);

      Serial.print("GPS Fix: ");
      Serial.println(gps_fix);

      // Get data from LoRa Packet
      Serial.print("Latitude: ");
      for (int i = 1; i < 16; i++) {
        Serial.print(out[i]);
      }
      Serial.println("");

      Serial.print("Longitude: ");
      for (int i = 16; i < 31; i++) {
        Serial.print(out[i]);
      }
    }

    // Payload
    else if (ID == 0x6) {
      // Payload State
      float pl_state = (out[1] & 0b11100000) >> 5;
      // Payload Status
      // SPI Flash 0
      float pl_status_1 = (out[1] & 0b00000001);
      // SPI Flash 1
      float pl_status_2 = (out[1] & 0b00000010) >> 1;
      // Accel.
      float pl_status_3 = (out[1] & 0b00000100) >> 2;
      // BME280 0
      float pl_status_4 = (out[1] & 0b00001000) >> 3;
      // BME280 1
      float pl_status_5 = (out[1] & 0b00010000) >> 4;

      uint16_t pl_accel_x_raw =
          (int16_t)(((uint16_t)out[3] << 8) | (uint16_t)out[2]);
      float pl_accel_x = pl_accel_x_raw & 0x1FFF;  // Mask first 3 bits

      uint16_t pl_accel_y_raw =
          (int16_t)(((uint16_t)out[5] << 8) | (uint16_t)out[4]);
      float pl_accel_y = pl_accel_y_raw & 0x1FFF;  // Mask first 3 bits

      uint16_t pl_accel_z_raw =
          (int16_t)(((uint16_t)out[7] << 8) | (uint16_t)out[6]);
      float pl_accel_z = pl_accel_z_raw & 0x1FFF;  // Mask first 3 bits

      float pl_0_temp = (int16_t)(((uint16_t)out[8] << 8) | (uint16_t)out[9]);
      float pl_0_humidity =
          (int16_t)(((uint16_t)out[10] << 8) | (uint16_t)out[11]);
      float pl_0_pressure =
          (int16_t)(((uint16_t)out[12] << 8) | (uint16_t)out[13]);

      float pl_1_temp = (int16_t)(((uint16_t)out[14] << 8) | (uint16_t)out[15]);
      float pl_1_humidity =
          (int16_t)(((uint16_t)out[16] << 8) | (uint16_t)out[17]);
      float pl_1_pressure =
          (int16_t)(((uint16_t)out[18] << 8) | (uint16_t)out[19]);

      // Print Out Data
      Serial.print("PL Flight Status: ");
      Serial.println(pl_state, 3);

      Serial.print("PL Flash 0 Status: ");
      Serial.println(pl_status_1, 3);

      Serial.print("PL Flash 1 Status: ");
      Serial.println(pl_status_2, 3);

      Serial.print("PL Accel Status: ");
      Serial.println(pl_status_3, 3);

      Serial.print("PL BME280 0 Status: ");
      Serial.println(pl_status_4, 3);

      Serial.print("PL BME280 1 Status: ");
      Serial.println(pl_status_5, 3);

      Serial.print("PL accel x: ");
      Serial.println(pl_accel_x);

      Serial.print("PL accel y: ");
      Serial.println(pl_accel_y);

      Serial.print("PL accel z: ");
      Serial.println(pl_accel_z);

      Serial.print("PL temp: ");
      Serial.println(pl_0_temp, 3);

      Serial.print("PL humidity: ");
      Serial.println(pl_0_humidity, 3);

      Serial.print("PL pressure: ");
      Serial.println(pl_0_pressure, 3);
    }
  }
}

void setup(void) {
  Serial.begin(115200);
  pinMode(led, OUTPUT);
  digitalWrite(led, LOW);

  Serial1.begin(230400, SERIAL_8N1, 16, 17);
  // 230400
  Serial.print("Serial1 LOCAL TEST\r\n");
  Serial.println("Connecting to LoRa E5...");

  while (!at_send_check_response("+AT: OK", 100, "AT\r\n"))
    Serial.println("No E5 module found.\n");

  // Initialise and Configure the E5
  if (at_send_check_response("+AT: OK", 100, "AT\r\n")) {
    at_send_check_response("+MODE: TEST", 1000, "AT+MODE=TEST\r\n");
    at_send_check_response(
        "+TEST: RFCFG", 1000,
        "AT+TEST=RFCFG,915,SF9,500,12,16,14,OFF,OFF,OFF\r\n");

    // Set E5 baud rate and update arduino serial
    // Uncomment this section and reset the E5 (power cycle or reset command) to
    // take effect at_send_check_response("+UART=BR, 230400", 1000, "AT+UART=BR,
    // 230400\r\n"); at_send_check_response("+RESET: OK, 9600", 1000,
    // "AT+RESET\r\n"); delay(2000);

    // Clear out the serial buffer and restart with new baud rate
    // Serial1.flush();
    // Serial1.begin(230400, SERIAL_8N1, 16, 17);
    // while(Serial1.available()) Serial.read();
    // delay(500);
  }

  at_send_check_response("+TEST: RXLRPKT", 1000, "AT+TEST=RXLRPKT\r\n");
  delay(200);

  digitalWrite(led, HIGH);
  Serial.println("End of Setup...");
}

void loop(void) {
  char cmd[128];
  // Transmit HEX Value
  sprintf(cmd, "");
  int ret = at_send_check_response("+TEST: RX", 100, "");
  if (ret) {
    recv_prase(recv_buf);
  } else {
    Serial.println("Receive failed!");
  }
}