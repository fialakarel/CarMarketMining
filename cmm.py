#!/usr/bin/python3

import urllib.request
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

url = 'https://www.sauto.cz/osobni/detail/skoda/fabia/17388873?goFrom=list' 
beatiful = urllib.request.urlopen(url).read()

soup = BeautifulSoup(beatiful, "html5lib")

#for key, value in zip(soup.findAll('th'), soup.findAll('td') ):
#    print(key.get_text() + " " + value.get_text() )


for row in soup.findAll('tr'):
    value = row.get_text()
    ok = value.find(":")
    if ok != -1:
        print(value.strip())

