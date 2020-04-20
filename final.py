from bs4 import BeautifulSoup
import requests
import json
import secrets 
import time
import sqlite3 
import random
from decimal import Decimal


HOTELS_URL = 'https://www.latlong.net/category/hotels-236-57.html'
BASE_URL = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
CACHE_DICT = {}
CACHE_FILE_NAME = 'cache.json'
API_KEY = secrets.API_KEY



#--------Scraping a web page and store data into sqlite--------#
 
def get_hotels_list(url):
    '''scraping a web page and get each hotel information into a list.

    Parameters
    ----------
    url: string
        the url we are going to scrape.
    
    Returns
    -------
    list
        all the hotel stored in a list.
    '''
    #cache
    CACHE_DICT = load_cache()
    url_text = make_url_request_using_cache(url, CACHE_DICT)

    hotels_list = []
    soup = BeautifulSoup(url_text, 'html.parser')
    hotels = soup.find_all("tr")[1:]
    
    for hotel in hotels:
        title = hotel.find('a')['title']
        hotel_name = title.split(',')[0].strip()
        hotel_city = title.split(',')[1].strip()
        hotel_state = title.split(',')[2].strip()
        latitude = hotel.find_all('td')[1].string
        longitude = hotel.find_all('td')[2].string
        hotels_list.append((hotel_name, hotel_city, hotel_state, latitude, longitude))

    return hotels_list


def insert_hotels_database(hotels_list):
    '''insert hotel attribute into sqlite database.

    Parameters
    ----------
    hotels_list: list
        the list with all hotel info
    
    Returns
    -------
    None

    '''

    connection = sqlite3.connect("Final_Project.db")
    cursor = connection.cursor()
    i = 1
    for hotel in hotels_list:
        query = f'''INSERT INTO Hotels (Id, HotelName, HotelCity, HotelState, Latitude, Longitude)
        VALUES ({i}, "{hotel[0]}", "{hotel[1]}", "{hotel[2]}", "{hotel[3]}", "{hotel[4]}")
        '''
        cursor.execute(query)
        i += 1
        connection.commit()
    connection.close()
        

#--------Request from Yelp Api and store data into sqlite-------#

def get_nearby_restaurants(hotel_id):
    '''with specific hotel id get 20 nearby restaurants from yelp api.

    Parameters
    ----------
    hotels_id: int
        the id of the hotel
    
    Returns
    -------
    dict:
        the dict type of returned data.
    '''
    
    connection = sqlite3.connect("Final_Project.db")
    cursor = connection.cursor()
    lat = Decimal(cursor.execute(f'SELECT * FROM Hotels WHERE Id={hotel_id}').fetchall()[0][-2])
    log = Decimal(cursor.execute(f'SELECT * FROM Hotels WHERE Id={hotel_id}').fetchall()[0][-1])
    connection.close()

    resource_url = BASE_URL + SEARCH_PATH
    headers = {'Authorization': 'Bearer %s' % API_KEY}
    params = {
        'term' : 'restaurants',
        'latitude' : lat,
        'longitude' : log,
        'sort_by' : 'best_match'
    }
    response = requests.get(resource_url, headers=headers, params=params)
    return response.json()



def load_cache():
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache


def save_cache(cache):
    cache_file = open(CACHE_FILE_NAME, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()

def make_url_request_using_cache(url, cache):
    if (url in cache.keys()): 
        print("Using cache")
        return cache[url]
    else:
        print("Fetching")
        time.sleep(1)
        response = requests.get(url)
        cache[url] = response.text
        save_cache(cache)
        return cache[url]



def insert_restaurants_database(id):
    '''insert restaurants attribute into sqlite database with specific hotel id.

    Parameters
    ----------
    hotels_id: int
        the id of the hotel
    
    Returns
    -------
    None

    '''
    rest_dict = get_nearby_restaurants(id)
    connection = sqlite3.connect("Final_Project.db")
    cursor = connection.cursor()
    i = 1
    for rest in rest_dict['businesses']:
        name = rest['name']
        hotel_id = id
        rating = rest['rating'] if 'rating' in rest else 'unclear'
        price = rest['price'] if 'price' in rest else 'unclear'
        dist = rest['distance'] if 'distance' in rest else 'unclear'
        link = rest['url'] if 'url' in rest else 'unclear'
        query = f'''INSERT INTO Restaurants (Id, Name, HotelId, Rating, AvgPrice, Distance, Link)
        VALUES ({i}, "{name}", {hotel_id}, "{rating}", "{price}", "{dist}", "{link}")
        '''
        cursor.execute(query)
        i += 1
        connection.commit()
    connection.close()





if __name__ == "__main__":
    #data part

    hotels_list = get_hotels_list(HOTELS_URL)
    insert_hotels_database(hotels_list)
    for i in range(1, len(hotels_list) + 1):
        insert_restaurants_database(i)
    
    #presentation part still in process
