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
        for eq in self.possible_equipment:
            data["equipment_%s" % eq] = self._browse_equipment_list(eq)
        return data
        # TODO: complete features list and store it

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

    def _browse_equipment_list(self, equip_name):
        return equip_name in self._all_equipment()

    def _all_equipment(self):
        equip_div = self.soup.find_all('div', id='equipList')
        return [li.text for li in equip_div[0].find_all('li')]


class PageParser:
    """
    Class parsing sauto page
    """

    def __init__(self, model, debug=False, custom_models_list=None):
        """
        :param model: tuple (manufacturer_id, model_id)
        :param debug: debug mode (default: False)
        """

        models_list = {('skoda', 'fabia'): (93, 707),
                       ('skoda', 'octavia'): (93, 705),
                       ('skoda', 'rapid'): (93, 6445)}
        if custom_models_list:
            print('Models_list replaced.\n%s' % str(custom_models_list))
            models_list = custom_models_list
        self.model = model
        self.debug = debug
        self.page_url = 'https://www.sauto.cz/hledani'
        try:
            self.params = (
                ('ajax', '2'),
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
                ('manufacturer', str(models_list[model][0])),
                ('model', str(models_list[model][1])),
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
        pages = self.get_page_data(1)['paging']['pages']
        cars = []
        if self.debug:
            print("PageParser: number of pages: %d" % (len(pages)))
        for pageindex in pages:
            page = pageindex['i']
            if self.debug:
                print("PageParser: parsing page %s" % str(page))
            if pages_nr and int(page) > pages_nr:
                break
            data = self.get_page_data(page)
            for x in data['advert']:
                cars.append(CarParser(self.model[0], self.model[1], x['advert_id']).parse())
        if self.debug:
            print("PageParser: number of cars: %d" % len(cars))
        cars = dict(zip(cars[0], zip(*[d.values() for d in cars])))
        return pd.DataFrame(cars, columns=cars.keys())
