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
    def __init__(self,route,ptr):
        self.route = route
        self.ptr = ptr

    def __call__(self,*args,**kwargs):
        self.ptr(self.route,*args,**kwargs)

class MethodSpecific(object):
    def __init__(self,route,ptr,keyword):
        self.ptr = ptr
        self.keyword = keyword

    def __call__(self,*args):
        self.ptr({self.keyword:args[0]})

class MethodPrewritten(object):
    def __init__(self,route,ptr,payload):
        self.ptr = ptr
        self.payload = payload

    def __call__(self):
        self.ptr(self.payload)

class View(object):
    def __init__(self,parent,query):
        self.parent = parent
        self.query = query

        self.cmdList = ['off',
                        'on',
                        'toggle',
                        'setState',
                        'setPower',
                        'setColor',
                        'setBrightness',
                        'setInfrared',
                        'pulseEffect',
                        'stateDelta',
                        'breatheEffect',
                        'pulseEffect',
                        'cycle']

    def abstractRequest(self,*args,**kwargs):
        kwargs['query'] = self.query
        self.parent.abstractRequest(*args,**kwargs)

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
        if e in self.cmdList:
            return Method(e,self.abstractRequest)

        #if e in self.cmd.keys():
        #    return self.cmd[e]

    def __repr__(self):
        contents = ','.join(['label:'+bulb.label for bulb in self.parent.filteredLights(self.query)])
        return 'View({0})'.format(contents)

class State(object):
    def __init__(self,token):
        self.headers = {'Authorization': 'Bearer ' + token}
        self.backoff = [1,1,1,1,1,2,4,8,16,32]

        self.requestParams = {'toggle':        {'url':'https://api.lifx.com/v1/lights/{0}/toggle',
                                                'method':'post'},
                              'setState':      {'url':'https://api.lifx.com/v1/lights/{0}/state',
                                                'method':'post'},
                              'stateDelta':    {'url':'https://api.lifx.com/v1/lights/{0}/state/delta',
                                                'method':'post'},
                              'breatheEffect': {'url':'https://api.lifx.com/v1/lights/{0}/effects/breathe',
                                                'method':'post'},
                              'pulseEffect':   {'url':'https://api.lifx.com/v1/lights/{0}/effects/pulse',
                                                'method':'post'},
                              'cycle':         {'url':'https://api.lifx.com/v1/lights/{0}/cycle',
                                                'method':'post'}}

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

    def buildSelector(self,query):
        idMatch = ['id:'+bulb.id for bulb in self.filteredLights(query)]
        return ','.join(idMatch)

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

    def abstractRequest(self,*args,**kwargs):
        print(args[0])
        #print((args,kwargs))

        query = kwargs['query']
        del kwargs['query']
        data = kwargs

        label = args[0]
        if label == 'on':
            cmd = 'setState'
            data['power'] = 'on'

        elif label == 'off':
            cmd = 'setState'
            data['power'] = 'off'

        elif label == 'toggle':
            cmd = 'toggle'

        elif label == 'setPower':
            cmd,data = 'setState',{'power':args[1]}

        elif label == 'setColor':
            if len(args) > 1 and type(args[1]) == type('string'):
                cmd,data = 'setState',{'color':args[1]}
            else: # if we get a bunch of keyword arguments, need to compile to string
                cmd = 'setState'
                s = []
                if 'rgb' in kwargs.keys():
                    s.append('rgb:' + ','.join([str(e) for e in kwargs['rgb']]))

                s += [k+':'+str(v) for k,v in kwargs.items() if k != 'rgb']
                data = {'color':' '.join(s)}


        elif label == 'setBrightness':
            cmd,data = 'setState',{'brightness':args[1]}

        elif label == 'setInfrared':
            cmd,data = 'setState',{'infrared':args[1]}

        elif label == 'setState':
            cmd = 'setState'

        elif label == 'stateDelta':
            cmd = 'stateDelta'

        elif label == 'breatheEffect':
            cmd = 'breatheEffect'

        elif label == 'pulseEffect':
            cmd = 'pulseEffect'

        elif label == 'cycle':
            cmd = 'cycle'

        else:
            cmd = ''


        #print('received by abstractRequest')
        #print((cmd,data))
        #print(' ')

        self.handleBackoff(cmd,query,data)

    def handleBackoff(self,cmd,query,data):
        self.actuallyRequest(cmd,query,data)

    def actuallyRequest(self,cmd,query,data):
        params = self.requestParams[cmd]

        method = params['method']
        url = params['url'].format(self.buildSelector(query))

        print(method,url,data)




with open('tokens.json') as f:
    token = json.load(f)['lifx']



s = State(token)

bedroom = s.filter(lambda bulb : 'bedroom' in bulb.label)
closet = s.filter(lambda bulb : 'closet' in bulb.label)

colorCapable = s.filter(lambda bulb : bulb.product.capabilities.has_color)

#closet.setState(brightness=0.5,color='green')

closet.on()
closet.on(duration=5.0)
closet.off()
closet.toggle()
closet.toggle(duration=2.0)
closet.setPower('on')
closet.setColor('green')
closet.setColor(brightness=0.5,rgb=[0,100,100])
closet.setBrightness(0.5)
closet.setInfrared(0.2)
closet.setState(color='blue',brightness=0.5)
closet.stateDelta(hue=-15,saturation=0.1)
closet.breatheEffect(color='red',from_color='blue')
closet.pulseEffect(color='red',from_color='blue',period=0.5)
closet.cycle(states={'states':[{'color':'red'},{'color':'blue'}],'defaults':{'power':'on'}})

#scenes = s.getScenes()


#closet.off()













