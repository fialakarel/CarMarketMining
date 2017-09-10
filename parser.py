import json
import re

import pandas as pd
import requests
import unidecode
from bs4 import BeautifulSoup


class CarParser:
    """
    Class extracting data from car advertising page
    """

    def __init__(self, manufacturer=None, model=None, id=None, debug=False):
        self.manufacturer = manufacturer
        self.model = model
        self.id = id
        if id:
            r = requests.get('https://www.sauto.cz/osobni/detail/%s/%s/%d' % (manufacturer, model, id)).text
            self.soup = BeautifulSoup(r, "lxml")
        else:
            self.soup = None
        self.debug = debug
        self.possible_equipment = [unidecode.unidecode(x).replace(' ', '_').replace('.', '')
                                   for x in ['ABS', 'CD přehrávač', 'EDS', 'ESP', 'Start/Stop systém', 'USB',
                                             'alarm', 'automatická klimatizace', 'automatické svícení',
                                             'autorádio', 'bluetooth', 'centrální zamykání',
                                             'deaktivace airbagu spolujezdce', 'dálkové centrální zamykání',
                                             'dělená zadní sedadla', 'el. ovládání oken', 'el. ovládání zrcátek',
                                             'el. seřiditelná sedadla', 'el. sklopná zrcátka', 'imobilizér',
                                             'isofix', 'klimatizovaná přihrádka', 'litá kola', 'mlhovky',
                                             'nastavitelná sedadla', 'nastavitelný volant', 'nouzové brždění',
                                             'originál autorádio', 'palubní počítač', 'panoramatická střecha',
                                             'parkovací senzory', 'posilovač řízení',
                                             'protiprokluzový systém kol (ASR)', 'přídavná světla',
                                             'příprava pro isofix', 'příprava pro telefon',
                                             'senzor opotřebení brzd. destiček', 'senzor tlaku v pneumatikách',
                                             'střešní nosič', 'tažné zařízení', 'telefon', 'tempomat',
                                             'tónovaná skla', 'venkovní teploměr', 'vstup paměťové karty',
                                             'vyhřívaná zrcátka', 'vyjímatelná zadní sedadla',
                                             'výškově nastavitelná sedadla',
                                             'výškově nastavitelné sedadlo řidiče', 'zadní stěrač',
                                             'zaslepení zámků', 'zámek řadící páky']]

    def parse(self, manufacturer=None, model=None, id=None):
        """
        Parse car page
        :param manufacturer: manufacturer string or None to use manufacturer from constructor (default: None)
        :param model: model string or None to use manufacturer from constructor (default: None)
        :param id: integer of the advert id or None to use id from constructor (default: None)
        :return: dictionary with parsed car
        """
        if manufacturer is not None:
            self.manufacturer = manufacturer
        if model is not None:
            self.model = model
        if id is not None:
            r = requests.get('https://www.sauto.cz/osobni/detail/%s/%s/%d' % (manufacturer, model, id)).text
            self.soup = BeautifulSoup(r, "lxml")
            self.id = id
        data = dict()
        data['advert_id'] = str(self.id)
        data['manufacturer'] = self.manufacturer
        data['model'] = self.model
        data['price'] = int(re.sub("\D", "", self.soup.find_all("strong", itemprop='price')[0].get_text()))
        data['year'] = int(self.soup.find_all("td", attrs={'data-sticky-header-value-src': 'year'})[0].get_text()[-4:])
        data['odometer'] = int(self._parse_tr('Tachometr:', digits=True))
        data['fuel_type'] = self._parse_tr('Palivo:')
        data['transmission'] = self._parse_tr('Převodovka:')
        data['ccm'] = int(self._parse_tr('Objem:', digits=True))
        data['hp'] = self._parse_tr('Výkon:')
        data['one_owner'] = self._parse_tr('První majitel:') == "ano"
        data['service_book'] = self._parse_tr('Servisní knížka:') == "ano"
        data['origin_country'] = self._parse_tr('Země původu:')
        data['stk'] = self._parse_tr('STK:')
        data['airbags'] = self._parse_tr('Počet airbagů:')
        data['bodywork'] = self._parse_tr('Karoserie:')
        data['condition'] = self._parse_tr('Stav:')
        data['colour'] = self._parse_tr('Barva:')
        data['places_nr'] = self._parse_tr('Počet míst:')
        data['doors_nr'] = self._parse_tr('Počet dveří:')
        equipment = self._all_equipment()
        if len(equipment) == 0:
            return None
        for eq in self.possible_equipment:
            data["equipment_%s" % eq] = eq in equipment
        return data

    def _parse_tr(self, key, digits=False):
        trs = self.soup.find_all('tr')
        for tr in trs:
            children = tr.findChildren()
            if len(children) == 2:
                if children[0].get_text() == key:
                    if digits:
                        return re.sub("\D", "", children[1].get_text())
                    return children[1].get_text()
        return ""

    def _all_equipment(self):
        equip_div = self.soup.find_all('div', id='equipList')
        try:
            return [li.text for li in equip_div[0].find_all('li')]
        except IndexError:
            #print('No equip for car: %s, %s, %s' % (self.manufacturer, self.model, str(self.id)))
            return []


class PageParser:
    """
    Class parsing sauto page
    """

    def __init__(self, debug=False):
        """
        :param debug: debug mode (default: False)
        """

        self.debug = debug
        self.page_url = 'https://www.sauto.cz/hledani'
        try:
            self.params = (
                ('ajax', '2'),
                ('stk', '1'),
                ('notCrashed', '1'),
                ('state', '1'),
                ('yearMin', '2000'),
                ('condition', ['4', '2', '1']),
                ('category', '1'),
                ('nocache', '658'),
            )
        except KeyError:
            raise KeyError('Unknown manufacturer or model.')
        pass

    def get_page_data(self, page):
        """
        Lads data of a page
        :param page: page to load (int or string)
        :return: dictionary of page elements
        """
        r = requests.get(self.page_url, params=self.params + (('page', str(page)),))
        data = json.loads(r.text)
        for k in ['ad', 'importKeys', 'checkBox', 'priorityAdvert', 'codebook', 'filter', 'manufacturer', 'equipments']:
            del data[k]
        return data

    def get_data(self, pages_nr=None):
        """
        Parse data of all pages
        :param pages: limits number of pages
        :return: pandas DataFrame
        """
        page = 0
        cars = []
        while True:
            page += 1
            if self.debug:
                print("PageParser: parsing page %s, cars loaded: %d" % (str(page), len(cars)))
            if pages_nr and page >= pages_nr:
                break
            data = self.get_page_data(str(page))
            if len(data['advert']) == 0:
                break
            for x in data['advert']:
                cars.append(CarParser(x['manufacturer_name'], x['model_name'], x['advert_id']).parse())
        cars = [x for x in cars if x is not None] # remove cars without equipment
        if self.debug:
            print("PageParser: number of cars: %d" % len(cars))
        cars = dict(zip(cars[0], zip(*[d.values() for d in cars])))
        return pd.DataFrame(cars, columns=cars.keys())
