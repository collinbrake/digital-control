import time
import math
from machine import Pin, I2C, Timer

# =========================================================
# I2C
# =========================================================

i2c = I2C(
    1,
    scl=Pin(19),
    sda=Pin(18),
    freq=400_000
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
T = 1          # control period (ms)
k = 0           # sample count
omega2 = 2*(T/1000)**2    # chirp function frequency squared
A = 1500
dist_cm = 0
i2c_error_count = 0

# =========================================================
# Timer ISR
# =========================================================

def timer_isr(timer):
    # Ctrl-C can land inside this hard-IRQ (it fires 1000x/s)
    # instead of the main loop; catch it here so it stops the
    # timer cleanly instead of repeating every tick forever.
    try:
        _timer_isr_body(timer)
    except KeyboardInterrupt:
        timer.deinit()


def _timer_isr_body(timer):

    global dac_buf
    global k
    global val 
    global dist_cm

    # -------------------------------------------------
    # Read distance sensor
    #
    # On failure, keep the last known dist_cm; a truly
    # stuck bus will also fail the DAC write below, which
    # is what trips the error counter and stops the timer.
    # -------------------------------------------------

    try:
        raw = i2c.readfrom_mem(
            DIST_ADDR,
            REG_DIST,
            2
        )
        dist_cm = (raw[0] * 16 + raw[1]) / 64
    except OSError:
        pass

    # k must advance once per tick regardless of I2C outcome,
    # since it stands in for real elapsed time in the chirp below
    k += 1

    val = A*math.cos(omega2*(k**2))

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

    global i2c_error_count

    try:
        i2c.writeto(DAC_ADDR, dac_buf, True)
        i2c_error_count = 0
    except OSError:
        i2c_error_count += 1
        if i2c_error_count >= 10:
            timer.deinit()
        return

    # -----------------------------------------------------
    # Assert and de-assert active-low latch
    #
    # LOW  -> latch asserted
    # HIGH -> latch released
    # -----------------------------------------------------

    latch_n.value(0)
    latch_n.value(1)

    file.write(str(k) + "," + str(dist_cm) + "," + str(val) + "\r\n")
    
# =========================================================
# CSV logging
# =========================================================

file = open("data.csv", "w")
file.write("k,dist_cm,dac_i2c\r\n")

# =========================================================
# Check I2C devices
# =========================================================

print("I2C devices found:")

for address in i2c.scan():
    print(hex(address))

# =========================================================
# Start timer
# =========================================================

timer = Timer(-1)

timer.init(
    freq=1000/T,
    mode=Timer.PERIODIC,
    callback=timer_isr
)

try:

    while True:
        # -------------------------------------------------
        # Print (throttled; USB-serial print on every
        # iteration blocks the loop far longer than 1 ms)
        # -------------------------------------------------

        print(
            k,
            dist_cm,
            val
        )

        time.sleep(1)

except KeyboardInterrupt:

    print("Stopping...")

finally:

    timer.deinit()
    file.close()