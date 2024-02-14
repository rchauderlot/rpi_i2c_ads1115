"""Constants for the rpi-i2c-ads1115 integration."""


DOMAIN = 'rpi_i2c_ads1115'

VALID_ADDRESSES = ['0x48', '0x49', '0x4A', '0x4B']
VALID_PINS = ['A0', 'A1', 'A2', 'A3']
VALID_DIFF_PINS = ['GND'] + VALID_PINS
VALID_GAINS = ['6.144V', '4.096V', '2.048V', '1.024V', '0.512V', '0.256V']

LABEL_ADDRESS = 'address'
LABEL_PIN = 'pin'
LABEL_DIFFPIN = 'differential_pin'
LABEL_GAIN = 'gain'
LABEL_UPDATE_INTERVAL='update_interval'
