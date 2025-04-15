const TEST_INTERFACE_ITEMS = [
  "av-vel-h",
  "av-vel-v",
  "av-vel-total",
  "av-accel-x-lo",
  "av-accel-x-hi",
  "av-accel-y-lo",
  "av-accel-y-hi",
  "av-accel-z-lo",
  "av-accel-z-hi",
  "av-gyro-x",
  "av-gyro-y",
  "av-gyro-z"
];

function test_updateAllInterfaceValues() {
    TEST_INTERFACE_ITEMS.forEach((item, i) => {
        updateInterfaceValue(item, i);
    });
}
