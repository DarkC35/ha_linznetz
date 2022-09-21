# LINZ NETZ Importer for Home-Assistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]

_Component to integrate with [ha_linznetz][ha_linznetz]._

**This component will set up the following platforms.**

Platform | Description
-- | --
`sensor` | Placeholder to import statistics by the service.

## Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `linznetz`.
4. Download _all_ the files from the `custom_components/linznetz/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant
7. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "LINZ NETZ"

Using your HA configuration directory (folder) as a starting point you should now also have this:

```text
custom_components/linznetz/translations/en.json
custom_components/linznetz/__init__.py
custom_components/linznetz/config_flow.py
custom_components/linznetz/const.py
custom_components/linznetz/manifest.json
custom_components/linznetz/sensor.py
custom_components/linznetz/services.yaml
```

## Configuration is done in the UI

**To use this integration you need a free account at https://www.linznetz.at and enable the quater-hour(QH) analysis ("Viertelstundenauswertung"). Then it will take 1-2 days until your SmartMeter transfers the QH data to LINZ NETZ.** Please make sure you have a LINZ NETZ account since *LINZ AG Plus24* does not support QH E-Mail reports! (You can have both accounts if you want to.) You can check on the LINZ NETZ services page > "Verbrauchsdateninformation"/"Verbräuche anzeigen" if your SmartMeter supports QH analysis and if your data is already transmitted to LINZ NETZ.

During the configuration insert the 33 characters long "meter point number" ("Zählerpunktnummer") you can find on https://www.linznetz.at > "Meine Verbräuche" > "Verbräuche anzeigen". This number is used as the unique ID. If you don't want to use your real number just use `AT0000000000000000000000000000000` but please make sure you need another number if you need a second instance of this integration! The second configuration value `name` is optinal, you can use it to identify different SmartMeters, the default name is "SmartMeter".

This will create a `sensor.smartmeter_energy` entity which you can use to import the QH reports to. To import your QH reports use the `linznetz.import_report` service.

After the import you can use the `sensor.smartmeter_energy` entity on the energy dashboard as a "grid consumption".

### TODOs
* Describe `linznetz.import_report` service.
* Add tests.
* Add example automation to import reports.
* Add screenshots.

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

## Credits

This project uses the [integration_blueprint](https://github.com/custom-components/integration_blueprint) template and is inspired by the usage of the `async_add_external_statistics` recorder function that is used by the [tibber](https://github.com/home-assistant/core/tree/dev/homeassistant/components/tibber) integration.

***

[ha_linznetz]: https://github.com/DarkC35/ha_linznetz
[commits-shield]: https://img.shields.io/github/commit-activity/y/DarkC35/ha_linznetz.svg?style=for-the-badge
[commits]: https://github.com/DarkC35/ha_linznetz/commits/master
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/DarkC35/ha_linznetz.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-DarkC35-red.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/DarkC35/ha_linznetz.svg?style=for-the-badge
[releases]: https://github.com/DarkC35/ha_linznetz/releases
