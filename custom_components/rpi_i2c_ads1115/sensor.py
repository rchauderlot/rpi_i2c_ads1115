"""Custom sensor platform integration for ADS1115."""
from __future__ import annotations

import logging
import voluptuous as vol
from datetime import timedelta, datetime
import time

from homeassistant.const import CONF_PLATFORM, CONF_NAME, UnitOfElectricPotential
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

import asyncio


from .const import (
    DOMAIN,
    VALID_ADDRESSES,
    VALID_PINS,
    VALID_DIFF_PINS,
    VALID_GAINS,
    LABEL_ADDRESS,
    LABEL_PIN,
    LABEL_DIFFPIN,
    LABEL_GAIN,
    LABEL_UPDATE_INTERVAL
)


import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from adafruit_ads1x15.ads1x15 import Mode
import board
import busio
            

_LOGGER = logging.getLogger(__name__)



PLATFORM_SCHEMA = vol.Schema({
    vol.Required(CONF_PLATFORM): cv.string,
    vol.Required(CONF_NAME): cv.string,
    vol.Required(LABEL_ADDRESS): vol.In(VALID_ADDRESSES),
    vol.Required(LABEL_PIN): vol.In(VALID_PINS),
    vol.Required(LABEL_DIFFPIN): vol.In(VALID_DIFF_PINS),
    vol.Required(LABEL_GAIN): vol.In(VALID_GAINS),
    vol.Required(LABEL_UPDATE_INTERVAL, default=0.5): cv.positive_float,
})


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
#    _LOGGER.warning("entry.data "+ ", ".join(entry.data))
    config = entry.data
    name = config[CONF_NAME]
    address = config[LABEL_ADDRESS]
    pin = config[LABEL_PIN]
    differential_pin = config[LABEL_DIFFPIN]
    gain = config[LABEL_GAIN]
    update_interval = config[LABEL_UPDATE_INTERVAL]
    unique_id = f"{address}_{pin}"
    
    sensor = ADS1115Sensor(unique_id, name, address, pin, differential_pin, gain, update_interval)
    async_add_entities([sensor], True)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
#    _LOGGER.warning("config "+ ", ".join(config))
    if (CONF_NAME in config):
        name = config[CONF_NAME]
        address = config[LABEL_ADDRESS]
        pin = config[LABEL_PIN]
        differential_pin = config[LABEL_DIFFPIN]
        gain = config[LABEL_GAIN]
        update_interval = config[LABEL_UPDATE_INTERVAL]
        unique_id = f"{address}_{pin}"
        
        sensor = ADS1115Sensor(unique_id, name, address, pin, differential_pin, gain, update_interval)
        add_entities([sensor], True)


    
class ADS1115Sensor(SensorEntity):
   
    def __init__(self, unique_id, name, address, pin, differential_pin, gain, update_interval):
        self._unique_id = unique_id
        self._name = name
        self._address = address
        self._pin = pin
        self._differential_pin = differential_pin
        self._gain = gain
        self._update_interval = update_interval
        self._state = None
        self._async_read_listener = None
        # Create maps to match internal variable values to adafruit lib values
        self._address_map = {
            VALID_ADDRESSES[0]: 0x48,
            VALID_ADDRESSES[1]: 0x49,
            VALID_ADDRESSES[2]: 0x4A,
            VALID_ADDRESSES[3]: 0x4B
        }
        self._pin_map = {
            VALID_PINS[0] : ADS.P0,
            VALID_PINS[1]: ADS.P1,
            VALID_PINS[2]: ADS.P2,
            VALID_PINS[3]: ADS.P3
        }
        self._diff_pin_map = {
            VALID_DIFF_PINS[0]: None,
            VALID_DIFF_PINS[1]: ADS.P0,
            VALID_DIFF_PINS[2]: ADS.P1,
            VALID_DIFF_PINS[3]: ADS.P2,
            VALID_DIFF_PINS[4]: ADS.P3
        }
        self._gain_map = {
            VALID_GAINS[0]: 2 / 3,
            VALID_GAINS[1]: 1,
            VALID_GAINS[2]: 2,
            VALID_GAINS[3]: 4,
            VALID_GAINS[4]: 8,
            VALID_GAINS[5] : 16
        }



    @property
    def unique_id(self):
        return self._unique_id

    @property
    def native_unit_of_measurement(self):
        return UnitOfElectricPotential.VOLT

    @property
    def device_class(self):
        return SensorDeviceClass.VOLTAGE
        
    @property
    def state_class(self):
        return SensorStateClass.MEASUREMENT
        
    @property
    def name(self):
        return self._name

    @property
    def updater_interval(self):
        return self._update_interval
    
    @property
    def state(self):
        return self._state


    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        
        self._async_read_listener = self.hass.helpers.event.async_track_time_interval(
            self.async_read,
            timedelta(seconds=self._update_interval)
        )
            
        
    async def async_will_remove_from_hass(self):
        if self._async_read_listener:
            self._async_read_listener()
            self._async_read_listener = None
            

            
            
    async def async_read(self, _ = None) -> None:
        """Reads the sensor value."""
        new_voltage = None

        # Validate that the pin an diff pin are not equal
        if self._pin == self._differential_pin:
            _LOGGER.error("pin and differential_pin cannot be equal.")
            self._state = None
            return

        try:            
            # Initialize the sensor
            i2c_ = busio.I2C(board.SCL, board.SDA)
            ads = ADS.ADS1115(
                i2c = i2c_,
                gain = self._gain_map[self._gain],
                data_rate = None,
                mode = Mode.SINGLE,
                address = self._address_map[self._address]
            )
            # Obtain and store the analog value
            analog_read = AnalogIn(
                ads,
                self._pin_map[self._pin],
                self._diff_pin_map[self._differential_pin]
            )
            #new_voltage = analog_read.voltage

            # Remove decimals
            new_voltage = (int(analog_read.voltage*1000.0))/1000.0
            
        except Exception as ex:
            _LOGGER.error("Error while reading the sensor: %s", ex)
            self._state = None

            
        threashold = 0.05
        if new_voltage != None and (self._state == None or new_voltage > (self._state * (1.0 + threashold)) or new_voltage < (self._state * (1.0 - threashold))) :
            self._state = new_voltage
            self.async_schedule_update_ha_state()
    

        
            
    def log_internal_status(self):
        ## To debug the internal status
        _LOGGER.warning("address " + self._address)
        _LOGGER.warning(self._address_map[self._address])
        _LOGGER.warning("pin " + self._pin)
        _LOGGER.warning(self._pin_map[self._pin])
        _LOGGER.warning("diffenrentialPin " + self._differential_pin)
        _LOGGER.warning(self._diff_pin_map[self._differential_pin])
        _LOGGER.warning("gain " + self._gain)
        _LOGGER.warning( self._gain_map[self._gain])
