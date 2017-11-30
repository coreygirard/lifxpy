from pprint import pprint
import time
import json
import requests
import asyncio



class Bulb(object):
    def __init__(self,data):
        for k,v in data.items():
            setattr(self,k,v)
            if type(v) == type(dict()):
                setattr(self,k,Bulb(v))

    def __repr__(self):
        return 'Light({0})'.format(self.label)

    def dict(self):
        d = {}
        for k,v in vars(self).items():
            if type(v) == type(self):
                d[k] = v.dict()
            else:
                d[k] = v
        return d






class Method(object):
    def __init__(self,domain,cmd,ptr):
        self.domain = domain
        self.cmd = cmd
        self.ptr = ptr

    def __call__(self,*args,**kwargs):
        self.ptr(self.domain,self.cmd,*args,**kwargs)

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
        self.parent.request(*args,**kwargs)

    def __contains__(self,item):
        names = []
        for bulb in self.parent.parent.filteredLights(self.query):
            names.append(self.parent.parent.lightsData[bulb].label)
            names.append(self.parent.parent.lightsData[bulb].id)
        return item in names

    def __getattr__(self,e):
        if e in self.cmdList:
            return Method('lights',e,self.abstractRequest)

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

    def request(self,*args,**kwargs):
        '''
        query = kwargs['query']
        del kwargs['query']
        data = kwargs



        bulbs = self.parent.filteredLights(query)
        self.parent.request(cmd,bulbs,data)
        '''
        self.parent.request(*args,**kwargs)









class Scene(object):
    def __init__(self,data):
        for k,v in data.items():
            setattr(self,k,v)
            if type(v) == type(dict()):
                setattr(self,k,Bulb(v))

    def __repr__(self):
        return 'Scene({0})'.format(self.label)

    def dict(self):
        d = {}
        for k,v in vars(self).items():
            if type(v) == type(self):
                d[k] = v.dict()
            else:
                d[k] = v
        return d


'''
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
'''


class State(object):
    def __init__(self,token,alwaysRefresh=True):
        self.alwaysRefresh = alwaysRefresh
        self.handleRequest = HandleRequest(self)

        #self.hardRefresh()
        #self.fetchScenes()
        #self.scenes = SceneHandler(self)
        self.lights = LightsHandler(self)

    # -------- FETCHING CURRENT STATE FROM SERVER --------


    def listLights(self):
        if self.alwaysRefresh:
            self.lightsData = self.handleRequest.fetchLights()
        return list(self.lightsData.values())

    def debugState(self):
        return [e.dict() for e in self.lightsData.values()]

    def filteredLights(self,query):
        return [bulb.id for bulb in self.listLights() if query(bulb)]

    '''
    def listScenes(self):
        return list(self.scenesData.values())

    def filteredScenes(self,query):
        return [scene.uuid for scene in self.listScenes() if query(scene)]
    '''
    def setBackoff(self,backoff):
        assert(type(backoff) == type([]))
        self.handleRequest.setBackoff(backoff)

    '''
    def abstractRequest(self,*args,**kwargs):
        print(args,kwargs)
    '''

    def request(self,*args,**kwargs):
        query = kwargs['query']
        del kwargs['query']
        data = kwargs
        domain,cmd = args

        if domain == 'lights':
            ids = [bulb.id for bulb in self.listLights() if query(bulb)]
        elif domain == 'scenes':
            pass

        #print(domain,ids,cmd,data)
        self.handleRequest.request(domain,ids,cmd,data)

    def updateState(self,bulb,cmd,data):
        if cmd == 'setState':
            for k,v in data.items():
                setattr(self.lightsData[bulb],k,v)
        elif cmd == 'toggle':
            if self.lightsData[bulb].power == 'on':
                self.lightsData[bulb].power = 'off'
            else:
                self.lightsData[bulb].power = 'on'

    '''
    # -------- HANDLE SCENES --------

    def activateScene(self,query):
        for i in self.filteredScenes(query):
            print(i)

            url = 'https://api.lifx.com/v1/scenes/{0}/activate'
            url = url.format('scene_id:'+i)
            resp = requests.put(url,headers=self.headers)
    '''


class HandleRequest(object):
    def __init__(self,parent):
        self.parent = parent
        self.headers = {'Authorization': 'Bearer ' + token}
        self.backoff = [1,1,1,1,1,2,4,8,16,32]

        '''
        TODO: implement a low-latency mode where the module attempts to
        keep track of all lights' state for filtering purposes, to reduce the
        number of calls required to get lights' current state. Likely error-prone
        in non-ideal network conditions or with complex operations, but
        should assist in performing tightly choreographed sequences
        '''

        self.params = {'lights':{'toggle':        {'url':'https://api.lifx.com/v1/lights/{0}/toggle',
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
                                                   'method':'post'}},
                       'scenes':{}}

    def fetchLights(self):
        print('hard refresh')
        resp = requests.get('https://api.lifx.com/v1/lights/all',headers=self.headers)
        return {e['id']:Bulb(e) for e in resp.json()}

    '''
    def fetchScenes(self):
        resp = requests.get('https://api.lifx.com/v1/scenes', headers=self.headers)
        return {e['uuid']:Scene(e) for e in resp.json()}
    '''

    def request(self,domain,ids,cmd,data):
        #print(domain,ids,cmd,data)

        cmd,data = self.buildRequest(cmd,data)

        method = self.params[domain][cmd]['method']
        url = self.params[domain][cmd]['url']

        print(domain,method,url,ids,data)

        #bulbs,resp = self.actuallyRequest(cmd,bulbs,data) # try once

        #if len(bulbs) > 0:
        #    self.coroutine(self.backoff[:],cmd,bulbs,data)

    def actuallyRequest(self,domain,method,url,ids,data):
        if domain == 'lights':
            selector = ','.join(['id:'+i for i in ids])
        elif domain == 'scenes':
            selector = ','.join(['uuid:'+i for i in ids])

        print(method,url.format(delector)

        #if method == 'get':
        #    resp = requests.get(url.format(selector),data=data)

        '''
    # TODO: make concurrent
    def coroutine(self,backoff,cmd,bulbs,data):
        while len(backoff) > 0 and len(bulbs) > 0:
            time.sleep(backoff.pop(0))
            bulbs,resp = self.actuallyRequest(cmd,bulbs,data)

    def actuallyRequest(self,cmd,bulbs,data):
        # TODO: Implement a .freeze() method to hold all outgoing requests,
        # concatenating them into a single state change if possible, which is
        # then sent when the opposite method is called
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
                self.parent.updateState(result['id'],cmd,data)
            else:
                failed.append(result['id'])

        return failed,resp.json()

    def setBackoff(self,backoff):
        assert(type(backoff) == type([]))
        self.backoff = backoff
        '''

    def buildRequest(self,label,data):
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

        return cmd,data


































with open('tokens.json') as f:
    token = json.load(f)['lifx']






state = State(token)

bedroom = state.lights.filter(lambda bulb : 'bedroom' in bulb.label)
bedroom.setState(color='white',power='off')

#print(bedroom)

#red = state.scenes.filter(lambda scene : 'Red' in scene.name)

#print(red)





