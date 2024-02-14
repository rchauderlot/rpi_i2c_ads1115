"""Config flow for ADS1115 sensor integration."""
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig
)

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


_LOGGER = logging.getLogger(__name__)


# Schema to config the sensor in the UI
CONFIG_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(LABEL_ADDRESS): vol.In(VALID_ADDRESSES),
    vol.Required(LABEL_PIN): vol.In(VALID_PINS),
    vol.Required(LABEL_DIFFPIN): vol.In(VALID_DIFF_PINS),
    vol.Required(LABEL_GAIN): vol.In(VALID_GAINS),
    vol.Required(LABEL_UPDATE_INTERVAL, default=0.5): cv.positive_float,
})




class ADS1115SensorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for ADS1115 sensor integration."""

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(f"{user_input['address']}_{user_input['pin']}")
            self._abort_if_unique_id_configured()

            if user_input[LABEL_PIN] == user_input[LABEL_DIFFPIN]:
                errors['base'] = 'pin_differential_equal'

            if not errors:
                return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=CONFIG_SCHEMA,
            errors=errors
        )

    async def async_step_import(self, import_info):
        """Import existing configuration from configuration.yaml."""
        return await self.async_step_user(import_info)
