import time
from machine import Pin, I2C
from csv_logger import CsvLogger

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
    time.sleep(0.1)