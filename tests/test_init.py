"""Test linznetz setup process."""
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.exceptions import ConfigEntryNotReady

from custom_components.linznetz import (
    async_reload_entry,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.linznetz.const import DOMAIN, CONF_METER_POINT_NUMBER

from .const import MOCK_CONFIG
from .test_common import auto_enable_custom_integrations


# TODO
async def test_setup_unload_and_reload_entry(hass):
    """Test entry setup and unload."""
    # Create a mock entry so we don't have to go through config flow
    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG)

    # Set up the entry and assert that the values set during setup are where we expect
    # them to be.
    assert await async_setup_entry(hass, config_entry)
    assert DOMAIN in hass.data
    # Since we don't use coordinators we have nothing in the domain dictionary
    # assert config_entry.entry_id in hass.data[DOMAIN]

    # Cannot check as well since nothing checkable happens...
    # # Reload the entry and assert that the data from above is still there
    # assert await async_reload_entry(hass, config_entry) is None
    # assert DOMAIN in hass.data and config_entry.entry_id in hass.data[DOMAIN]

    # # Unload the entry and verify that the data has been removed
    # assert await async_unload_entry(hass, config_entry)
    # assert config_entry.entry_id not in hass.data[DOMAIN]
