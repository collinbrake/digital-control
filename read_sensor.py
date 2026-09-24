import time
from machine import Pin, I2C


class CsvLogger:
    """Writes rows to a CSV file using named columns instead of positional values."""

    def __init__(self, filename, columns):
        self.columns = columns
        self.file = open(filename, "w")
        self.file.write(",".join(columns) + "\r\n")
        self.file.flush()

    def log(self, **values):
        # missing columns are written as empty fields so rows stay aligned
        row = [str(values.get(col, "")) for col in self.columns]
        self.file.write(",".join(row) + "\r\n")
        self.file.flush()

    def close(self):
        self.file.close()


i2c = I2C(1, scl=Pin(19), sda=Pin(18), freq=100_000)

ADDR = 0x40
REG_DIST = 0x5E

print(i2c.scan())

logger = CsvLogger("data.csv", ["time_s", "dist_cm"])
start_ms = time.ticks_ms()

while True:
    raw = i2c.readfrom_mem(ADDR, REG_DIST, 2)
    dist_cm = (raw[0] * 16 + raw[1]) / 64
    elapsed_s = time.ticks_diff(time.ticks_ms(), start_ms) / 1000
    print(elapsed_s, dist_cm)
    logger.log(time_s=elapsed_s, dist_cm=dist_cm)
    time.sleep(1)