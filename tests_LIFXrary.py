import unittest
import json
import LIFXrary


class TestLights(unittest.TestCase):
    def test_(self):

        def dummyFetchLights():
            resp = [
                      {
                        "id": "d3b2f2d97452",
                        "uuid": "8fa5f072-af97-44ed-ae54-e70fd7bd9d20",
                        "label": "Left Lamp",
                        "connected": True,
                        "power": "on",
                        "color": {
                          "hue": 250.0,
                          "saturation": 0.5,
                          "kelvin": 3500
                        },
                        "infrared": "1.0",
                        "brightness": 0.5,
                        "group": {
                          "id": "1c8de82b81f445e7cfaafae49b259c71",
                          "name": "Lounge"
                        },
                        "location": {
                          "id": "1d6fe8ef0fde4c6d77b0012dc736662c",
                          "name": "Home"
                        },
                        "last_seen": "2015-03-02T08:53:02.867+00:00",
                        "seconds_since_seen": 0.002869418,
                        "product": {
                          "name": "LIFX+ A19",
                          "company": "LIFX",
                          "identifier": "lifx_plus_a19",
                          "capabilities": {
                            "has_color": True,
                            "has_variable_color_temp": True,
                            "min_kelvin": 2500,
                            "max_kelvin": 9000,
                            "has_ir": True,
                            "has_multizone": False
                          }
                        }
                      }
                    ]
            return {e['id']:LIFXrary.Thing('Bulb',e) for e in resp}


        with open('tokens.json') as f:
            token = json.load(f)['lifx']


        state = LIFXrary.State(token,alwaysRefresh=False)
        state.handleRequest.fetchLights = dummyFetchLights
        state.refreshLights()

        data = state.lightsData
        self.assertEqual(data['d3b2f2d97452'].id,'d3b2f2d97452')
        self.assertEqual(data['d3b2f2d97452'].label,'Left Lamp')
        print(data)













if __name__ == '__main__':
    unittest.main()




