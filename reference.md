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
- acceptable range: `[0,0,0]` to `[255,255,255]`
- example: `[0,255,0]`

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

### setPower

`.setPower(power[,duration])`

Examples: 

- `lights.setPower('on')`
- `lights.setPower('off',duration=5.0)`

### setColor

`.setColor([color][,duration])`

This is provided mostly as a helper method to simplify color setting. `.setColor('blue')` is exactly equivalent to `.setState(color='blue')`

Examples: 

- `lights.setColor('blue')`
- `lights.setColor('blue',duration=3.0)`


### setState

`.setState([power][,color][,hue][,saturation][,brightness][,kelvin][,rgb][,duration])`

Examples:

- `lights.setState(color='blue')`
- `lights.setState(color='red',duration=2.0)`
- `lights.setState(hue=240,saturation=0.5)`
- `lights.setState(brightness=0.5,rgb=[255,0,0])`

### setBrightness

`.setBrightness(brightness)`

Examples

- `lights.setBrightness(1.0)`

### setInfrared

`.setInfrared(infrared)`

`.setInfrared(i)` is exactly equivalent to `.setState(infrared=i)`

Examples

- `lights.setInfrared(0.2)`


### stateDelta

`.stateDelta([power][,duration][,infrared][,hue][,saturation][,brightness][,kelvin])`



`.stateDelta(hue=-15,saturation=0.1)`

### breatheEffect


`.breatheEffect(color='red',from_color='blue')`

### pulseEffect

`.pulseEffect(color='red',from_color='blue',period=0.5)`

### cycle

`.cycle(states={'states':[{'color':'red'},{'color':'blue'}],'defaults':{'power':'on'}})`
