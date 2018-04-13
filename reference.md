# Reference

## Properties

For further information, see the [LIFX API](https://api.developer.lifx.com/docs/colors), especially on [colors](https://api.developer.lifx.com/docs/colors) and [states](https://api.developer.lifx.com/docs/set-state)

### power

Desired power state of bulb

- type: `string`
- acceptable values: `'on'`, `'off'`

### duration

Desired time for operation to take, in seconds

- type: `float`
- acceptable range: `0.0` (instantaneous) to `3155760000.0` (100 years)
- default value: `1.0`

### color

Description of color in English

- type: `string`
- acceptable values: `white`, `red`, `orange`, `yellow`, `cyan`, `green`, `blue`, `purple`, `pink`

### hue

- type: `int`
- acceptable range: `0` to `360`

### saturation

- type: `float`
- acceptable range: `0.0` to `1.0`

### brightness

- type: `float`
- acceptable range: `0.0` to `1.0`

### kelvin

- type: `int`
- acceptable range: `1500` to `9000`

### rgb (hex)

- type: `string`
- acceptable range: `#000000` to `#ffffff`
- examples: `#ff0000`, `#123ABC`, `00ff00`, `0000FF`

### rgb (int)

- type: `list`/`tuple` of `int`
- acceptable range: `[0, 0, 0]` to `[255, 255, 255]`
- example: `[0, 255, 0]`

### infrared

- type: `float`
- acceptable range: `0.0` to `1.0`



## Methods

### on

`.on([duration])`

Examples:

- `lights.on()`
- `lights.on(duration=5.0)`

### off

`.off([duration])`

Examples:

- `lights.off()`
- `lights.off(duration=5.0)`

### toggle

`.toggle([duration])`

Examples:

- `lights.toggle()`
- `lights.toggle(duration=5.0)`

### set_power

`.set_power(power[, duration])`

Examples:

- `lights.set_power('on')`
- `lights.set_power('off', duration=5.0)`

### set_color

`.set_color([color][, duration])`

This is provided mostly as a helper method to simplify color setting. `.set_color('blue')` is exactly equivalent to `.set_state(color='blue')`

Examples:

- `lights.set_color('blue')`
- `lights.set_color('blue', duration=3.0)`


### set_state

`.set_state([power][, color][, hue][, saturation][, brightness][, kelvin][, rgb][, duration])`

Examples:

- `lights.set_state(color='blue')`
- `lights.set_state(color='red', duration=2.0)`
- `lights.set_state(hue=240, saturation=0.5)`
- `lights.set_state(brightness=0.5, rgb=[255, 0, 0])`

### set_brightness

`.set_brightness(brightness)`

Examples

- `lights.set_brightness(1.0)`

### set_infrared

`.set_infrared(infrared)`

`.set_infrared(i)` is exactly equivalent to `.set_state(infrared=i)`

Examples

- `lights.set_infrared(0.2)`


### state_delta

`.state_delta([power][, duration][, infrared][, hue][, saturation][, brightness][, kelvin])`



`.state_delta(hue=-15, saturation=0.1)`

### breathe_effect


`.breathe_effect(color='red', from_color='blue')`

### pulse_effect

`.pulse_effect(color='red', from_color='blue', period=0.5)`

### cycle

`.cycle(states={'states':[{'color':'red'}, {'color':'blue'}], 'defaults':{'power':'on'}})`
