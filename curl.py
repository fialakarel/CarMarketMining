#!/usr/bin/python3

import requests
import json
import parser
import sys

def getData(page):
    params = (
        ('ajax', '2'),
        ('page', str(page)),
        ('stk', '1'),
        ('notCrashed', '1'),
        ('first', '1'),
        ('aircondition', '2'),
        ('gearbox', '1'),
        ('state', '1'),
        ('fuel', '1'),
        ('tachometrMax', '75000'),
        ('yearMin', '2015'),
        ('priceMax', '500000'),
        ('priceMin', '100000'),
        ('condition', ['4', '2', '1']),
        ('category', '1'),
        ('manufacturer', '93'),
        ('model', '707'),
        ('nocache', '658'),
    )
    
    r = requests.get('https://www.sauto.cz/hledani', params=params)
    
    data = json.loads(r.text)

    # delete unrelevant information
    del data['ad']
    del data['importKeys'] 
    del data['checkBox']          # wtf?
    del data['priorityAdvert']    # advertisement
    
    # delete non data fields
    del data['codebook']    # search options
    del data['filter']    # search options too?
    del data['manufacturer']    # Manufacturer + count
    del data['equipments']    # car equipments
    
    
    #data['paging']      # page informations
    #data['resultSize']      # result size
    #data['advert']      # adverts on selected page

    return data



#print(json.dumps(data['resultSize'], indent=4, sort_keys=True))
#print(json.dumps(data['advert'], indent=4, sort_keys=True))
#print(json.dumps(data, indent=4, sort_keys=True))

initdata = getData(1)

#print("Per page: " + str(initdata['paging']['perPage']))
firstRun = True

for pageindex in initdata['paging']['pages']:
    page = pageindex['i']

    data = getData(page)

    for x in data['advert']:
        #print(json.dumps(x, indent=4, sort_keys=True))
        #print(x['advert_id'])
        cp = parser.CarParser('skoda', 'fabia', x['advert_id'])
        car = cp.parse()
        if firstRun:
            print(';'.join([str(key) for key, value in car.items()]))
            firstRun = False
        print(';'.join([str(value) for key, value in car.items()]))
    

#print(json.dumps(data['advert'], indent=4, sort_keys=True))

