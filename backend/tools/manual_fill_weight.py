from numbers import Number
import datetime
import time
from tqdm import tqdm
import readline  # for up arrow history support in input
import csv
import os

EXPECTED_START_TOTAL_WEIGHT_KG = 24
# around 28-32
EXPECTED_FULL_TOTAL_WEIGHT_KG = 28
EXPECTED_FULL_N2O_WEIGHT_KG = EXPECTED_FULL_TOTAL_WEIGHT_KG - \
    EXPECTED_START_TOTAL_WEIGHT_KG


def process_reading(START_TIME_S: float, mv: Number, csv_path: str):
    # Show the user the value they entered, the time they entered it and a progress bar.
    # Every logged value from then on is stored in a CSV with raw value and time
    current_fill_time = time.monotonic() - START_TIME_S
    weight_kg = millivolts_to_kg(mv)

    fill_percentage = ((weight_kg-EXPECTED_START_TOTAL_WEIGHT_KG) /
                       (EXPECTED_FULL_N2O_WEIGHT_KG))*100

    update_csv(csv_path, [current_fill_time, mv, weight_kg, fill_percentage])
    print("-"*50)
    print(f"mV: \x1b[1m\x1b[33m{round(mv, 3)}\x1b[0m")
    print(
        f"kg: \x1b[1m\x1b[31m{round(weight_kg, 3)}\x1b[0m / {EXPECTED_FULL_TOTAL_WEIGHT_KG}kg {round(fill_percentage,2)}%")
    cft_minutes, cft_sec = divmod(current_fill_time, 60)
    cft_whole_seconds = int(cft_sec)
    cft_milliseconds = int((cft_sec - cft_whole_seconds) * 1000)

    formatted_time = f"{int(cft_minutes):02d}:{cft_whole_seconds:02d}.{cft_milliseconds:03d}"

    print(f"time: \x1b[1m\x1b[44m{formatted_time}\x1b[0m")

    if weight_kg > EXPECTED_FULL_TOTAL_WEIGHT_KG*2:
        print("\x1b[1m\x1b[33mPOSSIBLE INCORRECT VALUE. logged anyway\x1b[0m")
    # Draw progress bar
    if weight_kg < 0:
        print("Negative value detected, assume 0kg")
    elif weight_kg < EXPECTED_START_TOTAL_WEIGHT_KG:
        print(
            f"----- \x1b[35mBELOW START VALUE ({round(fill_percentage,2)}%)\x1b[0m {round(weight_kg,2)}kg / {EXPECTED_FULL_TOTAL_WEIGHT_KG}kg -----")
    elif EXPECTED_START_TOTAL_WEIGHT_KG < weight_kg < EXPECTED_FULL_TOTAL_WEIGHT_KG:
        bar = tqdm(total=1,
                   bar_format="{l_bar}{bar} ({percentage:3.0f}%)"
                   )
        bar.n = fill_percentage/100
        bar.refresh()
        bar.close()    # Overwrite?
    else:
        print(
            f"@@@@@@ \x1b[44mLIKELY FULL ({round(fill_percentage,2)}%)\x1b[0m {round(weight_kg,2)}kg / {EXPECTED_FULL_TOTAL_WEIGHT_KG}kg @@@@@@")


def millivolts_to_kg(mv: Number):
    # kg = 1.8799 * mv - 0.8836
    return (1.8799 * mv) - 0.8836


def create_csv_file():
    current_time = datetime.datetime.now()
    timestamp = current_time.strftime("%F_%T_%z")
    csv_path = os.path.join(os.getcwd(), "TEMP_LOG_" + timestamp + ".csv")
    with open(csv_path, "w") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["fill timestamp (s)", "reading (mV)", "rocket weight (kg)", "fill percentage"])
    return csv_path


def update_csv(csv_path, row: list):
    with open(csv_path, "a")as f:
        writer = csv.writer(f)
        writer.writerow(row)


def main():
    # As soon as the user hits enter, a timer starts
    os.system("clear")
    csv_path = create_csv_file()
    if csv_path is None:
        print("Failed to create CSV. Please restart")

    print('-'*50)
    print("WHEN FILL STARTS, PRESS ENTER TO START PROGRAM AND STOPWATCH")
    input("press enter to start ...")
    start_time_s = time.monotonic()
    while True:
        try:
            mv = float(input("millivoltage:\n> "))
        except Exception:
            print("INVALID INPUT")
            continue
        process_reading(start_time_s, mv, csv_path)


if __name__ == "__main__":
    main()
