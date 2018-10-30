from pprint import pprint
import time
import json
import requests
import asyncio



class Thing(object):
    def __init__(self, typ, data):
        self.typ = typ
        for k, v in data.items():
            setattr(self, k, v)
            if isinstance(v, dict):
                setattr(self, k, Thing(self.typ, v))

    def __repr__(self):
        return self.typ.title() + '({0})'.format(self.label)

    def dict(self):
        d = {}
        for k, v in vars(self).items():
            if isinstance(v, Thing):
                d[k] = v.dict()
            else:
                d[k] = v
        return d






class Method(object):
    def __init__(self, domain, cmd, ptr):
        self.domain = domain
        self.cmd = cmd
        self.ptr = ptr

    def __call__(self, *args, **kwargs):
        self.ptr(self.domain, self.cmd, *args, **kwargs)

class View(object):
    def __init__(self, domain, parent, query):
        self.domain = domain
        self.parent = parent
        self.query = query

        self.cmdList = {'lights': ['off',
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
                                   'cycle'],
                        'scenes': ['activate']}

    def abstract_request(self, *args, **kwargs):
        kwargs['query'] = self.query
        self.parent.request(*args, **kwargs)

    def __contains__(self, item):
        names = []
        for bulb in self.parent.parent.filteredLights(self.query):
            names.append(self.parent.parent.lightsData[bulb].label)
            names.append(self.parent.parent.lightsData[bulb].id)
        return item in names

    def __getattr__(self, e):
        if e in self.cmdList[self.domain]:
            return Method(self.domain, e, self.abstractRequest)

    def __repr__(self):
        if self.domain == 'lights':
            contents = ','.join(['label:'+bulb.label for bulb in self.parent.filteredLights(self.query)])
        elif self.domain == 'scenes':
            contents = ','.join(['name:'+bulb.name for bulb in self.parent.filteredScenes(self.query)])
        return self.domain.title() + 'View({0})'.format(contents)

class Handler(object):
    def __init__(self, domain, parent):
        self.domain = domain
        self.parent = parent

    def filter(self, query):
        return View(self.domain, self, query)

    def filtered_lights(self, query):
        return self.parent.filteredLights(query)

    def filtered_scenes(self, query):
        return self.parent.filteredScenes(query)

    def __contains__(self, item):
        names = []
        for s in self.parent.listLights():
            names.append(s.label)
            names.append(s.id)
        return item in names

    def request(self, *args, **kwargs):
        self.parent.request(*args, **kwargs)








class State(object):
    def __init__(self,token,alwaysRefresh=True):
        self.alwaysRefresh = alwaysRefresh
        self.handleRequest = HandleRequest(self,token)

        self.lights = Handler('lights',self)
        self.refreshLights()

        self.scenes = Handler('scenes',self)
        self.refreshScenes()

    def refreshLights(self):
        self.lightsData = self.handleRequest.fetchLights()

    def refreshScenes(self):
        self.scenesData = self.handleRequest.fetchScenes()

    def listLights(self):
        if self.alwaysRefresh:
            self.refreshLights()
        return list(self.lightsData.values())

    def listScenes(self):
        if self.alwaysRefresh:
            self.refreshScenes()
        return list(self.scenesData.values())

    def debugLights(self):
        return [e.dict() for e in self.lightsData.values()]

    def filteredLights(self,query):
        return [bulb for bulb in self.listLights() if query(bulb)]

    def filteredScenes(self,query):
        return [scene for scene in self.listScenes() if query(scene)]

    def request(self,*args,**kwargs):
        query = kwargs['query']
        del kwargs['query']
        data = kwargs
        domain,cmd = args

        if domain == 'lights':
            ids = [bulb.id for bulb in self.filteredLights(query)]
        elif domain == 'scenes':
            ids = [scene.uuid for scene in self.filteredScenes(query)]

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


class HandleRequest(object):
    def __init__(self,parent,token):
        self.parent = parent
        self.token = token
        self.headers = {'Authorization': 'Bearer ' + self.token}
        self.backoff = [1,1,1,1,1,2,4,8,16,32]

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
                       'scenes':{'activateScene': {'url':'https://api.lifx.com/v1/scenes/{0}/activate',
                                                   'method':'put'}}}

    def fetchLights(self):
        print('hard refresh')
        resp = requests.get('https://api.lifx.com/v1/lights/all',headers=self.headers)
        return {e['id']:Thing('Bulb',e) for e in resp.json()}

    def fetchScenes(self):
        resp = requests.get('https://api.lifx.com/v1/scenes', headers=self.headers)
        return {e['uuid']:Thing('Scene',e) for e in resp.json()}

    def request(self,domain,ids,cmd,data):
        if domain == 'lights':
            cmd,data = self.buildLightRequest(cmd,data)
            method = self.params[domain][cmd]['method']
            url = self.params[domain][cmd]['url']
            self.actuallyRequest(domain,method,url,ids,data)
        elif domain == 'scenes':
            cmd,data = self.buildSceneRequest(cmd,data)
            method = self.params[domain][cmd]['method']
            url = self.params[domain][cmd]['url']
            self.actuallyRequest(domain,method,url,ids,data)


    def actuallyRequest(self,domain,method,url,ids,data):
        if domain == 'lights':
            selector = ','.join(['id:'+i for i in ids])
        elif domain == 'scenes':
            selector = ','.join(['scene_id:'+i for i in ids])

        print(method,url.format(selector),data)

    def buildSceneRequest(self,label,data):
        if label == 'activate':
            cmd = 'activateScene'
        elif label == 'activateScene':
            cmd = label

        return cmd,data

    def buildLightRequest(self,label,data):
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










'''

with open('tokens.json') as f:
    token = json.load(f)['lifx']






state = State(token,alwaysRefresh=False)

bedroom = state.lights.filter(lambda bulb : 'bedroom' in bulb.label)
bedroom.setState(color='white',power='off')

print(bedroom)

night = state.scenes.filter(lambda scene : 'Night' in scene.name)

print(night)

night.activate()
'''
