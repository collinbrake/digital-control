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
        row = [str(values.get(col, "")) for col in self.columns]
        self.file.write(",".join(row) + "\r\n")
        self.file.flush()

    def close(self):
        self.file.close()


# ---------------------------------------------------------
# I2C setup
# ---------------------------------------------------------

i2c = I2C(
    1,
    scl=Pin(19),
    sda=Pin(18),
    freq=100_000
)

# Distance sensor
DIST_ADDR = 0x40
REG_DIST = 0x5E

# DT system
DT_ADDR = 0x60


# ---------------------------------------------------------
# DT system
# ---------------------------------------------------------

val = 0


def DT_system(source):
    global val

    # Increment command
    val = val + 8

    # Wrap val into the range -4096 to +4095
    val = ((val + 4096) % 8192) - 4096

    # Separate positive and negative portions
    if val > 0:
        vp = val
        vn = 0
    else:
        vp = 0
        vn = -val

    # Split positive value into high and low bytes
    hip = int(vp / 256)
    lop = int(vp) % 256

    # Split negative value magnitude into high and low bytes
    hin = int(vn / 256)
    lon = int(vn) % 256

    # Construct I2C packet
    buf = bytearray([
        0x08,
        hip,
        lop,
        0x00,
        hin,
        lon
    ])

    # Send packet to device at 0x60
    i2c.writeto(DT_ADDR, buf, True)


# ---------------------------------------------------------
# Main program
# ---------------------------------------------------------

print("I2C devices found:", [hex(addr) for addr in i2c.scan()])

logger = CsvLogger(
    "data.csv",
    ["time_s", "dist_cm", "dac_i2c"]
)

start_ms = time.ticks_ms()

try:
    while True:

        # ---------------------------------------------
        # Read distance sensor
        # ---------------------------------------------

        raw = i2c.readfrom_mem(
            DIST_ADDR,
            REG_DIST,
            2
        )

        dist_cm = (raw[0] * 16 + raw[1]) / 64

        # ---------------------------------------------
        # Run DT system
        # ---------------------------------------------

        DT_system(dist_cm)

        # ---------------------------------------------
        # Calculate elapsed time
        # ---------------------------------------------

        elapsed_s = (
            time.ticks_diff(
                time.ticks_ms(),
                start_ms
            ) / 1000
        )

        # ---------------------------------------------
        # Print/log results
        # ---------------------------------------------

        print(
            "time:",
            elapsed_s,
            "dist:",
            dist_cm,
            "val:",
            val
        )

        logger.log(
            time_s=elapsed_s,
            dist_cm=dist_cm,
            dac_i2c=val
        )

        time.sleep(0.1)

except KeyboardInterrupt:
    print("Stopping...")

finally:
    logger.close()