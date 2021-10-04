from bs4 import BeautifulSoup
import urllib.request
import re
import json
import pandas as pd

states_list = [
"New Jersey",
"New York",
]


def get_state_urls():
    state_urls = []
    base_url_string = "https://locations.kfc.com/"
    web_url = urllib.request.urlopen(base_url_string)
    data = web_url.read()
    soup = BeautifulSoup(data, 'html.parser')
    links = soup.find_all('a')
    for link in links:
        if link.string in states_list:
            state_urls.append(base_url_string + link.get('href'))
    return state_urls

def get_city_urls(state_urls):
    city_urls = []
    for state in state_urls:
        base_url_string = state
        web_url = urllib.request.urlopen(base_url_string)
        data = web_url.read()
        soup = BeautifulSoup(data, 'html.parser')
        links = soup.find_all('a',class_="Directory-listLink")
        for link in links:
            city_url = base_url_string.rsplit('/',1)[0]+'/' +link.get('href')
            city_urls.append(city_url)
    return city_urls


def read_address_list(city_url, locations):
    address_list = []
    for location in locations:
        location_url= location.find(class_="Teaser-titleLink")['href']
        location_url = location_url.rsplit('/',1)[1]
        location_url = city_url +'/' + location_url
        web_url =  urllib.request.urlopen(location_url)
        data = web_url.read()
        soup = BeautifulSoup(data, 'html.parser')
        address_list.append(read_single_address(soup))
    return address_list

def read_single_address(soup):
    hour_string = soup.find(attrs={'data-days' : True})['data-days']
    phone_number = soup.find(class_ ="Phone-link")['href']
    city = soup.find("meta", itemprop="addressLocality").get('content')
    street_address = soup.find("meta", itemprop="streetAddress").get('content')
    latitude = soup.find("meta", itemprop="latitude").get('content')
    longitude = soup.find("meta", itemprop="longitude").get('content')
    zip_code = soup.find(class_ ="c-address-postal-code").string
    if soup.find(class_ = "Core-additionalHours Text--small") is not None:
      misc_notes = soup.find(class_ = "Core-additionalHours Text--small").string
    else:
      misc_notes =""
    state = soup.find(class_ ="c-address-state").string
    single_address = {}
    single_address['street_address'] = street_address
    single_address['city'] = city
    single_address['state'] = state
    single_address['zip_code'] = zip_code
    single_address['lat'] = latitude
    single_address['lon'] = longitude
    single_address['misc_notes'] = misc_notes
    #single_address['hours'] = hour_string
    flattened = flatten_json(json.loads(hour_string))
   
    single_address['phone_number'] = re.sub("[^0-9]", "",phone_number)
    return {**single_address, **flattened}



def flatten_json(times):
    out = {}
    for time in times:
      if time:
          day = time['day']
          is_closed_key = day+'_is_closed'
          is_closed_value = time['isClosed']
          out[is_closed_key]= is_closed_value
          if not is_closed_value:
            opening_key = day + '_open'
            opening_value = time['intervals'][0]['start']
            closing_key = day + '_close'
            closing_value = time['intervals'][0]['end']
            out[opening_key] = opening_value
            out[closing_key] = closing_value
          
    return out


def get_addresses(city_urls):
    addresses = []
    for city_url in city_urls:
        web_url =  urllib.request.urlopen(city_url)
        data = web_url.read()
        soup = BeautifulSoup(data, 'html.parser')
        locations = soup.find_all(class_ = "Directory-listTeaser")
        if not locations: #must be a single location in city
            addresses.append(read_single_address(soup))
        else:
           addresses = addresses + read_address_list(city_url,locations)
    return addresses
        
            

    


def pull_kfc():
    state_urls = get_state_urls()
    city_urls = get_city_urls(state_urls)
    address_list = get_addresses(city_urls)
    address_frame = pd.DataFrame(address_list)
    address_frame.to_csv('kfcdata2.csv')

    

    

                
      
if __name__ == "__main__":
    pull_kfc()

       


if __name__ == "__main__":
    pull_kfc()