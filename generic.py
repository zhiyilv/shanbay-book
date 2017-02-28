import imdb
import shanbay
import sys
import json
import os
import myparser


book_name = '苍穹浩瀚 第一季 The Expanse Season 1'
url_douban = 'https://movie.douban.com/subject/25926851/'
url_imdb = 'http://www.imdb.com/title/tt3230854/episodes?season=1&ref_=tt_eps_sn_1'
book_id = 175855
shanbay_username = '...'
shanbay_password = '...'

# get poster
poster_path = '.\\Books\\{}'.format(book_name)
if 'poster.jpg' not in os.listdir(poster_path):
    imdb.get_poster(url_douban, poster_path)

# get details of episodes
season, episode_title, episode_description = imdb.get_titles_synopsis(url_imdb)
season_length = len(episode_title)

# create wordlists
connection = shanbay.login(shanbay_username, shanbay_password)
wordlist_ids, _, _ = shanbay.get_wordlists(book_id, connection)
if len(wordlist_ids) != season_length:
    for i in range(season_length):
        t = 'S{}E{}. {}'.format(season, str(i+1).zfill(2), episode_title[i])
        shanbay.create_list(book_id, t, episode_description[i], connection)
    # verify all lists created successfully
    wordlist_ids, _, _ = shanbay.get_wordlists(book_id, connection)
    if len(wordlist_ids) != season_length:
        print('XXXXXXXXXXXXXXXXXXXX')
        print('Something goes wrong. Manually have a check.')
        sys.exit(-1)







