import argparse
import csv
import random
from pathlib import Path


SCHEDULING_PATH = Path("scheduling_data.csv")
PROCESS_PATH = Path("process_data.csv")
SEED = 20260610

DEFAULT_FIELDNAMES = ["Process", "Burst time", "Arrival Time", "", "Arrival Time(normalized)"]

SCHED_MIN_MAX = {
    "mean_burst": (1.9, 17.5),
    "std_burst": (1.1135528725660042, 8.282511696339462),
    "mean_arrival": (0.7, 8.2),
    "std_arrival": (0.4472135954999579, 4.409081537009721),
}


def scale(value, source_min, source_max, target_min, target_max):
    if source_max == source_min:
        return target_min
    position = (value - source_min) / (source_max - source_min)
    return target_min + position * (target_max - target_min)


def round_to_quarter(value):
    return round(value * 4) / 4


def clamp(value, lower, upper):
    return max(lower, min(upper, value))


def fmt_decimal(value):
    text = f"{value:.4f}"
    return text.rstrip("0").rstrip(".")


def load_process_rows(path):
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    return reader.fieldnames, rows


def scheduling_slice(path, start_row, count):
    rows = []
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row_number, row in enumerate(reader, start=1):
            if row_number < start_row:
                continue
            rows.append(row)
            if len(rows) == count:
                break
    return rows


def synthesize_rows(source_rows, start_process_number):
    rng = random.Random(SEED + start_process_number)
    new_rows = []

    for offset, source in enumerate(source_rows):
        mean_burst = float(source["mean_burst"])
        std_burst = float(source["std_burst"])
        mean_arrival = float(source["mean_arrival"])
        std_arrival = float(source["std_arrival"])

        burst_center = scale(
            mean_burst,
            *SCHED_MIN_MAX["mean_burst"],
            20,
            380,
        )
        burst_spread = scale(
            std_burst,
            *SCHED_MIN_MAX["std_burst"],
            8,
            55,
        )
        arrival_center = scale(
            mean_arrival,
            *SCHED_MIN_MAX["mean_arrival"],
            2.5,
            100,
        )
        arrival_spread = scale(
            std_arrival,
            *SCHED_MIN_MAX["std_arrival"],
            2,
            18,
        )

        burst = int(round(clamp(rng.gauss(burst_center, burst_spread), 10, 400)))
        arrival = round_to_quarter(
            clamp(rng.gauss(arrival_center, arrival_spread), 2.5, 100.0)
        )

        new_rows.append(
            {
                "Process": f"P{start_process_number + offset}",
                "Burst time": str(burst),
                "Arrival Time": fmt_decimal(arrival),
                "": "",
                "Arrival Time(normalized)": fmt_decimal(arrival / 100),
            }
        )

    return new_rows


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic process rows and write/overwrite process_data.csv"
    )
    parser.add_argument("--count", type=int, default=10000)
    parser.add_argument("--source-start", type=int, default=501)
    args = parser.parse_args()

    fieldnames = DEFAULT_FIELDNAMES

    if not PROCESS_PATH.exists():
        print(f"File '{PROCESS_PATH}' does not exist. It will be created.")
    elif PROCESS_PATH.stat().st_size == 0:
        print(f"File '{PROCESS_PATH}' is empty. Generating new data.")
    else:
        print(f"File '{PROCESS_PATH}' is not empty. Cleaning (overwriting) it with new data.")
        try:
            with PROCESS_PATH.open(newline="") as handle:
                reader = csv.DictReader(handle)
                if reader.fieldnames:
                    fieldnames = reader.fieldnames
        except Exception:
            pass

    next_process_number = 1
    source_rows = scheduling_slice(SCHEDULING_PATH, args.source_start, args.count)

    if len(source_rows) != args.count:
        raise ValueError(
            f"Requested {args.count} source rows from {args.source_start}, "
            f"but found {len(source_rows)}."
        )

    process_rows = synthesize_rows(source_rows, next_process_number)

    with PROCESS_PATH.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(process_rows)


if __name__ == "__main__":
    main()
