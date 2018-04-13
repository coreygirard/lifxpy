# lifx.py

A library to communicate with LIFX smart bulbs. Main claim to fame is dynamic views based on current state.

## Usage

### Authentication

To get started, create a `State` object:

```python
import lifxpy

lifx = lifxpy.State(token)
```

`token` is a string containing either your [LIFX API token](https://api.developer.lifx.com)

```python
'ABC...DEF'
```

or the path to a JSON file containing your token in the following format:

```json
{"token": "ABC...DEF"}
```

### Bulbs

**lifx.py** takes a slightly unusual stance in that all 'objects' are actually dynamic views into the current state. Let's see a concrete example of what this means:

```python
import lifxpy
lifx = lifxpy.State(token)

kitchen = lifx.filter(lambda bulb : bulb.label == 'kitchen')
kitchen.toggle()
```

So what's happening here? At the basic level, we're initializing `kitchen` to an object that controls a bulb with a `label` equal to `'kitchen'`, and then we're toggling that bulb. What's actually happening under the hood is that we're creating a dynamic search for the label `kitchen` across all bulbs, and later we're toggling all bulbs which fit that description. An example that should help clarify the distinction:


```python
lifx = lifxpy.State(token)

kitchen = lifx.filter(lambda bulb : bulb.label == 'kitchen')
currentlyDim = lifx.filter(lambda bulb : bulb.brightness < 0.5)

print("'currentlyDim': {0}".format(currentlyDim))

kitchen.setBrightness(0.25)

print("'currentlyDim': {0}".format(currentlyDim))
```

```
'currentlyDim': []

# set brightness of label:kitchen bulb to 0.25

'currentlyDim': [Bulb(label:kitchen, id:0123456789)]
```

Why do things this way? Because it greatly simplifies doing certain operations to all bulbs that meet certain criteria:

- Turn off all bulbs whose brightness is below 0.5:

```python
dim = lifx.filter(lambda bulb : bulb.brightness < 0.5)
dim.off()
```

- Turn down brightness of all red bulbs by 0.25:

```python
red = lifx.filter(lambda bulb : bulb.color == 'red')
red.state_delta(brightness=-0.25
```

- Shift color of all lit bulbs:

```python
lit = lifx.filter(lambda bulb : bulb.power == 'on')
lit.state_delta(hue=+30)
```

- Turn on all lights labelled `kitchen_*` or `dining_*`:

```python
def f(bulb):
    if bulb.label.startswith('kitchen_'): return True
    if bulb.label.startswith('dining_'): return True
    return False

livingAndDining = lifx.filter(f)
livingAndDining.on()
```

- Get a list of all lights that might be physically unpowered:

```python
unpowered = lifx.filter(lambda bulb : bulb.seconds_since_seen > 10.0)
```

For a full list of available member functions and arguments, see the [reference](reference.md)

The library also offers two simple helper functions:

- `.get_bulb_by_label(label)` is equivalent to `.filter(lambda bulb : bulb.label == label)`

- `.get_bulb_by_id(i)` is equivalent to `.filter(lambda bulb : bulb.id == i)`

The earlier example could also be written:


```python
import lifxpy
lifx = lifxpy.State(token)

kitchen = lifx.get_bulb_by_label('kitchen')
kitchen.toggle()
```




---
---
---

Disallow non-keyword arguments for functions that take more than one argument:

```python
    def set_state(self, *args, **kwargs):
        if args:
            raise TypeError("'set_state' doesn't accept non-keyword arguments")

        brightness = kwargs.get('brightness', None)
        color = kwargs.get('color', None)

        # do stuff
```

Figure out how to do reliable color comparisons. For example:

```python
red = lifx.filter(lambda bulb : bulb.color == 'red')
```

Potentially allow 'freezing` a dynamic view, which would just return a new dynamic view that searches for whatever ids were in the dynamic search at the time

Maybe allow set operations between views. Example:

```python

a | b # all lights that are in a or b

a & b # all lights that are in a and b

a - b # all lights that are in a and not in b

b - a # all lights that are in b and not in a

```

---
---
---

```python
state = lifx.State(token)

kitchen = state.filter(lambda bulb : bulb.label == 'kitchen')
currentlyDim = state.filter(lambda bulb : bulb.brightness < 0.5)

print("'{0}' brightness: {1}".format(kitchen[0].label, kitchen[0].brightness))
print("'{0}' color: {1}".format(kitchen[0].label, kitchen[0].color))

currentlyDim.set_color('blue')

print("'{0}' brightness: {1}".format(kitchen[0].label, kitchen[0].brightness))
print("'{0}' color: {1}".format(kitchen[0].label, kitchen[0].color))

kitchen.set_brightness(0.25)

print("'{0}' brightness: {1}".format(kitchen[0].label, kitchen[0].brightness))
print("'{0}' color: {1}".format(kitchen[0].label, kitchen[0].color))

currentlyDim.set_color('blue')

print("'{0}' brightness: {1}".format(kitchen[0].label, kitchen[0].brightness))
print("'{0}' color: {1}".format(kitchen[0].label, kitchen[0].color))
```

```
'kitchen' brightness: 1.0
'kitchen' color: 'white' # figure out proper format

'kitchen' brightness: 1.0
'kitchen' color: 'white' # figure out proper format

'kitchen' brightness: 0.25
'kitchen' color: 'white' # figure out proper format

'kitchen' brightness: 0.25
'kitchen' color: 'blue' # figure out proper format
```


```python
s = State(token)

bedroom = s.filter(lambda bulb : 'bedroom' in bulb.label)
closet = s.filter(lambda bulb : 'closet' in bulb.label)
colorCapable = s.filter(lambda bulb : bulb.product.capabilities.has_color)

```

```python

state = State(token, alwaysRefresh=False)
bedroom = state.lights.filter(lambda bulb : 'bedroom' in bulb.label)
closet = state.lights.filter(lambda bulb : 'closet' in bulb.label)
bedroom.toggle()

assert('corey_bedroom' in bedroom)
assert('corey_bedroom' not in closet)
assert('corey_closet' not in bedroom)
assert('corey_closet' in closet)

assert('d073d512e980' in bedroom)
assert('d073d512e980' not in closet)
assert('d073d510ae5b' not in bedroom)
assert('d073d510ae5b' in closet)


blue = state.scenes.filter(lambda scene : scene.name == 'Blue')

blue.activate()




print(state.list_lights())

assert('Red' in state.scenes)




```
