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
MODEL_DIR = Path(__file__).parent / "model"


def find_todays_file(suffix="model"):
    today = datetime.date.today().isoformat()
    candidates = sorted(DATA_DIR.glob(f"{today}_{suffix}.csv"))
    if not candidates:
        raise FileNotFoundError(f"No {today}_{suffix}.csv found in {DATA_DIR}")
    return candidates[-1]


def build_regressors(y, u, n):
    """Build M (y[k-1]...y[k-n],u[k]...u[k-n]) and Y (y[k])."""
    rows = [
        [-y[k - i] for i in range(1, n + 1)] + [u[k - j] for j in range(n + 1)]
        for k in range(n, len(y))
    ]
    return np.array(rows), np.array(y[n:])


def leastsquares_model(y, u, order):
    """Solve M*coef = Y in the least-squares sense."""
    M, Y = build_regressors(y, u, order)
    coef, *_ = np.linalg.lstsq(M, Y, rcond=None)
    return M, coef, Y


def save_model(coef, n, source):
    MODEL_DIR.mkdir(exist_ok=True)
    names = [f"a{i}" for i in range(1, n + 1)] + [f"b{j}" for j in range(n + 1)]
    path = MODEL_DIR / f"{datetime.date.today().isoformat()}_model_order{n}.csv"
    pd.DataFrame([coef], columns=names).assign(source=source).to_csv(path, index=False)
    return path


def load_model(path):
    row = pd.read_csv(path).iloc[0]
    a = np.array([row[c] for c in row.index if c.startswith("a")], dtype=float)
    b = np.array([row[c] for c in row.index if c.startswith("b")], dtype=float)
    return np.concatenate([a, b]), len(a)


def simulate_model(u, y, a, b, n):
    # Run the model on the input data as a simulation
    y_sim = np.zeros(len(y))
    # populate the initial conditions
    for l in range(n):
        y_sim[l] = y[l]

    for l in range(n, len(y)):
        for i, ai in enumerate(a, start=1):
            y_sim[l] -= ai*y_sim[l-i]
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
    parser.add_argument("--start", type=int, default=None, help="First row (0-based) of the data to use")
    parser.add_argument("--end", type=int, default=None, help="Row (0-based) to stop at, exclusive")
    parser.add_argument("--save", action="store_true", help="Save coefficients to model/<date>_model_order<n>.csv")
    parser.add_argument("--model", default=None, help="Saved model CSV to simulate instead of fitting")
    args = parser.parse_args()

    csv_path = Path(args.file) if args.file else find_todays_file()

    df = pd.read_csv(csv_path).iloc[args.start:args.end]
    y = df[args.output_col].to_numpy()
    u = df[args.input_col].to_numpy()
    k0 = args.start or 0

    if args.model:
        print(f"Simulating {args.model} on {csv_path}")
        coef, n = load_model(args.model)
        M, Y = build_regressors(y, u, n)
    else:
        print(f"Fitting {csv_path}")
        n = args.order
        M, coef, Y = leastsquares_model(y, u, n)
    a = coef[:n]
    b = coef[n:]

    if args.save and not args.model:
        print(f"Saved model to {save_model(coef, n, csv_path.name)}")

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

    if n == 2:
        # complex D(Z) to calculate complex roots
        ac = a.astype(complex)
        print("\nPoles:")
        p1 = -0.5*ac[0] + 0.5*np.sqrt(ac[0]**2 - 4*ac[1])
        p2 = -0.5*ac[0] - 0.5*np.sqrt(ac[0]**2 - 4*ac[1])
        print(f"  p1 = {p1:.6g}")
        print(f"  p2 = {p2:.6g}")


    if not args.no_plot:
    
        k = np.arange(n, len(y)) + k0
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
