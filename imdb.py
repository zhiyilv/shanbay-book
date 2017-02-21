import re
import requests


def get_titles_synopsis(url):
    t = requests.get(url).text
    season = re.findall(r'&nbsp;<strong>Season (\d)<', t)
    titles = re.findall(r'<strong><a href="/title/.*\n?title="(.*?)"', t)
    synopsis = re.findall(r'itemprop="description">\n*(.*?)\s*</div', t, re.DOTALL)
    synopsis = [re.sub(r'<.*?>', '', i) for i in synopsis]  # delete labels in synopsis

    # season is in format of string
    return season, titles, synopsis

