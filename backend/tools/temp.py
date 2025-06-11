from gpiozero import Button
from time import sleep

# List your GPIO pins here:
GPIO_PINS = [4, 17, 27, 22, 10, 9, 11, 5]

# Create Button objects for each pin with internal pull-down resistors
buttons = {pin: Button(pin, pull_up=False) for pin in GPIO_PINS}

try:
    while True:
        states = {pin: btn.is_pressed for pin, btn in buttons.items()}
        print(states)
        sleep(0.5)
except KeyboardInterrupt:
    print("Exiting GPIO monitor.")
