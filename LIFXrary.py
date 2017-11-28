from pprint import pprint
import time
import json
import requests
import asyncio



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

def bulb2dict(bulb):
    d = {}
    for k,v in vars(bulb).items():
        if type(v) == type(Bulb()):
            d[k] = bulb2dict(v)
        else:
            d[k] = v
    return d

class Method(object):
    def __init__(self,route,ptr):
        self.route = route
        self.ptr = ptr

    def __call__(self,*args,**kwargs):
        self.ptr(self.route,*args,**kwargs)

'''
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
'''
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

    def __repr__(self):
        contents = ','.join(['label:'+bulb.label for bulb in self.parent.filteredLights(self.query)])
        return 'View({0})'.format(contents)

class State(object):
    def __init__(self,token,alwaysRefresh=True):
        self.headers = {'Authorization': 'Bearer ' + token}
        self.backoff = [1,1,1,1,1,2,4,8,16,32]

        '''
        TODO: implement a low-latency mode where the module attempts to
        keep track of all lights' state for filtering purposes, to reduce the
        number of calls required to get lights' current state. Likely error-prone
        in non-ideal network conditions or with complex operations, but
        should assist in performing tightly choreographed sequences
        '''
        self.alwaysRefresh = alwaysRefresh

        self.requestParams = {'toggle':        {'url':'https://api.lifx.com/v1/lights/{0}/toggle',
                                                'method':'post'},
                              'setState':      {'url':'https://api.lifx.com/v1/lights/{0}/state',
                                                'method':'put'},
                              'stateDelta':    {'url':'https://api.lifx.com/v1/lights/{0}/state/delta',
                                                'method':'post'},
                              'breatheEffect': {'url':'https://api.lifx.com/v1/lights/{0}/effects/breathe',
                                                'method':'post'},
                              'pulseEffect':   {'url':'https://api.lifx.com/v1/lights/{0}/effects/pulse',
                                                'method':'post'},
                              'cycle':         {'url':'https://api.lifx.com/v1/lights/{0}/cycle',
                                                'method':'post'}}

        self.loop = []

        self.hardRefresh()

    def hardRefresh(self):
        print('hard refresh')
        resp = requests.get('https://api.lifx.com/v1/lights/all',headers=self.headers)
        self.lights = {e['id']:buildBulb(e) for e in resp.json()}

    def filter(self,query):
        return View(self,query)

    def setBackoff(self,backoff):
        assert(type(backoff) == type([]))
        self.backoff = backoff

    def listLights(self):
        if self.alwaysRefresh:
            self.hardRefresh()
        return list(self.lights.values())

    def debugState(self):
        return [bulb2dict(e) for e in self.lights.values()]

    def filteredLights(self,query):
        return [bulb.id for bulb in self.listLights() if query(bulb)]

    def abstractRequest(self,*args,**kwargs):
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


        bulbs = self.filteredLights(query)
        self.handleBackoff(cmd,bulbs,data)

    # TODO: make concurrent
    def coroutine(self,backoff,cmd,bulbs,data):
        while len(backoff) > 0 and len(bulbs) > 0:
            time.sleep(backoff.pop(0))

            bulbs,resp = self.actuallyRequest(cmd,bulbs,data)

    def handleBackoff(self,cmd,bulbs,data):
        bulbs,resp = self.actuallyRequest(cmd,bulbs,data) # try once

        if len(bulbs) > 0:
            self.coroutine(self.backoff[:],cmd,bulbs,data)

    def updateState(self,bulb,cmd,data):
        if cmd == 'setState':
            for k,v in data.items():
                setattr(self.lights[bulb],k,v)
        elif cmd == 'toggle':
            if self.lights[bulb].power == 'on':
                self.lights[bulb].power = 'off'
            else:
                self.lights[bulb].power = 'on'

    def actuallyRequest(self,cmd,bulbs,data):
        method = self.requestParams[cmd]['method']
        url = self.requestParams[cmd]['url']

        selector = ','.join(['id:'+i for i in bulbs])
        url = url.format(selector)

        print(method,url,data)

        if method == 'get':
            resp = requests.get(url,headers=self.headers)
        elif method == 'put':
            resp = requests.put(url,headers=self.headers,data=data)
        elif method == 'post':
            resp = requests.post(url,headers=self.headers,data=data)

        failed = []
        for result in resp.json()['results']:
            if result['status'] == 'ok':
                self.updateState(result['id'],cmd,data)
            else:
                failed.append(result['id'])

        return failed,resp.json()



with open('tokens.json') as f:
    token = json.load(f)['lifx']








state = State(token,alwaysRefresh=False)

bedroom = state.filter(lambda bulb : 'bedroom' in bulb.label)

bedroom.toggle()







