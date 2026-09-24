"""Pull data.csv off the Pico and plot it (run this on your PC, not the Pico)."""
import argparse
import datetime
import shutil
import subprocess
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

DATA_DIR = Path(__file__).parent / "data"


def fetch_data(port, remote_file="data.csv", local_file="data.csv"):
    cmd = ["mpremote"]
    if port:
        cmd += ["connect", port]
    cmd += ["fs", "cp", f":{remote_file}", local_file]
    subprocess.run(cmd, check=True)
    return local_file


def save_copy(local_file, description):
    DATA_DIR.mkdir(exist_ok=True)
    today = datetime.date.today().isoformat()
    dest = DATA_DIR / f"{today}_{description}.csv"
    shutil.copy(local_file, dest)
    print(f"Saved a copy to {dest}")
    return dest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", default=None, help="Serial port of the Pico, e.g. COM5")
    parser.add_argument("--file", default="data.csv", help="CSV filename on the Pico")
    parser.add_argument("--skip-fetch", action="store_true", help="Plot the local file without copying from the Pico")
    parser.add_argument("--save", metavar="DESCRIPTION", help="Save a copy to data/<today>_<DESCRIPTION>.csv")
    args = parser.parse_args()

    local_file = args.file if args.skip_fetch else fetch_data(args.port, args.file, args.file)

    saved_csv = save_copy(local_file, args.save) if args.save else None

    df = pd.read_csv(local_file)
    print(df.head())

    time_col = df.columns[0]
    fig, ax = plt.subplots()
    ax2 = ax.twinx()
    notfirst = False
    for col in df.columns[1:]:
        if notfirst:
            ax2.plot(df[time_col], df[col], label=col, color="red")
        else:
            ax.plot(df[time_col], df[col], label=col, color="blue")
        notfirst = True
    ax.set_xlabel(time_col)
    ax.legend()
    ax2.legend()

    if saved_csv:
        png_dest = saved_csv.with_suffix(".png")
        fig.savefig(png_dest)
        print(f"Saved plot to {png_dest}")

    plt.show()


if __name__ == "__main__":
    main()
