from pprint import pprint
import time
import json
import requests
import asyncio



class Bulb(object):
    def __repr__(self):
        return 'Light({0})'.format(self.label)

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

class LightsView(object):
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

    def __contains__(self,item):
        names = []
        for bulb in self.parent.parent.filteredLights(self.query):
            names.append(self.parent.parent.lightsData[bulb].label)
            names.append(self.parent.parent.lightsData[bulb].id)
        return item in names

    def __getattr__(self,e):
        if e in self.cmdList:
            return Method(e,self.abstractRequest)

    def __repr__(self):
        contents = ','.join(['label:'+bulb.label for bulb in self.parent.filteredLights(self.query)])
        return 'LightsView({0})'.format(contents)

class LightsHandler(object):
    def __init__(self,parent):
        self.parent = parent

    def filter(self,query):
        return LightsView(self,query)

    def __contains__(self,item):
        names = []
        for s in self.parent.listLights():
            names.append(s.label)
            names.append(s.id)
        return item in names

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

        bulbs = self.parent.filteredLights(query)
        self.parent.requestAndRetry(cmd,bulbs,data)












class Scene(object):
    def __repr__(self):
        return 'Scene({0})'.format(self.label)

def setSceneData(scene,data):
    for k,v in data.items():
        setattr(scene,k,v)
        if type(v) == type(dict()):
            setattr(scene,k,Scene())

            setBulbData(getattr(scene,k),v)

def buildScene(data):
    scene = Scene()
    setSceneData(scene,data)
    return scene

def scene2dict(scene):
    d = {}
    for k,v in vars(scene).items():
        if type(v) == type(Scene()):
            d[k] = scene2dict(v)
        else:
            d[k] = v
    return d

class SceneView(object):
    def __init__(self,parent,query):
        self.parent = parent
        self.query = query

    def __contains__(self,item):
        names = []
        for s in self.parent.parent.filteredScenes(self.query):
            names.append(self.parent.parent.scenesData[s].uuid)
            names.append(self.parent.parent.scenesData[s].name)
        return item in names

    def activate(self):
        self.parent.activate(self.query)


class SceneHandler(object):
    def __init__(self,parent):
        self.parent = parent

    def __contains__(self,item):
        names = [s['name'] for s in self.parent.sceneData.values()]
        return item in names

    def filter(self,query):
        return SceneView(self,query)

    def activate(self,query):
        self.parent.activateScene(query)



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

        self.hardRefresh()
        self.fetchScenes()
        self.scenes = SceneHandler(self)
        self.lights = LightsHandler(self)

    # -------- FETCHING CURRENT STATE FROM SERVER --------

    def hardRefresh(self):
        print('hard refresh')
        resp = requests.get('https://api.lifx.com/v1/lights/all',headers=self.headers)
        self.lightsData = {e['id']:buildBulb(e) for e in resp.json()}

    def fetchScenes(self):
        resp = requests.get('https://api.lifx.com/v1/scenes', headers=self.headers)
        self.scenesData = {e['uuid']:buildScene(e) for e in resp.json()}

    def listLights(self):
        if self.alwaysRefresh:
            self.hardRefresh()
        return list(self.lightsData.values())

    def debugState(self):
        return [bulb2dict(e) for e in self.lightsData.values()]

    def filteredLights(self,query):
        return [bulb.id for bulb in self.listLights() if query(bulb)]

    def listScenes(self):
        return list(self.scenesData.values())

    def filteredScenes(self,query):
        return [scene.uuid for scene in self.listScenes() if query(scene)]


    # -------- HANDLE SENDING REQUESTS FOR STATE CHANGE --------

    def setBackoff(self,backoff):
        assert(type(backoff) == type([]))
        self.backoff = backoff

    def requestAndRetry(self,cmd,bulbs,data):
        bulbs,resp = self.actuallyRequest(cmd,bulbs,data) # try once

        if len(bulbs) > 0:
            self.coroutine(self.backoff[:],cmd,bulbs,data)

    # TODO: make concurrent
    def coroutine(self,backoff,cmd,bulbs,data):
        while len(backoff) > 0 and len(bulbs) > 0:
            time.sleep(backoff.pop(0))
            bulbs,resp = self.actuallyRequest(cmd,bulbs,data)

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

    def updateState(self,bulb,cmd,data):
        if cmd == 'setState':
            for k,v in data.items():
                setattr(self.lightsData[bulb],k,v)
        elif cmd == 'toggle':
            if self.lightsData[bulb].power == 'on':
                self.lightsData[bulb].power = 'off'
            else:
                self.lightsData[bulb].power = 'on'

    # -------- HANDLE SCENES --------

    def activateScene(self,query):
        for i in self.filteredScenes(query):
            print(i)

            url = 'https://api.lifx.com/v1/scenes/{0}/activate'
            url = url.format('scene_id:'+i)
            resp = requests.put(url,headers=self.headers)





with open('tokens.json') as f:
    token = json.load(f)['lifx']

state = State(token,alwaysRefresh=False)
bedroom = state.lights.filter(lambda bulb : 'bedroom' in bulb.label)
closet = state.lights.filter(lambda bulb : 'closet' in bulb.label)
#bedroom.toggle()

assert('corey_bedroom' in bedroom)
assert('corey_bedroom' not in closet)
assert('corey_closet' not in bedroom)
assert('corey_closet' in closet)

assert('d073d512e980' in bedroom)
assert('d073d512e980' not in closet)
assert('d073d510ae5b' not in bedroom)
assert('d073d510ae5b' in closet)

bedroom.setColor('white')
bedroom.off()

#state.activateScene('Red')

blue = state.scenes.filter(lambda scene : scene.name == 'Blue')
red = state.scenes.filter(lambda scene : scene.name == 'Red')

assert('Blue' in blue)
assert('Red' in red)

'''
while True:
    blue.activate()
    time.sleep(5)
    red.activate()
    time.sleep(5)
'''



'''
state = State(token,alwaysRefresh=False)

print(state.listLights())

assert('Red' in state.scenes)
state.activateScene('Red')
'''


















