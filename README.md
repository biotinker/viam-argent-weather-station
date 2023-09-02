# viam-argent-weather-station
A viam module providing the Argent amenometer and rain gauge as a sensor. Specifically, if you buy one of these: https://www.argentdata.com/catalog/product_info.php?products_id=145 and want to run it on Viam as a sensor.

This module provides a sensor whose Readings are three self-explanatory fields:
 - rain_amt_inches
 - wind_dir_degrees
 - wind_mph

If you want metric, that option will come in a future release.

# Wiring

The rain gauge is wired as a digital interrupt. One wire connects to ground on your board, the other to a GPIO pin configured as a digital interrupt of type "basic". This interrupt *MUST* be named `"rain_gauge"`. The ability to specify your preferred name is coming in release 1.0.0.

The amenometer's wind direction is wired as an analog. Connect the *red* wire to ground, and the green wire to an analog input. The software will read the analog value coming off the weathervane and attempt to determine the wind direction via a lookup table. This may be buggy. Recommend using 50 samples per sec, averaged over 500ms. This analog *MUST* be named "wind_dir"

The amenometer's wind speed is tricky. The yellow wire must be split and have two wires which connect to two pins, one of which must be named "amenometer_count" and be a digital interrupt of tpye "basic", and the other must be named "amenometer" abd be a digital interrupt of type "servo". The reason for this is that we need to be able to measure both whether the tick count is increasing (and thus the wind blowing), but also, the period of time between the ticks.

# Configuration

This module is available via Viam's module registry.

To configure the module, simply add the module to your robot, and add the following to your config:
```
    {
      "model": "biotinker:sensor:argent",
      "type": "sensor",
      "attributes": {
        "board": "pi"
      },
      "depends_on": [
        "pi"
      ],
      "name": "weather"
    }
```

Note that "pi" is an example name for a board, replace that with whatever the name of your board is.
