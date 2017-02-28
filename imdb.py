import re
import requests
from bs4 import BeautifulSoup as bs
from os import path, makedirs


# this is for imdb.com
def get_titles_synopsis(url):
    t = requests.get(url).text
    season = re.findall(r'&nbsp;<strong>Season (\d)<', t)[0]
    titles = re.findall(r'<strong><a href="/title/.*\n?title="(.*?)"', t)
    synopsis = re.findall(r'itemprop="description">\n*(.*?)\s*</div', t, re.DOTALL)
    synopsis = [re.sub(r'<.*?>', '', i) for i in synopsis]  # delete labels in synopsis

    # season is in format of string
    return season, titles, synopsis


# this is for douban.com
def get_poster(url, store_path='.\\'):
    """
    input the url of the movie on douban.com
    and the path to store the poster (optional)
    :param url:
    :param store_path:
    :return:
    """
    print('Getting poster url...')
    movie_page = requests.get(url).content
    posters_url = bs(movie_page, 'lxml').find('a', class_='nbgnbg')['href']
    posters_page = requests.get(posters_url).content
    poster_url = bs(posters_page, 'lxml').find('div', class_='cover').find('a')['href']
    poster_page = requests.get(poster_url).content
    pic_url = bs(poster_page, 'lxml').find('a', class_='mainphoto').find('img')['src']
    print('It is at {}'.format(pic_url))
    res = requests.get(pic_url)

    if not path.exists(store_path):
        makedirs(store_path)
    with open(path.join(store_path, 'poster.jpg'), 'wb') as f:
        f.write(res.content)

    print('The poster is stored at {}'.format(store_path))




