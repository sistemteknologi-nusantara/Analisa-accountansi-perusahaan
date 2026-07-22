from machine import I2C, Pin
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
alamat = i2c.scan()
print("Alamat I2C yang terdeteksi:", [hex(a) for a in alamat])
