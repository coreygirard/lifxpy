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

    def __call__(self):
        self.ptr()

class View(object):
    def __init__(self,parent,query):
        self.parent = parent
        self.query = query

        self.cmd = {'off':    Method(self.handleOff),
                    'on':     Method(self.handleOn),
                    'toggle': Method(self.handleToggle)}

    def handleOff(self):
        self.parent.operation(self.query,'off')

    def handleOn(self):
        self.parent.operation(self.query,'on')

    def handleToggle(self):
        self.parent.operation(self.query,'toggle')

    def __getattr__(self,e):
        if e in self.cmd.keys():
            return self.cmd[e]

    def __repr__(self):
        contents = ','.join(['label:'+bulb.label for bulb in self.parent.filteredLights(self.query)])
        return 'View({0})'.format(contents)

class State(object):
    def __init__(self,token):
        self.headers = {'Authorization': 'Bearer ' + token}

    def filter(self,query):
        return View(self,query)

    def listLights(self):
        resp = requests.get('https://api.lifx.com/v1/lights/all',headers=self.headers)
        return [buildBulb(e) for e in resp.json()]

    def filteredLights(self,query):
        return [bulb for bulb in self.listLights() if query(bulb)]

    def operation(self,query,op):
        idMatch = ['id:'+bulb.id for bulb in self.filteredLights(query)]
        selector = ','.join(idMatch)

        if op == 'on':
            self.on(selector)
        elif op == 'off':
            self.off(selector)
        elif op == 'toggle':
            self.toggle(selector)

    def on(self,selector):
        resp = requests.put('https://api.lifx.com/v1/lights/{0}/state'.format(selector),
                             data={'power':'on'},
                             headers=self.headers)

    def off(self,selector):
        resp = requests.put('https://api.lifx.com/v1/lights/{0}/state'.format(selector),
                             data={'power':'off'},
                             headers=self.headers)

    def toggle(self,selector):
        resp = requests.post('https://api.lifx.com/v1/lights/{0}/toggle'.format(selector),
                             headers=self.headers)

token = ''

s = State(token)

bedroom = s.filter(lambda bulb : 'bedroom' in bulb.label)
closet = s.filter(lambda bulb : 'closet' in bulb.label)


warm = s.filter(lambda bulb : bulb.color.kelvin == 3500)

#closet.toggle()

#recent = s.filter(lambda bulb : bulb['seconds_since_seen'] < 20)


print(closet)
print(warm)


'''
class State(object):
    def __init__(self,token):
        self.headers = {'Authorization': 'Bearer ' + token}

    def filter(self,query):
        return View(query)


token = ''

s = State(token)


q = s.filter('hello')

q.off()
'''


'''
token = ''

s = State(token)

resp = requests.get('https://api.lifx.com/v1/lights/all',headers=s.headers)

from pprint import pprint
pprint(resp.json())


class Light(object):
    def __init__(self,data,headers):
        self.data = data
        self.headers = headers

        self.brightness = data['brightness']
        self.hue = data['color']['hue']
        self.kelvin = data['color']['kelvin']
        self.saturation = data['color']['saturation']
        self.id = data['id']
        self.label = data['label']
        self.power = data['power']


class State(object):
    def __init__(self,token):
        self.headers = {"Authorization": "Bearer %s" % token}

        self.light = {}
        for e in self.listAll():
            temp = Light(e,self.headers)
            self.light[temp.label] = temp

    def makeRequest(self,method,url,selector,data={}):
        if method == 'get':
            response = requests.get(url.format(selector=selector), headers=self.headers)
        elif method == 'put':
            response = requests.put(url.format(selector=selector), data=data, headers=self.headers,verify=False)
        elif method == 'post':
            response = requests.post(url.format(selector=selector), data=data, headers=self.headers,verify=False)

        return json.loads(response.text)

    def listAll(self):
        url = 'https://api.lifx.com/v1/lights/{selector}'
        results = self.makeRequest('get',url=url,selector='all')
        return results

    def setState(self,selector,data):
        results = self.makeRequest('put','https://api.lifx.com/v1/lights/{selector}/state',selector=selector,data=data)
        return results


    def tryIt(self,typ,url1,selector,url2,payload,waits=[1]): #[1,1,1,1,1,5,5,5,5,5,5]
        results = {}
        while (len(selector) > 0) and (len(waits) > 0):
            s = ','.join(['label:'+e for e in selector])

            #Make the HTTP call
            if typ == 'put':
                response = requests.put(url1 + s + url2,data=payload,headers=self.headers)
            elif typ == 'post':
                response = requests.post(url1 + s + url2,data=payload,headers=self.headers)

            #Get results of attempt
            r = json.loads(response.text)['results']

            #Remove successful operations for next attempt
            for d in r:
                if d['status'] == 'ok':
                    results[d['label']] = d['status']
                    selector = [e for e in selector if e != d['label']]

            #If some attempts failed
            if len(selector) > 0:
                time.sleep(waits.pop())

        #Throw the failed results into the report
        for d in r:
            results[d['label']] = d['status']

        if all([e=='ok' for e in results.values()]):
            return results,'SUCCESS'
        else:
            return results,'FAILURE'


    def on(self,selector,duration=1.0):
        payload = {'power':'on','duration':duration}
        results,outcome = self.tryIt('put','https://api.lifx.com/v1/lights/',selector,'/state',payload)
        return results,outcome

    def off(self,selector,duration=1.0):
        payload = {'power':'off','duration':duration}
        results,outcome = self.tryIt('put','https://api.lifx.com/v1/lights/',selector,'/state',payload)
        return results,outcome

    def toggle(self,selector,duration=1.0):
        payload = {'duration':duration}
        results,outcome = self.tryIt('post','https://api.lifx.com/v1/lights/',selector,'/toggle',payload)
        return results,outcome


def connect(token):
    return State(token)
'''








