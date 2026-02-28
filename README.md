# LycheeThings SmartSlydr Cloud -- Custom Integration

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

_Integration to integrate [Lycheethings SmartSlydr][lycheethings_smartslydr] devices with HomeAssistant._

**This integration will set up the following platforms.**

Platform | Description
-- | --
`cover` | Every window opener will be represented as one individual cover. 0 is closed, 100% is open.

## Installation

### Pre-installation steps
1. Navigate to https://my.home-assistant.io/ and make sure the Home Assistant Instance
   is configured correctly to point to your local Home Assistant instance.
2. Power on all your SmartSlydr devices.
3. Turn **OFF** the wifi on your phone and make sure all the appliances are operational in the LycheeThings mobile app.

### Installation
1. The easiest way to install the integration is using HACS. Just click the
   button below and follow the instructions:
   [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=holger81&repository=ha_smartslydr_cloud_custom)
   Alternatively, go to Settings -> Devices & Services in Home Assistant and click the "Add Integration" button. Search for "SmartSlydr" and install it.
2. Next you will be asked to provide the LycheeThings app credentials you
   created earlier.
3. Congratulations, you're done!
   SmartSlydr Cloud will now start downloading the data for your
   SmartSlydr devices and will add the entities for them to Home Assistant.
   Note that the integration dynamically discovers entities as they are made available by the API, so expect new entities to be added in the first few uses of the appliances.


## Configuration is done in the UI

<!---->

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

## Thank you!

This integration was only possible because of the great work done by Jay Basen (https://github.com/jbasen/Crestron-SmartSlydr).

***

[lycheethings_smartslydr]: https://lycheethings.com
[commits-shield]: https://img.shields.io/github/commit-activity/y/holger81/ha_smartslydr_cloud_custom.svg?style=for-the-badge
[commits]: https://github.com/holger81/ha_smartslydr_cloud_custom/commits/main
[exampleimg]: example.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/holger81/ha_smartslydr_cloud_custom.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/holger81/ha_smartslydr_cloud_custom.svg?style=for-the-badge
[releases]: https://github.com/holger81/ha_smartslydr_cloud_custom/releases
