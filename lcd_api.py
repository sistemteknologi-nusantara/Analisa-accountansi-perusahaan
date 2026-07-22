import time

class LcdApi:
    LCD_CLEAR_DISPLAY = 0x01
    LCD_RETURN_HOME = 0x02
    LCD_ENTRY_MODE_SET = 0x04
    LCD_DISPLAY_CONTROL = 0x08
    LCD_CURSOR_SHIFT = 0x10
    LCD_FUNCTION_SET = 0x20
    LCD_SET_CGRAM_ADDR = 0x40
    LCD_SET_DDRAM_ADDR = 0x80

    LCD_ENTRY_RIGHT = 0x00
    LCD_ENTRY_LEFT = 0x02
    LCD_ENTRY_SHIFT_INCREMENT = 0x01
    LCD_ENTRY_SHIFT_DECREMENT = 0x00

    LCD_DISPLAY_ON = 0x04
    LCD_DISPLAY_OFF = 0x00
    LCD_CURSOR_ON = 0x02
    LCD_CURSOR_OFF = 0x00
    LCD_BLINK_ON = 0x01
    LCD_BLINK_OFF = 0x00

    LCD_DISPLAY_MOVE = 0x08
    LCD_CURSOR_MOVE = 0x00

    LCD_8BIT_MODE = 0x10
    LCD_4BIT_MODE = 0x00
    LCD_2LINE = 0x08
    LCD_1LINE = 0x00
    LCD_5x10DOTS = 0x04
    LCD_5x8DOTS = 0x00

    def __init__(self, num_lines, num_columns):
        self.num_lines = num_lines
        if self.num_lines > 4:
            self.num_lines = 4
        self.num_columns = num_columns
        if self.num_columns > 40:
            self.num_columns = 40
        self.cursor_x = 0
        self.cursor_y = 0
        self.backlight = True
        self.display_off()
        self.backlight_on()
        self.clear()
        self.hal_write_command(self.LCD_ENTRY_MODE_SET | self.LCD_ENTRY_LEFT)
        self.display_on()

    def clear(self):
        self.hal_write_command(self.LCD_CLEAR_DISPLAY)
        time.sleep_ms(2)

    def home(self):
        self.hal_write_command(self.LCD_RETURN_HOME)
        time.sleep_ms(2)

    def set_cursor(self, x, y):
        self.cursor_x = x
        self.cursor_y = y
        addr = x
        if y == 0:
            addr |= 0x00
        elif y == 1:
            addr |= 0x40
        elif y == 2:
            addr |= 0x14
        elif y == 3:
            addr |= 0x54
        self.hal_write_command(self.LCD_SET_DDRAM_ADDR | addr)

    def write_char(self, char):
        self.hal_write_data(ord(char))
        self.cursor_x += 1
        if self.cursor_x >= self.num_columns:
            self.cursor_x = 0
            self.cursor_y += 1
            if self.cursor_y >= self.num_lines:
                self.cursor_y = 0

    def putstr(self, string):
        for char in string:
            self.write_char(char)

    def custom_char(self, location, charmap):
        location &= 0x7
        self.hal_write_command(self.LCD_SET_CGRAM_ADDR | (location << 3))
        for i in range(8):
            self.hal_write_data(charmap[i])

    def display_on(self):
        self.display_control = self.LCD_DISPLAY_ON | self.LCD_CURSOR_OFF | self.LCD_BLINK_OFF
        self.hal_write_command(self.LCD_DISPLAY_CONTROL | self.display_control)

    def display_off(self):
        self.display_control = self.LCD_DISPLAY_OFF | self.LCD_CURSOR_OFF | self.LCD_BLINK_OFF
        self.hal_write_command(self.LCD_DISPLAY_CONTROL | self.display_control)

    def backlight_on(self):
        self.backlight = True

    def backlight_off(self):
        self.backlight = False

    def hal_write_command(self, cmd):
        raise NotImplementedError

    def hal_write_data(self, data):
        raise NotImplementedError


class I2cLcd(LcdApi):
    def __init__(self, i2c, num_lines, num_columns, i2c_addr=0x27):
        self.i2c = i2c
        self.i2c_addr = i2c_addr
        self.bits = 0
        self.init_done = False

        try:
            self.i2c.writeto(self.i2c_addr, bytearray([0]))
            time.sleep_ms(20)
            self.write_init(0x03)
            self.write_init(0x03)
            self.write_init(0x03)
            self.write_init(0x02)

            self.hal_write_command(self.LCD_FUNCTION_SET | self.LCD_4BIT_MODE | self.LCD_2LINE | self.LCD_5x8DOTS)
            self.hal_write_command(self.LCD_DISPLAY_CONTROL | self.LCD_DISPLAY_OFF)
            self.hal_write_command(self.LCD_CLEAR_DISPLAY)
            self.hal_write_command(self.LCD_ENTRY_MODE_SET | self.LCD_ENTRY_LEFT)

            self.display_on()
            self.set_cursor(0, 0)
            self.init_done = True
        except Exception as e:
            print("LCD tidak terdeteksi:", e)

    def write_init(self, cmd):
        self.write_byte(cmd << 4)
        time.sleep_ms(5)

    def write_byte(self, data):
        self.bits = data
        if self.backlight:
            self.bits |= 0x08
        self.i2c.writeto(self.i2c_addr, bytearray([self.bits]))

    def hal_write_command(self, cmd):
        self.write_byte((cmd & 0xF0) | 0x04)
        self.write_byte((cmd & 0xF0) & 0xFB)
        self.write_byte(((cmd & 0x0F) << 4) | 0x04)
        self.write_byte(((cmd & 0x0F) << 4) & 0xFB)
        if cmd <= 3:
            time.sleep_ms(5)

    def hal_write_data(self, data):
        self.write_byte((data & 0xF0) | 0x05)
        self.write_byte((data & 0xF0) & 0xFB)
        self.write_byte(((data & 0x0F) << 4) | 0x05)
        self.write_byte(((data & 0x0F) << 4) & 0xFB)
