"""Fit an nth-order ARX difference equation to data/<today>_model.csv via least squares.

Adapted from p10_leastsquares.m: instead of fitting powers of x to f(x), the
regressor matrix coefhere is built from past input/output samples so that

    y[k] = -a1*y[k-1] - ... - an*y[k-n] + b0*u[k] + b1*u[k-1] + ... + bn*u[k-n]

and M = inv(X'*X)*X'*f gives the difference-equation coefficients [a1..an, b0..bn].
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


def leastsquares_model(y, u, order):
    """Build M (y[k-1]...y[k-n],u[k]...u[k-n]), Y (y[k]) and solve coef = inv(M'*M)*M'*Y for difference equation model."""
    n = order
    rows = [
        [-y[k - i] for i in range(1, n + 1)] + [u[k - j] for j in range(n + 1)]
        for k in range(n, len(y))
    ]
    M = np.array(rows)
    Y = np.array(y[n:])
    coef = np.linalg.inv(M.T @ M) @ M.T @ Y
    return M, coef, Y

def simulate_model(u, y, a, b, n):
    # Run the model on the input data as a simulation
    y_sim = np.zeros(len(y))
    # populate the initial conditions
    for l in range(n):
        y_sim[l] = y[l]

    for l in range(n, len(y)):
        for i, ai in enumerate(a, start=1):
            y_sim[l] -= ai*y[l-i]
        for i, bi in enumerate(b):
            y_sim[l] += bi*u[l-i]
    return y_sim

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", default=None, help="CSV file to fit (default: today's data/*_model.csv)")
    parser.add_argument("--order", type=int, default=2, help="Difference equation order n (default: 2)")
    parser.add_argument("--input-col", default="dac_i2c", help="Input (u) column name")
    parser.add_argument("--output-col", default="dist_cm", help="Output (y) column name")
    parser.add_argument("--no-plot", action="store_true", help="Skip plotting the fit vs. measured data")
    parser.add_argument("--downsample", type=int, default=1, help="")
    args = parser.parse_args()

    csv_path = Path(args.file) if args.file else find_todays_file()
    print(f"Fitting {csv_path}")

    df = pd.read_csv(csv_path)
    y = df[args.output_col].to_numpy()
    u = df[args.input_col].to_numpy()

    if (args.downsample > 1):
        u = u[0:len(u):args.downsample]
        y = y[0:len(y):args.downsample]

    n = args.order
    M, coef, Y = leastsquares_model(y, u, n)
    a = coef[:n]
    b = coef[n:]

    rms = np.sqrt(np.sum((Y - M @ coef) ** 2) / len(Y))

    y_sim = simulate_model(u, y, a, b, n)

    print(f"\nDifference equation:")
    terms_y = " ".join(f"- ({a[i]:+.6g})*y[k-{i + 1}]" for i in range(n))
    terms_u = " + ".join(f"({b[j]:+.6g})*u[k-{j}]" for j in range(n + 1))
    print(f"y[k] = {terms_y} + {terms_u}")

    print("\nCoefficients:")
    for i, ai in enumerate(a, start=1):
        print(f"  a{i} = {ai:.6g}")
    for j, bj in enumerate(b):
        print(f"  b{j} = {bj:.6g}")

    print(f"\nRMS fit error: {rms:.6g}")

    if (args.order == 2):
        print("\nPoles:")
        p1 = -0.5*a[0] + 0.5*np.sqrt(a[0]**2 - 4*a[1])
        p2 = -0.5*a[0] - 0.5*np.sqrt(a[0]**2 - 4*a[1])
        print(f"  p1 = {p1:.6g}")
        print(f"  p2 = {p2:.6g}")


    if not args.no_plot:
    
        k = np.arange(n, len(y))
        fig, ax = plt.subplots()
        ax.plot(
            k,
            Y,
            color="black",
            alpha=0.9,
            linestyle="--",
            label="Measured chirp response",
            zorder=3,
        )
        ax.plot(
            k,
            M @ coef,
            color="#0B84F3",
            alpha=0.9,
            linestyle=(0, (8, 3)),
            label="Least squares difference equation result (M * coef)",
            zorder=2,
        )
        ax.plot(
            k,
            y_sim[n:],
            color="#E64B35",
            alpha=0.9,
            linestyle=(0, (2, 2)),
            label="Difference equation simulation",
            zorder=4,
        )
        ax1 = ax.twinx()
        ax1.plot(
            k,
            u[n:],
            color="green",
            alpha=0.2,
            linestyle="-",
            label="Chirp input",
            zorder=5,
        )
        ax.set_xlabel("k")
        ax.set_ylabel(args.output_col)
        ax1.set_ylabel(args.input_col)
        ax.legend(frameon=True)
        ax1.legend(frameon=True)
        ax.grid(True)
        plt.show()


if __name__ == "__main__":
    main()
