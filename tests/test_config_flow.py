"""Test linznetz config flow."""
from unittest.mock import patch
import pytest

from homeassistant import config_entries, data_entry_flow

from custom_components.linznetz.const import DOMAIN, CONF_METER_POINT_NUMBER

from .const import MOCK_CONFIG, MOCK_CONFIG_WITH_CUSTOM_NAME, MOCK_CONFIG_INVALID_LENGTH
from .test_common import auto_enable_custom_integrations


# This fixture bypasses the actual setup of the integration
# since we only want to test the config flow. We test the
# actual functionality of the integration in other test modules.
@pytest.fixture(autouse=True)
def bypass_setup_fixture():
    """Prevent setup."""
    with patch("custom_components.linznetz.async_setup", return_value=True,), patch(
        "custom_components.linznetz.async_setup_entry",
        return_value=True,
    ):
        yield


# Here we simiulate a successful config flow.
async def test_successful_config_flow(hass):
    """Test a successful config flow."""
    # Initialize a config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Check that the config flow shows the user form as the first step
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    # Only enter the meter point number
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_CONFIG
    )

    # Check that the config flow is complete and a new entry is created with
    # the input data
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == MOCK_CONFIG[CONF_METER_POINT_NUMBER]
    assert result["data"] == MOCK_CONFIG
    assert result["result"]


# Here we simiulate a successful config flow with optional name.
async def test_successful_config_flow_with_optional_name(hass):
    """Test a successful config flow."""
    # Initialize a config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Check that the config flow shows the user form as the first step
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    # Only enter the meter point number
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_CONFIG_WITH_CUSTOM_NAME
    )

    # Check that the config flow is complete and a new entry is created with
    # the input data
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == MOCK_CONFIG_WITH_CUSTOM_NAME[CONF_METER_POINT_NUMBER]
    assert result["data"] == MOCK_CONFIG_WITH_CUSTOM_NAME
    assert result["result"]


# In this case, we want to simulate a failure during the config flow.
async def test_failed_config_flow(hass):
    """Test a failed config flow due to credential validation failure."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_CONFIG_INVALID_LENGTH
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {"base": "invalid_length"}
