import imdb
import shanbay
import sys
import json
import os
import myparser


# manually enter details here, or use initializations
book_name = '大群 Legion'
url_douban = 'https://movie.douban.com/subject/26641716/'
url_imdb = 'http://www.imdb.com/title/tt5114356/episodes?season=1&ref_=tt_eps_sn_1'
subtitle_path = 'D:\Dropbox\Others\Subtitles\Legion'
subtitle_start = 'Legion.S01E'  # for sorting subtitles
subtitle_codec = 'utf-8'
book_id = 176434

# initialization, recommended
if not book_name:
    book_name = input('The book name is: ')
if not url_douban:
    url_douban = input('The url on douban.com is: ')
if not url_imdb:
    url_imdb = input('The url on imdb.com is: ')
if not subtitle_path:
    subtitle_path = input('Subtitles are stored at: ')
if not subtitle_start:
    sub=subtitle_start = input('All subtitles should be started with: ')
if not subtitle_codec:
    subtitle_codec = input('Subtitles are encoded with: ')
if not book_id:
    book_id = int(input('Word Book id on shanbay.com is: '))

shanbay_username = input('Your shanbay username: ')
shanbay_password = input('Your shanbay password: ')

# get poster
book_path = '.\\Books\\{}'.format(book_name)
if not os.path.exists(book_path):
    os.makedirs(book_path)
if 'poster.jpg' not in os.listdir(book_path):
    imdb.get_poster(url_douban, book_path)

# get details of episodes
season, episode_title, episode_description = imdb.get_titles_synopsis(url_imdb)

season_length = len(episode_title)
season_length = 4
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

# get obsolete words
obsolete = []
exclusion_path = '.\Books\Exclusion'
for d in os.listdir(exclusion_path):
    with open(os.path.join(exclusion_path, d), 'r') as f:
        obsolete += json.load(f)
obsolete = set(obsolete)

# add words
total = set()
subtitles = os.listdir(subtitle_path)
subtitles.sort(key=lambda x: x[len(subtitle_start):len(subtitle_start)+2])
for i in range(1, season_length+1):
    file_path = os.path.join(subtitle_path, subtitles[i-1])
    temp, _ = myparser.get_words_from_ass_2(file_path, subtitle_codec)
    temp -= obsolete
    temp -= total
    for w in temp:
        shanbay.add_word(wordlist_id=wordlist_ids[i-1], word=w, s=connection)
    total = total.union(temp)
    print('added {} words into wordlist {}'.format(len(temp), episode_title[i-1]))
    print(temp)
    print('----------------------------\n')

# store locally
with open(os.path.join('.\\Books\\{}'.format(book_name), book_name+'-local.json'), 'w') as f:
    json.dump(list(total), f)

# evoke if necessary
shanbay.get_dumb(book_id, total, connection)


