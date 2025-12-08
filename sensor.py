"""
Generic JSON API Integration for Home Assistant
Fetches JSON from an API and creates a sensor with the full JSON as attributes.
"""
import logging
import voluptuous as vol
from datetime import timedelta
import aiohttp
import async_timeout

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_NAME, CONF_URL
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import Throttle
from homeassistant.helpers import template as template_helper

_LOGGER = logging.getLogger(__name__)

CONF_AUTHORIZATION = "authorization"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_HEADERS = "headers"
CONF_ATTRIBUTES_TEMPLATE = "attributes_template"

DEFAULT_NAME = "JSON API Sensor"
DEFAULT_SCAN_INTERVAL = timedelta(minutes=5)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_URL): cv.url,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_AUTHORIZATION): cv.string,
    vol.Optional(CONF_HEADERS, default={}): vol.Schema({cv.string: cv.string}),
    vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.time_period,
    vol.Optional(CONF_ATTRIBUTES_TEMPLATE): cv.string,
})


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the JSON API sensor."""
    name = config[CONF_NAME]
    url = config[CONF_URL]
    authorization = config.get(CONF_AUTHORIZATION)
    headers = config.get(CONF_HEADERS, {})
    scan_interval = config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    attributes_template = config.get(CONF_ATTRIBUTES_TEMPLATE)
    
    session = async_get_clientsession(hass)
    
    sensor = JsonApiSensor(name, url, authorization, headers, session, scan_interval, attributes_template, hass)
    async_add_entities([sensor], True)


class JsonApiSensor(SensorEntity):
    """Representation of a JSON API sensor."""

    def __init__(self, name, url, authorization, headers, session, scan_interval, attributes_template, hass):
        """Initialize the sensor."""
        self._name = name
        self._url = url
        self._authorization = authorization
        self._headers = headers.copy()
        self._session = session
        self._state = None
        self._attributes = {}
        self._available = True
        self._scan_interval = scan_interval
        self._attributes_template = attributes_template
        self._hass = hass
        
        # Add authorization header if provided
        if self._authorization:
            self._headers["Authorization"] = self._authorization

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def available(self):
        """Return True if entity is available."""
        return self._available

    async def async_update(self):
        """Fetch new state data for the sensor."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.get(
                    self._url,
                    headers=self._headers
                )
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Apply attributes template if provided
                    if self._attributes_template:
                        try:
                            _LOGGER.debug(f"Applying attributes_template to data")
                            # Create a template object
                            tpl = template_helper.Template(self._attributes_template, self._hass)
                            # Render the template with the data as 'value_json'
                            rendered = tpl.async_render({'value_json': data})
                            # Convert to string if it's a Wrapper object
                            rendered_str = str(rendered)
                            _LOGGER.debug(f"Template rendered: {rendered_str[:200]}")
                            # Parse the rendered result as JSON
                            import json
                            processed_data = json.loads(rendered_str)
                            _LOGGER.debug(f"Template processing successful")
                            
                            # Handle the processed data
                            if isinstance(processed_data, list):
                                self._state = len(processed_data)
                                self._attributes = {"items": processed_data}
                            elif isinstance(processed_data, dict):
                                if "count" in processed_data:
                                    self._state = processed_data["count"]
                                elif "total" in processed_data:
                                    self._state = processed_data["total"]
                                else:
                                    self._state = "OK"
                                self._attributes = processed_data
                            else:
                                self._state = str(processed_data)
                                self._attributes = {"raw": processed_data}
                        except Exception as err:
                            _LOGGER.error(f"Error processing attributes_template: {err}")
                            # Fall back to default behavior
                            if isinstance(data, list):
                                self._state = len(data)
                                self._attributes = {"items": data}
                            elif isinstance(data, dict):
                                if "count" in data:
                                    self._state = data["count"]
                                elif "total" in data:
                                    self._state = data["total"]
                                else:
                                    self._state = "OK"
                                self._attributes = data
                            else:
                                self._state = str(data)
                                self._attributes = {"raw": data}
                    else:
                        # Default behavior - no template
                        if isinstance(data, list):
                            self._state = len(data)
                            self._attributes = {"items": data}
                        elif isinstance(data, dict):
                            if "count" in data:
                                self._state = data["count"]
                            elif "total" in data:
                                self._state = data["total"]
                            else:
                                self._state = "OK"
                            self._attributes = data
                        else:
                            self._state = str(data)
                            self._attributes = {"raw": data}
                    
                    self._available = True
                    _LOGGER.debug(f"Successfully fetched data from {self._url}")
                else:
                    _LOGGER.error(f"Error fetching data: HTTP {response.status}")
                    self._available = False
                    
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Error fetching data from {self._url}: {err}")
            self._available = False
        except Exception as err:
            _LOGGER.error(f"Unexpected error: {err}")
            self._available = False