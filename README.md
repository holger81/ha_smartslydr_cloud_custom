# LycheeThings SmartSlydr Cloud -- Custom Integration

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

_Integration to integrate with [integration_blueprint][integration_blueprint]._

**This integration will set up the following platforms.**

Platform | Description
-- | --
`cover` | Every window opener will be represented as one individual cover. 0 is closed, 100% is open.

## Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
1. If you do not have a `custom_components` directory (folder) there, you need to create it.
1. In the `custom_components` directory (folder) create a new folder called `integration_blueprint`.
1. Download _all_ the files from the `custom_components/integration_blueprint/` directory (folder) in this repository.
1. Place the files you downloaded in the new directory (folder) you created.
1. Restart Home Assistant
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Integration blueprint"

## Configuration is done in the UI

<!---->

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

***

[integration_blueprint]: https://github.com/holger81/ha_smartslydr_cloud_custom
[commits-shield]: https://img.shields.io/github/commit-activity/y/holger81/ha_smartslydr_cloud_custom.svg?style=for-the-badge
[commits]: https://github.com/holger81/ha_smartslydr_cloud_custom/commits/main
[exampleimg]: example.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/ludeeus/integration_blueprint.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/holger81/ha_smartslydr_cloud_custom.svg?style=for-the-badge
[releases]: https://github.com/holger81/ha_smartslydr_cloud_custom/releases
