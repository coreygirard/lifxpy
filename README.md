# LIFXrary


```python
closet.on()
closet.on(duration=5.0)
closet.off()
closet.toggle()
closet.toggle(duration=2.0)
closet.setPower('on')
closet.setColor('green')
closet.setState(brightness=0.5,color='green')
closet.setColor(brightness=0.5,rgb=[0,100,100])
closet.setBrightness(0.5)
closet.setInfrared(0.2)
closet.setState(color='blue',brightness=0.5)
closet.stateDelta(hue=-15,saturation=0.1)
closet.breatheEffect(color='red',from_color='blue')
closet.pulseEffect(color='red',from_color='blue',period=0.5)
closet.cycle(states={'states':[{'color':'red'},{'color':'blue'}],'defaults':{'power':'on'}})
```
```python
s = State(token)

bedroom = s.filter(lambda bulb : 'bedroom' in bulb.label)
closet = s.filter(lambda bulb : 'closet' in bulb.label)
colorCapable = s.filter(lambda bulb : bulb.product.capabilities.has_color)

```

