
[![License](https://img.shields.io/github/license/ryanwinter/hass-rainforest-emu-2.svg?style=flat-square)](https://github.com/ryanwinter/hass-rainforest-emu-2/blob/main/LICENSE)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)

[![Blog](https://img.shields.io/badge/blog-Ryan%20Winter-orange?style=flat-square)](https://ryanwinter.org)

[![HACS Action](https://github.com/ryanwinter/hass-rainforest-emu-2/actions/workflows/hacs.yml/badge.svg)](https://github.com/ryanwinter/hass-rainforest-emu-2/actions/workflows/hacs.yml)
[![Validate with hassfest](https://github.com/ryanwinter/hass-rainforest-emu-2/actions/workflows/hassfest.yml/badge.svg)](https://github.com/ryanwinter/hass-rainforest-emu-2/actions/workflows/hassfest.yml)

# Rainforest EMU-2

> [!CAUTION]
> This device is now available via the [Rainfoest RAVEn](https://www.home-assistant.io/integrations/rainforest_raven) integration in Home Assistant.

Integrate the [Rainforest EMU-2](https://www.rainforestautomation.com/rfa-z105-2-emu-2-2) into the Home Assistant Energy Dashboard.

# Installation

1. Install [HACS](https://hacs.xyz)
1. Through the HACS integration, search for and install "Rainforest EMU-2"
1. Choose from one of the detected serial ports, or enter a host name and TCP port number when using a USB>TCP adapter to remotely locate your EMU-2 device

# Configuration

1. Select ```Configure | Dashboards | Energy``` to enter configuration mode
1. Choose ```ADD CONSUMPTION```
1. For ```Consumed Energy (kWh)``` select the Rainforest ```Summation Delivered``` sensor
1. Under cost, select the entity option and choose the Rainforest ```Current Price``` sensor
    > This option depends on the device containing the pricing information. Chose one of the other options if the device is not loaded with pricing information.
1. If you have solar, then repeat steps 2-4 for the ```Summation Received``` sensor
1. Select ```SAVE```

# Result

![Dashboard](https://raw.githubusercontent.com/ryanwinter/hass-rainforest-emu-2/main/images/dashboard.png)
