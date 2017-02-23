import imdb
import shanbay
import sys
import json
import os
import myparser


# get details from imdb
season = 2
url_s2 = 'http://www.imdb.com/title/tt0903747/episodes?season={}'.format(season)
_, episode_title, episode_description = imdb.get_titles_synopsis(url_s2)
season_length = len(episode_title)

# create wordlists
connection = shanbay.login()
book_id = 174418
wordlist_ids, _, _ = shanbay.get_wordlists(book_id, connection)
if len(wordlist_ids) != season_length:
    for i in range(season_length):
        t = 'S{}E'.format(season) + str(i+1).zfill(2) + '. ' + episode_title[i]
        shanbay.create_list(book_id, t, episode_description[i], connection)
    # verify all lists created successfully
    wordlist_ids, _, _ = shanbay.get_wordlists(book_id, connection)
    if len(wordlist_ids) != season_length:
        print('XXXXXXXXXXXXXXXXXXXX')
        print('Something goes wrong. Manually have a check.')
        sys.exit(-1)

# get obsolete words
obsolete = []
exclusion_path = '.\Books\Exclusion'
for d in os.listdir(exclusion_path):
    with open(os.path.join(exclusion_path, d), 'r') as f:
        obsolete += json.load(f)
obsolete = set(obsolete)
# # get manually excluded words
# if 'manual_exclude.json' in os.listdir('.\\'):
#     with open('.\manual_exclude.json', 'r') as f:
#         manual_exclude = json.load(f)
#         manual_exclude = set(manual_exclude)
# else:
#     manual_exclude = set()

# get folder path
d_info_path = os.path.join(os.environ['LOCALAPPDATA'], 'Dropbox\info.json')
with open(d_info_path, 'r') as f:
    d_info = json.load(f)
# get words from subtitle files
folder_path = os.path.join(d_info['personal']['path'], 'Others\\Subtitles\\Breaking Bad\\S2')

total = set()
for i in range(1, season_length+1):
    file_path = os.path.join(folder_path, 'Breaking.Bad.S02E'+str(i).zfill(2)+'.720p.Bluray-clue.ass')
    temp, _ = myparser.get_words_from_ass_2(file_path)
    temp -= obsolete
    temp -= total
    # temp -= manual_exclude
    for w in temp:
        shanbay.add_word(wordlist_id=wordlist_ids[i-1], word=w, s=connection)
    total = total.union(temp)

# store book
book_name = '绝命毒师 第二季.json'
book_path = '.\\Books\\'

with open(os.path.join(book_path, book_name), 'w') as f:
    json.dump(list(total), f)

