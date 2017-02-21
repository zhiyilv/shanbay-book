import imdb
import shanbay
import sys
import json
import os
import myparser
import enchant


# get details from imdb
season = 2
url_s2 = 'http://www.imdb.com/title/tt0903747/episodes?season={}'.format(season)
_, episode_title, episode_description = imdb.get_titles_synopsis(url_s2)
season_length = len(episode_title)

# create wordlists
connection = shanbay.login()
book_id = 174418
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

# get folder path
d_info_path = os.path.join(os.environ['LOCALAPPDATA'], 'Dropbox\info.json')
with open(d_info_path, 'r') as f:
    d_info = json.load(f)
# get words from subtitle files
folder_path = os.path.join(d_info['personal']['path'], 'Others\\Subtitles\\Breaking Bad\\S2')
for i in range(1, season_length+1):
    file_path = os.path.join(folder_path, 'Breaking.Bad.S02E'+str(i).zfill(2)+'.720p.Bluray-clue.ass')
    temp = myparser.get_words_from_ass(file_path)




# main operations
full = []
obsolete = []
count = 0
total = 0
for file_name in file_list:
    count = 0
    print('These are words form \n'+file_name)
    current = get_words_from_ass(os.path.join(file_path, file_name))
    for i in current:
        if (i not in full) and (i not in obsolete):
            if (i in lv4) or (i in lv6):
                obsolete.append(i)
            else:
                full.append(i)
                total += 1
                count += 1
                print(i+'      current ep {} and totally {}'.format(count, total))
    print('======================================')
    print('\n\n')




