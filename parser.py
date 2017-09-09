import json
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup


class CarParser:
    """
    Class extracting data from car advertising page
    """

    def __init__(self, brand=None, model=None, id=None, debug=False):
        self.brand = brand
        self.model = model
        if id:
            r = requests.get('https://www.sauto.cz/osobni/detail/%s/%s/%d' % (brand, model, id)).text
            self.soup = BeautifulSoup(r, "lxml")
        else:
            self.soup = None
        self.debug = debug

    def parse(self, brand=None, model=None, id=None):
        """
        Parse car page
        :param brand: brand string or None to use brand from constructor (default: None)
        :param model: model string or None to use brand from constructor (default: None)
        :param id: integer of the advert id or None to use id from constructor (default: None)
        :return: dictionary with parsed car
        """
        if brand is not None:
            self.brand = brand
        if model is not None:
            self.model = model
        if id is not None:
            r = requests.get('https://www.sauto.cz/osobni/detail/%s/%s/%d' % (brand, model, id)).text
            self.soup = BeautifulSoup(r, "lxml")
        data = dict()
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


class PageParser:
    """
    Class parsing sauto page
    """

    def __init__(self, debug=False):
        self.debug = debug
        self.page_url = 'https://www.sauto.cz/hledani'
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
            ('manufacturer', '93'),
            ('model', '707'),
            ('nocache', '658'),
        )
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
                cars.append(CarParser('skoda', 'fabia', x['advert_id']).parse())
        if self.debug:
            print("PageParser: number of cars: %d" % len(cars))
        cars = dict(zip(cars[0], zip(*[d.values() for d in cars])))
        return pd.DataFrame(cars, columns=cars.keys())
