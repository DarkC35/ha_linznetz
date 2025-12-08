"""
Custom integration to integrate linznetz with Home Assistant.
"""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.core_config import Config

from .const import (
    DOMAIN,
    PLATFORMS,
)


async def async_setup(_hass: HomeAssistant, _config: Config):
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up linznetz from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # # only needed when client or coordinator is saved at hass.data[DOMAIN][entry.entry_id]
    # if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
    #     hass.data[DOMAIN].pop(entry.entry_id)
    # # otherwise this is enough:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
