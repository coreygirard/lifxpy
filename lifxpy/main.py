from attrdict import AttrDict


class LightCallback(object):
    def __init__(self, attr, callback):
        self.attr = attr
        self.callback = callback

    def __eq__(self, other):
        return self.callback(self.attr, other)

class Light(object):
    def __getattr__(self, attr):
        return LightCallback(attr, self.set)

    def set(self, attr, value):
        return (attr, value)

light = Light()


class HTTP(object):
    def fetch_lights(self):
        resp = [{"id": "d3b2f2d97452",
                 "uuid": "8fa5f072-af97-44ed-ae54-e70fd7bd9d20",
                 "label": "Left Lamp",
                 "connected": True,
                 "power": "on",
                 "color": {"hue": 250.0,
                           "saturation": 0.5,
                           "kelvin": 3500},
                 "infrared": "1.0",
                 "brightness": 0.5,
                 "group": {"id": "1c8de82b81f445e7cfaafae49b259c71",
                           "name": "Lounge"},
                 "location": {"id": "1d6fe8ef0fde4c6d77b0012dc736662c",
                              "name": "Home"},
                 "last_seen": "2015-03-02T08:53:02.867+00:00",
                 "seconds_since_seen": 0.002869418,
                 "product": {"name": "LIFX+ A19",
                             "company": "LIFX",
                             "identifier": "lifx_plus_a19",
                             "capabilities": {"has_color": True,
                                              "has_variable_color_temp": True,
                                              "min_kelvin": 2500,
                                              "max_kelvin": 9000,
                                              "has_ir": True,
                                              "has_multizone": False}}}]

        return map(AttrDict, resp)


class View(object):
    def __init__(self, parent, query):
        self.parent = parent
        self.attr, self.value = query

    def __iter__(self):
        for i in self.parent:
            try:
                if getattr(i, self.attr) == self.value:
                    yield i
            except AttributeError:
                pass


class State(object):
    def __init__(self):
        self.http = HTTP()

    def filter(self, query):
        return View(self, query)

    def __iter__(self):
        for i in self.http.fetch_lights():
            yield i
