"""Test linznetz sensor."""
from decimal import Decimal

from unittest.mock import patch
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.recorder.common import (
    async_wait_recording_done,
)

from homeassistant.components.recorder.statistics import statistics_during_period
from homeassistant.exceptions import HomeAssistantError

from custom_components.linznetz import async_setup_entry
from custom_components.linznetz.const import (
    DEFAULT_NAME,
    DOMAIN,
    SENSOR,
    SERVICE_IMPORT_REPORT,
    END_TIME_KEY,
    START_TIME_KEY,
)
from custom_components.linznetz.sensor import (
    get_csv_data_list_from_file,
    get_csv_data_value_key,
    parse_csv_date_str,
    parse_german_number_str_to_decimal,
    parse_value_to_decimal,
    validate_hour_block,
)

from .const import MOCK_CONFIG


STATISTIC_ID = f"{SENSOR}.{DEFAULT_NAME.lower()}_energy"


DATA_WITH_INVALID_LENGTH = [
    {
        START_TIME_KEY: "17.09.2022 00:00",
        END_TIME_KEY: "17.09.2022 00:15",
        "Energiemenge in kWh": "1",
        "Ersatzwert": "",
    }
]
DATA_WITH_INVALID_ORDER = [
    {
        START_TIME_KEY: "17.09.2022 00:00",
        END_TIME_KEY: "17.09.2022 00:15",
        "Energiemenge in kWh": "1",
        "Ersatzwert": "",
    },
    {
        START_TIME_KEY: "17.09.2022 00:15",
        END_TIME_KEY: "17.09.2022 00:30",
        "Energiemenge in kWh": "1",
        "Ersatzwert": "",
    },
    {
        START_TIME_KEY: "17.09.2022 00:45",
        END_TIME_KEY: "17.09.2022 01:00",
        "Energiemenge in kWh": "1",
        "Ersatzwert": "",
    },
    {
        START_TIME_KEY: "17.09.2022 00:30",
        END_TIME_KEY: "17.09.2022 00:45",
        "Energiemenge in kWh": "1",
        "Ersatzwert": "",
    },
]
DATA_WITH_INVALID_PREFIX = [
    {
        START_TIME_KEY: "17.09.2022 00:00",
        END_TIME_KEY: "17.09.2022 00:15",
        "Energiemenge in kWh": "1",
        "Ersatzwert": "",
    },
    {
        START_TIME_KEY: "17.09.2022 01:15",
        END_TIME_KEY: "17.09.2022 00:30",
        "Energiemenge in kWh": "1",
        "Ersatzwert": "",
    },
    {
        START_TIME_KEY: "17.09.2022 00:30",
        END_TIME_KEY: "17.09.2022 00:45",
        "Energiemenge in kWh": "1",
        "Ersatzwert": "",
    },
    {
        START_TIME_KEY: "17.09.2022 00:45",
        END_TIME_KEY: "17.09.2022 01:00",
        "Energiemenge in kWh": "1",
        "Ersatzwert": "",
    },
]


