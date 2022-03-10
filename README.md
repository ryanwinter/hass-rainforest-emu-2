
[![License](https://img.shields.io/github/license/ryanwinter/hass-rainforest-emu-2.svg?style=flat-square)](https://github.com/ryanwinter/hass-rainforest-emu-2/blob/main/LICENSE)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)

[![Blog](https://img.shields.io/badge/blog-Ryan%20Winter-orange?style=flat-square)](https://ryanwinter.org)

[![HACS Action](https://github.com/ryanwinter/hass-rainforest-emu-2/actions/workflows/hacs.yml/badge.svg)](https://github.com/ryanwinter/hass-rainforest-emu-2/actions/workflows/hacs.yml)
[![Validate with hassfest](https://github.com/ryanwinter/hass-rainforest-emu-2/actions/workflows/hassfest.yml/badge.svg)](https://github.com/ryanwinter/hass-rainforest-emu-2/actions/workflows/hassfest.yml)

# Rainforest EMU-2

Integrate the [Rainforest EMU-2](https://www.rainforestautomation.com/rfa-z105-2-emu-2-2) into the Home Assistant Energy Dashboard.

# Installation

1. Install [HACS](https://hacs.xyz)
1. Through the HACS integration, search for and install "Rainforest EMU-2"
1. Choose from one of the detected serial ports

# Configuration

1. Select ```Configure | Dashboards | Energy``` to enter configuration mode
1. Choose ```ADD CONSUMPTION```
1. For ```Consumed Energy (kWh)``` select the Rainforest ```Current Perdiod Usage``` sensor
1. Under cost, select the entity option and choose the Rainforest ```Current Price``` sensor
    > This option depends on the device containing the pricing information. Chose one of the other options if the device is not loaded with pricing information.
1. Select ```SAVE```

# Result

![Dashboard](https://raw.githubusercontent.com/ryanwinter/hass-rainforest-emu-2/main/images/dashboard.png)
