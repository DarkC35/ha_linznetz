"""Sensor platform for linznetz."""

import csv
from datetime import datetime, timedelta
from decimal import Decimal
import logging
import os
import voluptuous as vol

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import StatisticData, StatisticMetaData
from homeassistant.components.recorder.statistics import (
    get_last_statistics,
    async_import_statistics,
    statistics_during_period,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ENERGY_KILO_WATT_HOUR
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util import dt as dt_util

from .const import (
    CONF_METER_POINT_NUMBER,
    CONF_NAME,
    DEFAULT_NAME,
    DOMAIN,
    SERVICE_IMPORT_REPORT,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_entry(
    _hass: HomeAssistant, config_entry: ConfigEntry, async_add_devices
):
    """Setup sensor platform."""

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_IMPORT_REPORT,
        {
            vol.Required("path"): str,
        },
        LinzNetzSensor.import_report.__name__,
    )

    async_add_devices([LinzNetzSensor(config_entry)])


class LinzNetzSensor(SensorEntity):
    """linznetz Sensor class."""

    def __init__(self, config_entry: ConfigEntry):
        """Initialize the sensor."""
        self.config_entry = config_entry
        _unique_id = config_entry.data[CONF_METER_POINT_NUMBER]
        _name = config_entry.data.get(CONF_NAME, DEFAULT_NAME)
        self._attr_name = f"{_name} Energy"

        self._attr_native_unit_of_measurement = ENERGY_KILO_WATT_HOUR
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL
        self._attr_should_poll = False
        self._attr_icon = "mdi:transmission-tower-import"
        self._attr_available = True

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, _unique_id)}, name=_name
        )
        self._attr_unique_id = f"{_unique_id}_energy"

    async def import_report(self, path: str) -> None:
        """Service to import csv data from path."""
        _LOGGER.debug("Import Report executed with path: %s", path)
        _LOGGER.debug(
            "Entity: %s; Entity_ID: %s; Unique_ID: %s",
            self.name,
            self.entity_id,
            self.unique_id,
        )

        if not os.path.isfile(path):
            raise HomeAssistantError(f"Report file at path {path} not found.")

        with open(path, encoding="UTF-8") as file:
            _LOGGER.debug(file)
            # metadata for external stats
            # metadata = StatisticMetaData(
            #     unit_of_measurement=ENERGY_KILO_WATT_HOUR,
            #     state_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
            #     source=DOMAIN,
            #     name=self.name,
            #     statistic_id=self.statistic_id,
            #     has_mean=False,
            #     has_sum=True,
            # )
            # metadata for internal stats
            metadata = StatisticMetaData(
                unit_of_measurement=ENERGY_KILO_WATT_HOUR,
                # state_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
                source="recorder",
                name=self.name,
                statistic_id=self.entity_id,
                has_mean=False,
                has_sum=True,
            )
            statistics = []

            report_dict_reader = csv.DictReader(file, delimiter=";")
            csv_data = list(report_dict_reader)

            if len(csv_data) % 96 != 0:
                raise HomeAssistantError(
                    "Report to import should have exactly 96 quarter-hour entries per day."
                )

            last_inserted_stat = await get_instance(self.hass).async_add_executor_job(
                get_last_statistics, self.hass, 1, self.entity_id, True
            )
            inserted_stats = {self.entity_id: []}
            _LOGGER.debug("Last inserted stat:")
            _LOGGER.debug(last_inserted_stat)

            if (
                len(last_inserted_stat) == 0
                or len(last_inserted_stat[self.entity_id]) == 0
            ):
                _sum = Decimal(0)
                _LOGGER.debug("No previous inserted stats, start sum with 0.")
            elif (
                len(last_inserted_stat) == 1
                and len(last_inserted_stat[self.entity_id]) == 1
                and dt_util.parse_datetime(
                    last_inserted_stat[self.entity_id][0]["start"]
                )
                < datetime.strptime(csv_data[0]["Datum von"], "%d.%m.%Y %H:%M").replace(
                    tzinfo=dt_util.get_time_zone("Europe/Vienna")
                )
            ):
                _sum = Decimal(last_inserted_stat[self.entity_id][0]["sum"])
                _LOGGER.debug("Previous inserted stats found, start sum with %d.", _sum)
            else:
                inserted_stats = await get_instance(self.hass).async_add_executor_job(
                    statistics_during_period,
                    self.hass,
                    dt_util.as_utc(
                        datetime.strptime(
                            csv_data[0]["Datum von"], "%d.%m.%Y %H:%M"
                        ).replace(tzinfo=dt_util.get_time_zone("Europe/Vienna"))
                    )
                    - timedelta(hours=1),
                    None,
                    [self.entity_id],
                )
                _LOGGER.debug("Inserted stats:")
                _LOGGER.debug(inserted_stats)
                _sum = (
                    Decimal(inserted_stats[self.entity_id][0]["sum"])
                    if len(inserted_stats) > 0
                    and len(inserted_stats[self.entity_id]) > 0
                    and dt_util.parse_datetime(
                        inserted_stats[self.entity_id][0]["start"]
                    )
                    < datetime.strptime(
                        csv_data[0]["Datum von"], "%d.%m.%Y %H:%M"
                    ).replace(tzinfo=dt_util.get_time_zone("Europe/Vienna"))
                    else Decimal(0)
                )
                _LOGGER.debug("Overlap detected, start sum with %d.", _sum)

            hourly_sum = Decimal(0)
            start = None
            for index, record in enumerate(csv_data, start=1):
                hourly_sum += Decimal(record[list(record.keys())[2]].replace(",", "."))
                if index % 4 == 1:
                    start = datetime.strptime(
                        record["Datum von"], "%d.%m.%Y %H:%M"
                    ).replace(tzinfo=dt_util.get_time_zone("Europe/Vienna"))
                if index % 4 == 0:
                    _sum += hourly_sum
                    statistics.append(
                        StatisticData(
                            start=start,
                            state=hourly_sum,
                            sum=_sum,
                        )
                    )
                    hourly_sum = Decimal(0)
        for stat in inserted_stats[self.entity_id]:
            if dt_util.parse_datetime(stat["start"]) <= statistics[-1]["start"]:
                continue
            _sum += Decimal(stat["state"])
            statistics.append(
                StatisticData(
                    start=dt_util.parse_datetime(stat["start"]),
                    state=stat["state"],
                    sum=_sum,
                )
            )
        _LOGGER.debug(statistics)
        _LOGGER.debug(metadata)
        async_import_statistics(self.hass, metadata, statistics)
