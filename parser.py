import re

import requests
from bs4 import BeautifulSoup


class CarParser:
    def __init__(self, brand, model, id):
        self.brand = brand
        self.model = model
        r = requests.get('https://www.sauto.cz/osobni/detail/%s/%s/%d' % (brand, model, id)).text
        self.soup = BeautifulSoup(r, "lxml")

    def parse(self):
        price = int(re.sub("\D", "", self.soup.find_all("strong", itemprop='price')[0].get_text()))
        year = int(self.soup.find_all("td", attrs={'data-sticky-header-value-src': 'year'})[0].get_text()[-4:])
        odometer = int(self.parse_tr('Tachometr:', digits=True))
        fuel_type = self.parse_tr('Palivo:')
        transmission = self.parse_tr('Převodovka:')
        ccm = int(self.parse_tr('Objem:', digits=True))
        hp = self.parse_tr('Výkon:')
        one_owner = self.parse_tr('První majitel:') == "ano"
        service_book = self.parse_tr('Servisní knížka:') == "ano"
        origin_country = self.parse_tr('Země původu:')
        STK = self.parse_tr('STK:')

        # Test:
        print(
            "%s %s\nprice %d\nyear %d\nodometer %d\nfuel_type %s\ntransmission %s\nccm %d\nhp %s\none_owner %s\nservice_book %s\norigin_country %s\nSTK %s" % (
            self.brand, self.model, price,
            year, odometer, fuel_type, transmission, ccm, hp, one_owner, service_book, origin_country, STK))

        # TODO: complete features list and store it

    def parse_tr(self, key, digits=False):
        trs = self.soup.find_all('tr')
        for tr in trs:
            children = tr.findChildren()
            if len(children) == 2:
                if children[0].get_text() == key:
                    if digits:
                        return re.sub("\D", "", children[1].get_text())
                    return children[1].get_text()
        return ""
