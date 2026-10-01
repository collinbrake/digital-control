"""Fit an nth-order ARX difference equation to data/<today>_model.csv via least squares.

Adapted from p10_leastsquares.m: instead of fitting powers of x to f(x), the
regressor matrix X here is built from past input/output samples so that

    y[k] = -a1*y[k-1] - ... - an*y[k-n] + b0*u[k] + b1*u[k-1] + ... + bn*u[k-n]

and A = inv(X'*X)*X'*f gives the difference-equation coefficients [a1..an, b0..bn].
"""
import argparse
import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

DATA_DIR = Path(__file__).parent / "data"


def find_todays_file(suffix="model"):
    today = datetime.date.today().isoformat()
    candidates = sorted(DATA_DIR.glob(f"{today}_{suffix}.csv"))
    if not candidates:
        raise FileNotFoundError(f"No {today}_{suffix}.csv found in {DATA_DIR}")
    return candidates[-1]


def leastsquares_arx(y, u, order):
    """Build X, f and solve A = inv(X'*X)*X'*f for an ARX(order, order) model."""
    n = order
    rows = [
        [-y[k - i] for i in range(1, n + 1)] + [u[k - j] for j in range(n + 1)]
        for k in range(n, len(y))
    ]
    X = np.array(rows)
    f = np.array(y[n:])
    A = np.linalg.inv(X.T @ X) @ X.T @ f
    return A, X, f


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", default=None, help="CSV file to fit (default: today's data/*_model.csv)")
    parser.add_argument("--order", type=int, default=2, help="Difference equation order n (default: 2)")
    parser.add_argument("--input-col", default="dac_i2c", help="Input (u) column name")
    parser.add_argument("--output-col", default="dist_cm", help="Output (y) column name")
    parser.add_argument("--no-plot", action="store_true", help="Skip plotting the fit vs. measured data")
    args = parser.parse_args()

    csv_path = Path(args.file) if args.file else find_todays_file()
    print(f"Fitting {csv_path}")

    df = pd.read_csv(csv_path)
    y = df[args.output_col].to_numpy()
    u = df[args.input_col].to_numpy()

    n = args.order
    A, X, f = leastsquares_arx(y, u, n)
    a = A[:n]
    b = A[n:]

    rms = np.sqrt(np.sum((f - X @ A) ** 2) / len(f))

    print(f"\nARX({n},{n}) difference equation:")
    terms_y = " ".join(f"- ({a[i]:+.6g})*y[k-{i + 1}]" for i in range(n))
    terms_u = " + ".join(f"({b[j]:+.6g})*u[k-{j}]" for j in range(n + 1))
    print(f"y[k] = {terms_y} + {terms_u}")

    print("\nCoefficients:")
    for i, ai in enumerate(a, start=1):
        print(f"  a{i} = {ai:.6g}")
    for j, bj in enumerate(b):
        print(f"  b{j} = {bj:.6g}")

    print(f"\nRMS fit error: {rms:.6g}")

    if not args.no_plot:
        k = np.arange(n, len(y))
        fig, ax = plt.subplots()
        ax.plot(k, f, label="Measured")
        ax.plot(k, X @ A, label="ARX fit", linestyle="--")
        ax.set_xlabel("k")
        ax.set_ylabel(args.output_col)
        ax.legend()
        ax.grid(True)
        plt.show()


if __name__ == "__main__":
    main()
