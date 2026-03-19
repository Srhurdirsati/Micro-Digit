import machine
import utime
import st7789

# --- Pin definitions ---
ROW_PINS = [machine.Pin(i, machine.Pin.OUT) for i in range(0, 5)]  # GPIO0-4
COL_PINS = [machine.Pin(i, machine.Pin.IN, machine.Pin.PULL_DOWN) for i in range(6, 17)]  # GPIO6-16

# TFT display pins
TFT_SCK = machine.Pin(18)
TFT_MOSI = machine.Pin(19)
TFT_DC = machine.Pin(20)
TFT_RES = machine.Pin(21)
TFT_CS = machine.Pin(22)
TFT_BL = machine.Pin(17, machine.Pin.OUT)

# Encoder pins
ENC_A = machine.Pin(26, machine.Pin.IN, machine.Pin.PULL_UP)
ENC_B = machine.Pin(27, machine.Pin.IN, machine.Pin.PULL_UP)
ENC_BTN = machine.Pin(28, machine.Pin.IN, machine.Pin.PULL_UP)

# --- TFT Setup ---
spi = machine.SPI(0, baudrate=40000000, sck=TFT_SCK, mosi=TFT_MOSI)
display = st7789.ST7789(
    spi, 240, 240,
    reset=TFT_RES,
    dc=TFT_DC,
    cs=TFT_CS,
    rotation=0
)
TFT_BL.value(1)
display.init()
display.fill(st7789.BLACK)

# --- Encoder state ---
encoder_value = 0
last_a = ENC_A.value()

# --- Caps Lock state ---
capslock = False
capslock_last = False
typed_text = ""

# --- Key mapping ---
KEY_MAP = {
    # Row 0 (top row)
    (0, 0): "ESC", (0, 1): "!", (0, 2): "1", (0, 3): "@", (0, 4): "2",
    (0, 5): "#", (0, 6): "3", (0, 7): "$", (0, 8): "4", (0, 9): "%", (0,10): "5",
    # Row 1
    (1, 0): "TAB", (1, 1): "=", (1, 2): "9", (1, 3): "W", (1, 4): "F",
    (1, 5): "P", (1, 6): "G", (1, 7): "J", (1, 8): "L", (1, 9): "U", (1,10): "Y",
    # Row 2
    (2, 0): "CAPS", (2, 1): "+", (2, 2): "A", (2, 3): "R", (2, 4): "S",
    (2, 5): "T", (2, 6): "N", (2, 7): "E", (2, 8): "I", (2, 9): "O", (2,10): "ENTER",
    # Row 3
    (3, 0): "SHIFT", (3, 1): "Z", (3, 2): "X", (3, 3): "C", (3, 4): "V",
    (3, 5): "B", (3, 6): "K", (3, 7): "M", (3, 8): "<", (3, 9): ">", (3,10): "?",
    # Row 4 (bottom row)
    (4, 0): "CTRL", (4, 1): "CMD", (4, 2): "ALT", (4, 3): "SPACE", (4, 4): "ALT",
    (4, 5): "FN", (4, 6): "LEFT", (4, 7): "DOWN", (4, 8): "UP", (4, 9): "RIGHT", (4,10): "BLANK",
}

def scan_matrix():
    pressed = []
    for row_idx, row in enumerate(ROW_PINS):
        for r in ROW_PINS:
            r.value(0)
        row.value(1)
        utime.sleep_us(50)
        for col_idx, col in enumerate(COL_PINS):
            if col.value():
                pressed.append((row_idx, col_idx))
    return pressed

def read_encoder():
    global encoder_value, last_a
    a = ENC_A.value()
    b = ENC_B.value()
    if a != last_a:
        if a == 1:
            if b == 0:
                encoder_value += 1
            else:
                encoder_value -= 1
    last_a = a

def show_status(keys, enc_val, capslock, text):
    display.fill(st7789.BLACK)
    display.text(
        st7789.FONT_Default, "Keys:", 10, 10, st7789.WHITE, st7789.BLACK
    )
    y = 30
    for k in keys:
        display.text(
            st7789.FONT_Default, f"R{k[0]} C{k[1]}", 10, y, st7789.YELLOW, st7789.BLACK
        )
        y += 20
    display.text(
        st7789.FONT_Default, f"Encoder: {enc_val}", 10, 200, st7789.CYAN, st7789.BLACK
    )
    display.text(
        st7789.FONT_Default, f"Btn: {'PRESSED' if ENC_BTN.value()==0 else 'UP'}", 10, 220, st7789.GREEN, st7789.BLACK
    )
    display.text(
        st7789.FONT_Default, f"Caps: {'ON' if capslock else 'OFF'}", 120, 10, st7789.RED if capslock else st7789.WHITE, st7789.BLACK
    )
    if text:
        display.text(
            st7789.FONT_Default, text, 10, 120, st7789.WHITE, st7789.BLACK
        )

# --- Main loop ---
while True:
    keys = scan_matrix()
    read_encoder()

    # Caps Lock logic
    capslock_pressed = (0, 0) in keys
    if capslock_pressed and not capslock_last:
        capslock = not capslock
    capslock_last = capslock_pressed

    # Add text if capslock is on and a mapped key is pressed (not CAPS key)
    if capslock:
        for k in keys:
            if k in KEY_MAP and KEY_MAP[k] != "CAPS":
                if len(typed_text) < 20:  # limit text length
                    typed_text += KEY_MAP[k]
                utime.sleep(0.2)  # simple debounce

    show_status(keys, encoder_value, capslock, typed_text)
    utime.sleep(0.1)