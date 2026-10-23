# digital-control

## model_leastsquares.py

Fits a difference equation to CSV data using least squares.

```powershell
.venv\Scripts\Activate.ps1
python model_leastsquares.py --file data/2026-10-07_model_100Hz.csv
```

Truncate data with `--start`/`--end` (row indices), save the fit to `model/<date>_model_order<n>.csv` with `--save`, and simulate a saved model on data with `--model`:

```powershell
python model_leastsquares.py --file data/2026-10-07_model_100Hz.csv --start 10 --end 500 --save
python model_leastsquares.py --file data/2026-10-07_model_1kHz.csv --model model/2026-10-23_model_order2.csv
```

Without `--file`, it uses today's `data/<date>_model.csv`. Run `python model_leastsquares.py -h` for other options (`--order`, `--no-plot`, etc.).
