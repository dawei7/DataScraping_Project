import re
import requests
from bs4 import BeautifulSoup

def url_to_soup_converter(url):
    #Some header settings to get everything in english, with US IP
    headers = {'Accept-Language': 'en','X-FORWARDED-FOR': '2.21.184.0'}
    #url request by given url paramter and soup conversion
    url_request = requests.get(url, headers=headers)
    soup = BeautifulSoup(url_request.text,features="html.parser")
    return soup

def get_name(url):
    my_soup = url_to_soup_converter(url)
    return my_soup.find_all('span',attrs={'class': 'itemprop'})[0].contents[0] #Get actors



