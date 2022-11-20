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

### HACS (Custom Repository)

1. Navigate to `HACS` on your Home-Assistant dashboard.
2. Select `Integrations`.
3. Click on the menu in the top right corner and choose `Custom Repositories`.
4. Insert `https://github.com/DarkC35/ha_linznetz` for repository and select category `integration`.
5. Search for `LINZ NETZ` in the integration tab.
6. Click on the integration and install it with the button on the bottom right corner.
7. Restart Home-Assistant as prompted.
8. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "LINZ NETZ".


### Manual

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `linznetz`.
4. Download _all_ the files from the `custom_components/linznetz/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant.
7. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "LINZ NETZ".

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

## Configurations with the UI

**To use this integration you need a free account at https://www.linznetz.at and enable the quater-hour(QH) analysis ("Viertelstundenauswertung"). Then it will take 1-2 days until your SmartMeter transfers the QH data to LINZ NETZ.** Please make sure you have a LINZ NETZ account since *LINZ AG Plus24* does not support QH E-Mail reports! (You can have both accounts if you want to.) You can check on the LINZ NETZ services page > "Verbrauchsdateninformation"/"Verbräuche anzeigen" if your SmartMeter supports QH analysis and if your data is already transmitted to LINZ NETZ.

During the configuration insert the 33 characters long "meter point number" ("Zählerpunktnummer") you can find on https://www.linznetz.at > "Meine Verbräuche" > "Verbräuche anzeigen". This number is used as the unique ID. If you don't want to use your real number just use `AT0000000000000000000000000000000` but please make sure you need another number if you need a second instance of this integration! The second configuration value `name` is optinal, you can use it to identify different SmartMeters, the default name is "SmartMeter".

This will create a `sensor.smartmeter_energy` entity which you can use to import the QH reports to. To import your QH reports use the `linznetz.import_report` service.

After the import you can use the `sensor.smartmeter_energy` entity on the energy dashboard as a "grid consumption".

### TODOs
* Describe `linznetz.import_report` service.
* Add tests.
* Add screenshots.

## Example automation for daily inserts

This example uses [emcniece/ha_imap_attachment](https://github.com/emcniece/ha_imap_attachment/) to download the attachments. You can install this component manually or as an HACS custom repository.

0. Optional: Before setting up the daily automation you can bulk import all your available previous QH values. Download them from linznetz.at as a csv file, copy this file to your HA installation and all the `linznetz.import_report` service from the HA developer tools page. This integrations tries to re-calculate and update the statistics when missing values are inserted afterwards but it's safer to insert them chronologically.
1. Install `ha_imap_attachment` and follow the steps to create a new folder for the attachments on your HA installation (we use `/config/attachments` here).
2. Lookup the IMAP configurations for your mail provider (example below uses Outlook). For Gmail you will have to set an App Password on your Google account and enable Multi-Factor Authentication (see [core IMAP docs](https://www.home-assistant.io/integrations/imap/#gmail-with-app-password)).
3. Optional: Login to your mail provider and create a new folder for the LINZ NETZ reports, e.g. `VDI`. If you don't want to use a new folder you have to use the folder `INBOX` in your configuration but it will be difficult to filter this way.
4. **IMPORTANT**: Since the reports are sent with SMIME encryption `ha_imap_attachment` downloads the encrypted mail instead of the attachments. To solve this problem you have to configure some rules for your inbox as a workaround: The easiest way is to forward the daily reports to yourself (or another mail address), this will remove the encryption (tested with Outlook.com). Example rules:
```
1. Mails with tiles containing "Tagesbericht Viertelstundenverbrauch" from "vdi@linznetz.at" forward to <my mail address> and delete original mail.
2. Mails with titles containing "Tagesbericht Viertelstundenverbrauch" from <my mail address> move to folder "VDI".
```
5. Add the configs from the `configuration.yaml` example below to your configurations.
6. Restart Home-Assistant. You can test the configuration with forwarding a daily report to yourself. You should see a `sensor.linz_netz_attachments` (based on the sensor name in the configuration) entity with the path to a csv file now (this can take some minutes).
7. Create an automation like the `automation-example.yaml` below (as a file or with the UI; you can copy-paste this as-is).

### configuration.yaml

```yaml
homeassistant:
  allowlist_external_dirs:
    - "/config/attachments"

sensor:
  - platform: imap_attachment
    name: LINZ NETZ Attachments
    server: outlook.office365.com
    port: 993
    folder: VDI
    senders:
        - !secret outlook_mail
    username: !secret outlook_mail
    password: !secret outlook_password
    storage_path: /config/attachments
    value_template: "{{ ( attachment_paths | select('search', '.csv')) | first | default('unavailable') }}"
```

### automation-example.yaml
```yaml
alias: Import Linz Netz Email Reports
description: ""
trigger:
  - platform: state
    entity_id:
      - sensor.linz_netz_attachments
condition:
  - condition: not
    conditions:
      - condition: state
        entity_id: sensor.linz_netz_attachments
        state: unknown
      - condition: state
        entity_id: sensor.linz_netz_attachments
        state: unavailable
action:
  - service: linznetz.import_report
    data:
      entity_id: sensor.smartmeter_energy
      path: "{{ states('sensor.linz_netz_attachments') }}"
mode: single
```

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
