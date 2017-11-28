from pprint import pprint
import time
import json
import requests



class Bulb(object):
    pass

def setBulbData(bulb,data):
    for k,v in data.items():
        setattr(bulb,k,v)
        if type(v) == type(dict()):
            setattr(bulb,k,Bulb())

            setBulbData(getattr(bulb,k),v)


def buildBulb(data):
    bulb = Bulb()
    setBulbData(bulb,data)
    return bulb


class Method(object):
    def __init__(self,ptr):
        self.ptr = ptr

    def __call__(self,*args,**kwargs):
        self.ptr(kwargs)

class MethodSpecific(object):
    def __init__(self,ptr,keyword):
        self.ptr = ptr
        self.keyword = keyword

    def __call__(self,*args):
        self.ptr({self.keyword:args[0]})

class MethodPrewritten(object):
    def __init__(self,ptr,payload):
        self.ptr = ptr
        self.payload = payload

    def __call__(self):
        self.ptr(self.payload)

class View(object):
    def __init__(self,parent,query):
        self.parent = parent
        self.query = query

        self.cmd = {
                    'off':           MethodPrewritten(self.handleSetState,{'power':'off'}),
                    'on':            MethodPrewritten(self.handleSetState,{'power':'on'}),
                    'toggle':        Method(self.handleToggle),
                    'setState':      Method(self.handleSetState),
                    'setPower':      MethodSpecific(self.handleSetState,'power'),
                    'setColor':      MethodSpecific(self.handleSetState,'color'),
                    'setBrightness': MethodSpecific(self.handleSetState,'brightness'),
                    'setInfrared':   MethodSpecific(self.handleSetState,'infrared'),
                    'pulseEffect':   Method(self.handlePulseEffect),
                    }

    def handleOff(self):
        self.parent.operation(self.query,'off')

    def handleOn(self):
        self.parent.operation(self.query,'on')

    def handleToggle(self):
        self.parent.operation(self.query,'toggle')

    def handleSetState(self,kwargs):
        self.parent.operation(self.query,'setState',kwargs)

    def handlePulseEffect(self,kwargs):
        self.parent.operation(self.query,'pulseEffect',kwargs)

    def __getattr__(self,e):
        if e in self.cmd.keys():
            return self.cmd[e]

    def __repr__(self):
        contents = ','.join(['label:'+bulb.label for bulb in self.parent.filteredLights(self.query)])
        return 'View({0})'.format(contents)

class State(object):
    def __init__(self,token):
        self.headers = {'Authorization': 'Bearer ' + token}
        self.backoff = [1,1,1,1,1,2,4,8,16,32]

    def filter(self,query):
        return View(self,query)

    def setBackoff(self,backoff):
        assert(type(backoff) == type([]))
        self.backoff = backoff

    def listLights(self):
        resp = requests.get('https://api.lifx.com/v1/lights/all',headers=self.headers)
        return [buildBulb(e) for e in resp.json()]

    def filteredLights(self,query):
        return [bulb for bulb in self.listLights() if query(bulb)]

    def operation(self,query,op,kwargs={}):
        idMatch = ['id:'+bulb.id for bulb in self.filteredLights(query)]
        selector = ','.join(idMatch)

        if op == 'on':
            self.on(selector)
        elif op == 'off':
            self.off(selector)
        elif op == 'toggle':
            self.toggle(selector)
        elif op == 'setState':
            self.setState(selector,kwargs)
        elif op == 'pulseEffect':
            self.pulseEffect(selector,kwargs)


    def on(self,selector):
        print(('on',selector))
        '''
        resp = requests.put('https://api.lifx.com/v1/lights/{0}/state'.format(selector),
                             data={'power':'on'},
                             headers=self.headers)
        '''

    def off(self,selector):
        print(('off',selector))
        '''
        resp = requests.put('https://api.lifx.com/v1/lights/{0}/state'.format(selector),
                             data={'power':'off'},
                             headers=self.headers)
        '''

    def toggle(self,selector):
        print(('toggle',selector))
        '''
        resp = requests.post('https://api.lifx.com/v1/lights/{0}/toggle'.format(selector),
                              headers=self.headers)
        '''

    def setState(self,selector,kwargs):
        print(('setState',selector,kwargs))
        '''
        resp = requests.put('https://api.lifx.com/v1/lights/{0}/state'.format(selector),
                             data={'power':'off'},
                             headers=self.headers)
        '''

    def pulseEffect(self,selector,data):
        print(('pulseEffect',selector,data))
        '''
        resp = requests.post('https://api.lifx.com/v1/lights/{0}/effects/pulse'.format(selector),
                              data=data,
                              headers=self.headers)
        '''

token = 'c917678ee3fdeee1f81332a7aa01560f93831c50d9d5ef4feb81107563d1de91'

s = State(token)

bedroom = s.filter(lambda bulb : 'bedroom' in bulb.label)
closet = s.filter(lambda bulb : 'closet' in bulb.label)


colorCapable = s.filter(lambda bulb : bulb.product.capabilities.has_color)


#closet.pulseEffect(color='red',from_color='blue')

#scenes = s.getScenes()

closet.on()
















