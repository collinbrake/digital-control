import time
import math
from machine import Pin, I2C, Timer

# =========================================================
# Timer ISR
# =========================================================

def timer_isr(timer):

    global dac_buf
    global val 
    global dist_cm

    # -------------------------------------------------
    # Read distance sensor
    # -------------------------------------------------

    # raw = i2c.readfrom_mem(
    #     DIST_ADDR,
    #     REG_DIST,
    #     2
    # )

    # dist_cm = (raw[0] * 16 + raw[1]) / 64  

    t = (
        time.ticks_diff(
            time.ticks_ms(),
            start_ms
        ) / 1000
    )
           
    val = A*math.cos(omega2*(t**2))

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
# I2C
# =========================================================

i2c = I2C(
    1,
    scl=Pin(19),
    sda=Pin(18),
    freq=1_00_000
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
vp = 0          # positive DAC channel value, updated by main loop
vn = 0          # negative DAC channel value, updated by main loop
T = 1          # control period
t = 0           # elapsed time since start of main loop
omega2 = 0.1    # chirp function frequency squared
A = 1600
dist_cm = 0

start_ms = time.ticks_ms()

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

while True:
    # -------------------------------------------------
    # Print (throttled; USB-serial print on every
    # iteration blocks the loop far longer than 1 ms)
    # -------------------------------------------------

    print(
        t,
        dist_cm,
        val
    )

    time.sleep(0.1)