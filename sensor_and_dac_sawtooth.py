import time
from machine import Pin, I2C, Timer

from csv_logger import CsvLogger


# =========================================================
# I2C
# =========================================================

i2c = I2C(
    1,
    scl=Pin(19),
    sda=Pin(18),
    freq=100_000
)


# =========================================================
# Distance sensor
# =========================================================

DIST_ADDR = 0x40
REG_DIST = 0x5E


# =========================================================
# DAC
# =========================================================

DAC_ADDR = 0x60

# Active-low latch
latch_n = Pin(20, Pin.OUT, value=1)


# Pre-allocated DAC message buffer.
# This is important because the ISR should not create
# a new bytearray every time it executes.
dac_buf = bytearray(6)


# =========================================================
# Global val
# =========================================================

val = 0


# =========================================================
# Timer ISR
# =========================================================

def timer_isr(timer):
    global val

    # -----------------------------------------------------
    # Increment val
    # -----------------------------------------------------

    val = val + 8

    # -----------------------------------------------------
    # Keep val bounded from -4096 to +4095
    #
    # Equivalent to:
    #     val = ((val + 4096) % 8192) - 4096
    # -----------------------------------------------------

    val = ((val + 4096) % 8192) - 4096


    # -----------------------------------------------------
    # Express:
    #
    #     val = vp - vn
    #
    # with vp >= 0 and vn >= 0
    # -----------------------------------------------------

    if val > 0:
        vp = val
        vn = 0
    else:
        vp = 0
        vn = -val


    # -----------------------------------------------------
    # Split vp into two 8-bit bytes
    #
    # hip = four MSBs of the 12-bit value
    # lop = eight LSBs
    # -----------------------------------------------------

    hip = int(vp / 256)
    lop = int(vp) % 256


    # -----------------------------------------------------
    # Split vn into two 8-bit bytes
    # -----------------------------------------------------

    hin = int(vn / 256)
    lon = int(vn) % 256


    # -----------------------------------------------------
    # Create DAC message frame
    #
    # Byte 0: 0x08 -> VOUT1 write command
    # Bytes 1-2: VOUT1 data
    #
    # Byte 3: 0x00 -> VOUT0 write command
    # Bytes 4-5: VOUT0 data
    # -----------------------------------------------------

    dac_buf[0] = 0x08
    dac_buf[1] = hip
    dac_buf[2] = lop

    dac_buf[3] = 0x00
    dac_buf[4] = hin
    dac_buf[5] = lon


    # -----------------------------------------------------
    # Send message to DAC
    # -----------------------------------------------------

    i2c.writeto(DAC_ADDR, dac_buf, True)


    # -----------------------------------------------------
    # Assert and de-assert active-low latch
    #
    # LOW  -> latch asserted
    # HIGH -> latch released
    # -----------------------------------------------------

    latch_n.value(0)
    latch_n.value(1)


# =========================================================
# Check I2C devices
# =========================================================

print("I2C devices found:")

for address in i2c.scan():
    print(hex(address))


# =========================================================
# CSV logger
# =========================================================

logger = CsvLogger(
    "data.csv",
    [
        "time_s",
        "dist_cm",
        "dac_i2c"
    ]
)


# =========================================================
# Start timer
# =========================================================

timer = Timer(-1)

timer.init(
    freq=10,
    mode=Timer.PERIODIC,
    callback=timer_isr
)

# =========================================================
# Main loop
# =========================================================

start_ms = time.ticks_ms()

try:

    while True:

        # -------------------------------------------------
        # Read distance sensor
        # -------------------------------------------------

        raw = i2c.readfrom_mem(
            DIST_ADDR,
            REG_DIST,
            2
        )

        dist_cm = (raw[0] * 16 + raw[1]) / 64


        # -------------------------------------------------
        # Calculate elapsed time
        # -------------------------------------------------

        elapsed_s = (
            time.ticks_diff(
                time.ticks_ms(),
                start_ms
            ) / 1000
        )


        # -------------------------------------------------
        # Print
        # -------------------------------------------------

        print(
            elapsed_s,
            dist_cm,
            val
        )


        # -------------------------------------------------
        # Log
        # -------------------------------------------------

        logger.log(
            time_s=elapsed_s,
            dist_cm=dist_cm,
            dac_i2c=val
        )

        time.sleep(0.1)


except KeyboardInterrupt:

    print("Stopping...")


finally:

    timer.deinit()
    logger.close()