async def prepare_and_call_import_service_mocked(hass, csv_data):
    """Helper to prepare and call the import service with mocked csv_data."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG)
    await async_setup_entry(hass, config_entry)
    await hass.async_block_till_done()

    with patch(
        "custom_components.linznetz.sensor.get_csv_data_list_from_file",
        return_value=csv_data,
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_IMPORT_REPORT,
            service_data={
                "entity_id": STATISTIC_ID,
                "path": "mocked",
            },
            blocking=True,
        )
    await async_wait_recording_done(hass)


async def get_statistics(hass, start_time, end_time=None, statistic_id=STATISTIC_ID):
    """Helper to get statistics during period."""
    stats = await hass.async_add_executor_job(
        statistics_during_period,
        hass,
        start_time,
        end_time,
        [statistic_id],
        "hour",
        None,
        {"sum", "state"},
    )
    return stats


def get_csv_data_sum(csv_data: list) -> Decimal:
    """Helper to calculate the sum of the csv_data."""
    csv_data_value_key = get_csv_data_value_key(csv_data)
    return sum(
        [parse_german_number_str_to_decimal(d[csv_data_value_key]) for d in csv_data]
    )


@pytest.fixture(autouse=True)
def auto_recorder_mock_and_enable_custom_integrations(
    recorder_mock, enable_custom_integrations
):
    """Enables recorder_mock and custom_integrations fixtures in the right order."""
    yield


async def test_import_service_with_actual_file(hass):
    """Test import service with actual file."""

    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG)
    assert await async_setup_entry(hass, config_entry)
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN,
        SERVICE_IMPORT_REPORT,
        service_data={
            "entity_id": STATISTIC_ID,
            "path": "tests/data/2022-09-17.csv",
        },
        blocking=True,
    )
    await async_wait_recording_done(hass)

    stats = await get_statistics(hass, parse_csv_date_str("17.09.2022 00:00"))

    assert len(stats) == 1
    assert len(stats[STATISTIC_ID]) == 24


async def test_import_service_with_missing_file(hass):
    """Test import service with missing file."""

    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG)
    assert await async_setup_entry(hass, config_entry)
    await hass.async_block_till_done()

    with pytest.raises(HomeAssistantError) as err:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_IMPORT_REPORT,
            service_data={
                "entity_id": STATISTIC_ID,
                "path": "tests/data/no-file.csv",
            },
            blocking=True,
        )
    assert err


async def test_import_service_with_no_previous_data(hass):
    """Test import service with no previous data."""

    csv_data = get_csv_data_list_from_file("tests/data/2022-09-17.csv")
    stats = await get_statistics(hass, parse_csv_date_str(csv_data[0][START_TIME_KEY]))
    assert len(stats) == 0

    await prepare_and_call_import_service_mocked(hass, csv_data)

    stats = await get_statistics(hass, parse_csv_date_str(csv_data[0][START_TIME_KEY]))
    assert len(stats) == 1
    assert len(stats[STATISTIC_ID]) == 24

    for i, stat in enumerate(stats[STATISTIC_ID]):
        assert stat["start"] == parse_csv_date_str(csv_data[(i * 4)][START_TIME_KEY])
    assert parse_value_to_decimal(stats[STATISTIC_ID][-1]["sum"]) == get_csv_data_sum(
        csv_data
    )


async def test_import_service_with_prvious_data(hass):
    """Test import service with no previous data."""

    prev_csv_data = get_csv_data_list_from_file("tests/data/2022-09-17.csv")
    stats = await get_statistics(
        hass, parse_csv_date_str(prev_csv_data[0][START_TIME_KEY])
    )
    assert len(stats) == 0
    await prepare_and_call_import_service_mocked(hass, prev_csv_data)
    stats = await get_statistics(
        hass, parse_csv_date_str(prev_csv_data[0][START_TIME_KEY])
    )
    assert len(stats) == 1
    assert len(stats[STATISTIC_ID]) == 24
    assert parse_value_to_decimal(stats[STATISTIC_ID][-1]["sum"]) == get_csv_data_sum(
        prev_csv_data
    )

    csv_data = get_csv_data_list_from_file("tests/data/2022-09-18.csv")
    stats = await get_statistics(hass, parse_csv_date_str(csv_data[0][START_TIME_KEY]))
    assert len(stats) == 0
    await prepare_and_call_import_service_mocked(hass, csv_data)
    stats = await get_statistics(hass, parse_csv_date_str(csv_data[0][START_TIME_KEY]))
    assert len(stats) == 1
    assert len(stats[STATISTIC_ID]) == 24

    stats_with_prev_data = await get_statistics(
        hass, parse_csv_date_str(prev_csv_data[0][START_TIME_KEY])
    )
    assert len(stats_with_prev_data) == 1
    assert len(stats_with_prev_data[STATISTIC_ID]) == 48
    assert parse_value_to_decimal(stats_with_prev_data[STATISTIC_ID][-1]["sum"]) == (
        get_csv_data_sum(prev_csv_data) + get_csv_data_sum(csv_data)
    )


async def test_import_service_before_previous_data(hass):
    """Test import service before previous data."""

    prev_csv_data = get_csv_data_list_from_file("tests/data/2022-09-18.csv")
    stats = await get_statistics(
        hass, parse_csv_date_str(prev_csv_data[0][START_TIME_KEY])
    )
    assert len(stats) == 0
    await prepare_and_call_import_service_mocked(hass, prev_csv_data)
    stats = await get_statistics(
        hass, parse_csv_date_str(prev_csv_data[0][START_TIME_KEY])
    )
    assert len(stats) == 1
    assert len(stats[STATISTIC_ID]) == 24
    assert parse_value_to_decimal(stats[STATISTIC_ID][-1]["sum"]) == get_csv_data_sum(
        prev_csv_data
    )

    csv_data = get_csv_data_list_from_file("tests/data/2022-09-17.csv")
    stats = await get_statistics(
        hass,
        parse_csv_date_str(csv_data[0][START_TIME_KEY]),
        parse_csv_date_str(csv_data[len(csv_data) - 1][START_TIME_KEY]),
    )
    assert len(stats) == 0
    await prepare_and_call_import_service_mocked(hass, csv_data)
    stats = await get_statistics(
        hass,
        parse_csv_date_str(csv_data[0][START_TIME_KEY]),
        parse_csv_date_str(csv_data[len(csv_data) - 1][START_TIME_KEY]),
    )
    assert len(stats) == 1
    assert len(stats[STATISTIC_ID]) == 24

    stats_with_prev_data = await get_statistics(
        hass, parse_csv_date_str(csv_data[0][START_TIME_KEY])
    )
    assert len(stats_with_prev_data) == 1
    assert len(stats_with_prev_data[STATISTIC_ID]) == 48
    assert parse_value_to_decimal(stats_with_prev_data[STATISTIC_ID][-1]["sum"]) == (
        get_csv_data_sum(prev_csv_data) + get_csv_data_sum(csv_data)
    )


async def test_import_service_update_with_modified_data(hass):
    """Test import service update with modified data."""

    prev_csv_data = get_csv_data_list_from_file("tests/data/2022-09-18.csv")
    stats = await get_statistics(
        hass, parse_csv_date_str(prev_csv_data[0][START_TIME_KEY])
    )
    assert len(stats) == 0
    await prepare_and_call_import_service_mocked(hass, prev_csv_data)
    stats = await get_statistics(
        hass, parse_csv_date_str(prev_csv_data[0][START_TIME_KEY])
    )
    assert len(stats) == 1
    assert len(stats[STATISTIC_ID]) == 24
    assert parse_value_to_decimal(stats[STATISTIC_ID][-1]["sum"]) == get_csv_data_sum(
        prev_csv_data
    )

    modified_csv_data = prev_csv_data.copy()
    csv_data_value_key = get_csv_data_value_key(modified_csv_data)
    modified_csv_data[0][csv_data_value_key] = "1"
    await prepare_and_call_import_service_mocked(hass, modified_csv_data)
    stats = await get_statistics(
        hass, parse_csv_date_str(modified_csv_data[0][START_TIME_KEY])
    )
    assert len(stats) == 1
    assert len(stats[STATISTIC_ID]) == 24
    assert parse_value_to_decimal(stats[STATISTIC_ID][-1]["sum"]) == get_csv_data_sum(
        modified_csv_data
    )


async def test_import_service_with_daylight_saving_change_winter(hass):
    """Test import service with daylight saving change in winter."""

    csv_data = get_csv_data_list_from_file("tests/data/2022-10-30.csv")
    stats = await get_statistics(hass, parse_csv_date_str(csv_data[0][START_TIME_KEY]))
    assert len(stats) == 0

    await prepare_and_call_import_service_mocked(hass, csv_data)

    stats = await get_statistics(hass, parse_csv_date_str(csv_data[0][START_TIME_KEY]))
    assert len(stats) == 1
    assert len(stats[STATISTIC_ID]) == 25

    assert parse_value_to_decimal(stats[STATISTIC_ID][-1]["sum"]) == get_csv_data_sum(
        csv_data
    )


async def test_import_service_with_daylight_saving_change_summer(hass):
    """Test import service with daylight saving change in summer."""

    csv_data = get_csv_data_list_from_file("tests/data/2022-03-27.csv")
    stats = await get_statistics(hass, parse_csv_date_str(csv_data[0][START_TIME_KEY]))
    assert len(stats) == 0

    await prepare_and_call_import_service_mocked(hass, csv_data)

    stats = await get_statistics(hass, parse_csv_date_str(csv_data[0][START_TIME_KEY]))
    assert len(stats) == 1
    assert len(stats[STATISTIC_ID]) == 23

    assert parse_value_to_decimal(stats[STATISTIC_ID][-1]["sum"]) == get_csv_data_sum(
        csv_data
    )


async def test_import_service_with_invalid_lenght_data(hass):
    """Test import service with invalid lenght data."""

    with pytest.raises(HomeAssistantError) as err:
        await prepare_and_call_import_service_mocked(hass, DATA_WITH_INVALID_LENGTH)
    assert err


async def test_import_service_with_invalid_order_data(hass):
    """Test import service with invalid order data."""

    with pytest.raises(HomeAssistantError) as err:
        await prepare_and_call_import_service_mocked(hass, DATA_WITH_INVALID_ORDER)
    assert err


async def test_import_service_with_invalid_hour_block_prefix(hass):
    """Test import service with invalid hour block prefix."""

    with pytest.raises(HomeAssistantError) as err:
        await prepare_and_call_import_service_mocked(hass, DATA_WITH_INVALID_PREFIX)
    assert err


def test_invalid_hour_block_length():
    """Test hour block validation with invalid length."""

    assert not validate_hour_block(DATA_WITH_INVALID_LENGTH)
