import requests
import re
import sys
import os
import json
import itertools
from bs4 import BeautifulSoup as BS
import configparser
import enchant
from nltk.stem.wordnet import WordNetLemmatizer
import string


class MyBook:
    def __init__(self, book_name, connection=None):
        self.name = book_name
        config_all = configparser.ConfigParser()
        config_all.read('config.ini', encoding='utf8')
        if book_name not in config_all:
            self.config = dict()
            print('There is no book called {} in config.ini, setup?'.format(book_name))
            if input('y to proceed, others to quit') == 'y':
                for key in config_all['example'].keys():  # for all valid keys, ask the input
                    self.config[key] = input('{}: '.format(key))
        else:
            self.config = dict(config_all[book_name])
        self.folder_dir = '.\\Books\\{}\\'.format(self.name)
        self.poster_dir = '.\\Books\\{}\\poster.jpg'.format(self.name)
        self.local_dir = '.\\Books\\{}\\{}-local.json'.format(self.name, self.name)
        self.online_dir = '.\\Books\\{}\\{}.json'.format(self.name, self.name)
        self.connection = connection
        self.online_url = 'https://www.shanbay.com/wordbook/{}/'.format(self.config['book_id'])  # update when necessary

    def save_config(self):
        config_all = configparser.ConfigParser()
        config_all.read('config.ini', encoding='utf8')
        config_all[self.name] = {}
        for key in self.config:
            config_all[self.name][key] = self.config[key]
        with open('config.ini', 'w', encoding='utf8') as f:
            config_all.write(f)

    def update_config(self, key, val):
        self.config[key] = val
        if key == 'book_id':
            self.online_url = 'https://www.shanbay.com/wordbook/{}/'.format(self.config['book_id'])

    def show_config(self):
        for key in self.config:
            print('{}: {}'.format(key, self.config[key]))

    def create_folder(self):
        if not os.path.exists(self.folder_dir):
            os.makedirs(self.folder_dir)

    def fetch_poster(self, force=False):
        if not force and os.path.exists(self.poster_dir):
            print('Poster already exists. It is at {}.'.format(self.poster_dir))
        else:
            url = self.config['url_douban']
            print('Getting poster url...')
            movie_page = requests.get(url).content
            posters_url = BS(movie_page, 'lxml').find('a', class_='nbgnbg')['href']
            posters_page = requests.get(posters_url).content
            poster_url = BS(posters_page, 'lxml').find('div', class_='cover').find('a')['href']
            poster_page = requests.get(poster_url).content
            pic_url = BS(poster_page, 'lxml').find('a', class_='mainphoto').find('img')['src']
            print('It is at {}'.format(pic_url))
            res = requests.get(pic_url)

            self.create_folder()
            with open(self.poster_dir, 'wb') as f:
                f.write(res.content)
            print('Poster is saved at {}.'.format(self.poster_dir))

    def connect_shanbay(self):
        if not self.connection:
            self.connection = login(self.config['shanbay_usr'], self.config['shanbay_psw'])
            if not self.connection:
                print('exit')
                return None

    def fetch_online(self, force=False):
        if not force and os.path.exists(self.online_dir):  # not forced to update, read locally
            print('The book: {} is already saved. Read from local file...'.format(self.name))
            with open(self.online_dir, 'r') as f:
                book = json.load(f)
            vocabulary = set(itertools.chain(*book))
            print('It contains {} word lists and {} words.'.format(len(book), len(vocabulary)))
            return book, vocabulary
        else:  # no local file, fetch from shanbay.com
            print('\n----fetching the book: {}, id: {} from shanbay.com----'.format(self.name, self.config['book_id']))
            self.connect_shanbay()
            book_soup = BS(self.connection.get(self.online_url).content, 'lxml')
            book = []
            book_chapters = book_soup.find_all('td', class_='wordbook-wordlist-name')  # containers of wordlists
            print('\nThere are {} word lists:'.format(len(book_chapters)))
            for i in book_chapters:
                print(i.a.string)

            print('\nDealing with them:')
            for i in book_chapters:
                wordlist = []
                print('doing with wordlist: {} ...'.format(i.a.string))
                wordlist_url = 'https://www.shanbay.com{}'.format(i.a.get('href'))
                try:
                    first_page_soup = BS(self.connection.get(wordlist_url).content, 'lxml')
                except requests.exceptions.RequestException as e:
                    print(e)
                    exit(1)
                wordlist += [tr.td.string for tr in first_page_soup.find_all('tr', class_='row')]

                # deal with other sub-pages, avoid reading the pagination
                for page_count in range(2, 1000):
                    url_update = wordlist_url + '?page={}'.format(page_count)
                    page_soup = BS(self.connection.get(url_update).content, 'lxml')
                    temp = [tr.td.string for tr in page_soup.find_all('tr', class_='row')]
                    if temp:  # until no more words
                        wordlist += temp
                    else:
                        break
                book.append(wordlist)
                print('added {} words into the vocabulary\n'.format(len(wordlist)))
            print('******finished**********')

            # save the book
            vocabulary = set(itertools.chain(*book))
            with open(self.online_dir, 'w') as f:
                json.dump(book, f)
            print('The book is saved at {}.'.format(self.online_dir))
            print('It contains {} word lists and {} words.'.format(len(book), len(vocabulary)))
            return book, vocabulary

    def get_local(self, force=False):
        if not force and os.path.exists(self.local_dir):  # not forced to update, read locally
            print('The book: {} is already generated. Read from local file...'.format(self.name))
            with open(self.local_dir, 'r') as f:
                book = json.load(f)
            vocabulary = set(itertools.chain(*book))
            print('It contains {} word lists and {} words.'.format(len(book), len(vocabulary)))
            return book, vocabulary
        else:
            obsolete = []
            exclusion_path = '.\\Books\\Exclusion'
            for d in os.listdir(exclusion_path):
                with open(os.path.join(exclusion_path, d), 'r') as f:
                    obsolete += json.load(f)  # these books are just stored as a list of words
            obsolete = set(obsolete)
            print('Preparation: got {} obsolete words from {}'.format(len(obsolete), exclusion_path))

            print('\n----Generating the book: {}, from subtitles in----{}'.format(self.name,
                                                                                  self.config['subtitle_path']))
            files = os.listdir(self.config['subtitle_path'])
            files.sort(key=lambda x: x[len(self.config['subtitle_start']): len(self.config['subtitle_start'])+2])
            print('There are {} subtitles:'.format(len(files)))
            for ass in files:
                print(ass)

            print('\ndealing with them:')
            vocabulary = set()
            book = []
            for ass in files:
                print('doing with subtitle: {} ...'.format(ass))
                temp, _ = get_words_from_ass(os.path.join(self.config['subtitle_path'], ass),
                                             codec=self.config['subtitle_codec'])
                temp -= obsolete  # temp is a set of words
                temp -= vocabulary
                vocabulary = vocabulary.union(temp)
                book.append(list(temp))
                print('added {} words into the vocabulary \n'.format(len(temp)))
            print('******finished**********')

            # save the book
            with open(self.local_dir, 'w') as f:
                json.dump(book, f)
            print('The book is saved at {}.'.format(self.local_dir))
            print('It contains {} word lists and {} words.'.format(len(book), len(vocabulary)))
            return book, vocabulary

    def get_chapter_details(self):
        t = requests.get(self.config['url_imdb']).text
        season = re.findall(r'&nbsp;<strong>Season (\d)<', t)[0]

        titles = re.findall(r'<strong><a href="/title/.*\n?title="(.*?)"', t)
        titles = ['S{}E{}. {}'.format(season, str(i).zfill(2), titles[i]) for i in range(len(titles))]

        synopsis = re.findall(r'itemprop="description">\n*(.*?)\s*</div', t, re.DOTALL)
        synopsis = [re.sub(r'<.*?>', '', i) for i in synopsis]  # delete labels in synopsis

        return season, titles, synopsis

    def setup_wordlist(self, title, synopsis):
        self.connect_shanbay()
        self.connection.headers['Referer'] = 'https://www.shanbay.com/wordbook/{}/'.format(self.config['book_id'])
        url = 'https://www.shanbay.com/api/v1/wordbook/wordlist/'

        wordlist_data = {'name': title,
                         'description': synopsis,
                         'wordbook_id': int(self.config['book_id']), }
        try:
            self.connection.post(url, data=wordlist_data)
            print('successfully created wordlist: {}'.format(title))
            print(synopsis)
            return 1
        except requests.exceptions.RequestException as e:
            print(e)
            return -1

    def fetch_online_wordlists(self):
        self.connect_shanbay()
        book_soup = BS(self.connection.get(self.online_url).content, 'lxml')
        existing_chapters = book_soup.find_all('td', class_='wordbook-wordlist-name')
        return [i.a.string for i in existing_chapters], [i.a.get('href') for i in existing_chapters]

    def setup_book(self):
        _, titles, synopsis = self.get_chapter_details()  # prepare wordlists
        existing_chapters, _ = self.fetch_online_wordlists()

        if existing_chapters:
            print('There are already {} word lists:'.format(len(existing_chapters)))
        for i in existing_chapters:
            print(i)

        for t, s in zip(titles, synopsis):
            if t not in existing_chapters:
                self.setup_wordlist(t, s)

        existing_chapters, urls = self.fetch_online_wordlists()

        if len(existing_chapters) == len(titles):
            print('\n*********The wordbook is all set*************')
        else:
            print('XXXXXXXXXXXXXXXXXXXX')
            print('Something goes wrong. Manually have a check. Returning existing wordlists')

        return existing_chapters, urls

    def upload(self):
        book, vocabulary = self.get_local()
        titles, urls = self.setup_book()
        if len(book) != len(urls):
            print('Word lists not match, please check manually.')
            return 0

        for chapter, title, wordlist_url in zip(book, titles, urls):
            print('dealing with {}'.format(title))
            wordlist_url = 'https://www.shanbay.com{}'.format(wordlist_url)
            for word in chapter:
                word_data = {'id': int(wordlist_url.split('/')[-2]),
                             'word': word}
            try:
                self.connection.post(wordlist_url, data=word_data)
            except requests.exceptions.RequestException as e:
                print(e)
                return -1

            print('added {} words into {}'.format(len(chapter), title))
        print('\n*************Finished uploading****************')


def login(usr=None, psw=None):
    s = requests.session()
    s.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ' \
                              'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
    s.headers['Origin'] = 'https://shanbay.com'
    s.headers['Referer'] = 'https://shanbay.com/web/account/login'

    #     s.get('https://www.shanbay.com/web/account/login')
    # headers = {'Origin': 'https://www.shanbay.com',
    #            'X-CSRFToken': None,
    #            'Content-type': 'application/json;charset=UTF-8',
    #            'Referer': 'https://www.shanbay.com/web/account/login',
    #            }
    login_url = 'https://www.shanbay.com/api/v1/account/login/web/'
    if not usr:
        usr = input('your user name: ')
    if not psw:
        psw = input('your password: ')

    login_data = {'username': usr,
              'password': psw,}
    r = s.put(login_url, data=login_data)
    if s.cookies.get('captcha_needed') != 'True':
        print('login successful')
        return s
    else:
        print('need to input captcha, try other ways')
        return None


def get_wordlists(book_id, shanbay_session=None, require_description=False):
    """
    given a book id, return its details of its wordlists
    :param book_id:
    :param shanbay_session:
    :param require_description:
    :return: ids, titles, descriptions
    """
    book_url = 'https://www.shanbay.com/wordbook/{}/'.format(book_id)
    if not shanbay_session:
        shanbay_session = login()

    book_page = shanbay_session.get(book_url).text
    ids = re.findall(r'wordbook-wordlist-name">\n*\s*<a href="/wordlist/\d*/(\d*?)/">', book_page)
    titles = re.findall(r'wordbook-wordlist-name">\n*\s*<a href="/wordlist/\d*/\d*/">(.*?)<', book_page)
    descriptions = []

    if require_description:
        for i in ids:
            url = 'https://www.shanbay.com/wordlist/{}/{}/'.format(book_id, i)
            page = shanbay_session.get(url).text
            description = re.findall(r'wordlist-description-container">\n?\s*(.*?)\n\s*</div', page)
            if description:
                descriptions.append(description[0])
            else:
                descriptions.append('')

    return ids, titles, descriptions


def get_book(book_id, s=None, local_path='.\\Books', url=None):
    """
    given a url of book on shanbay.com, automatically save the book in format of json
    if the book exists locally, load it
    :param book_id:
    :param s:
    :param local_path:
    :param url:
    :return: book name, word lists details, vocabulary
    """

    if not url:
        url = 'https://www.shanbay.com/wordbook/{}/'.format(book_id)
    if not s:
        s = login()
    print('Fetching book from shanbay.com...')
    try:
        book_page = s.get(url).text
        url_local = url[url.find('.com')+4:]
        book_name = re.findall(r'<div class="wordbook-title".*\n?\s*<a href="{}">(.*?)<'
                               .format(url_local), book_page)
        if not book_name:
            print('Didn\'t find the book, check the url and try again')
            sys.exit(-1)
        book_name = book_name[0]
        print('Book name:  ' + book_name)
    except requests.exceptions.RequestException as e:
        print(e)
        exit(0)

    # book exists alreay
    local_path = os.path.join(local_path, book_name)
    if not os.path.exists(local_path):
        os.makedirs(local_path)
    book_file = book_name + '.json'
    if book_file in os.listdir(local_path):
        print('It is already saved. Read from local file')
        with open(os.path.join(local_path, book_file), 'r') as f:
            v = json.load(f)
            return book_name, None, v

    # get book from shanbay
    wordlist_ids, wordlist_titles, _ = get_wordlists(book_id, s)
    print('\nThere are {} word lists:'.format(len(wordlist_ids)))
    for i in wordlist_ids:
        print(i)

    print('\n-------main process----------')
    vocabulary = []
    wordlist_descriptions = []  # a list of [wordlist_title, wordlist_description]
    for i in wordlist_ids:
        count_pin = len(vocabulary)
        print('doing with wordlist {} ...'.format(i))
        wordlist_url = 'https://www.shanbay.com/wordlist/{}/{}/'.format(book_id, i)
        try:
            wordlist_first_page = s.get(wordlist_url).text
        except requests.exceptions.RequestException as e:
            print(e)
            sys.exit(1)

        # wordlist_title = re.findall(r'<h4>\n?\s*"(.*?)\n', wordlist_first_page)
        description = re.findall(r'wordlist-description-container">\n?\s*(.*?)\n\s*</div', wordlist_first_page)
        if description:
            wordlist_descriptions.append(description[0])
        else:
            wordlist_descriptions.append('')
        vocabulary += re.findall(r'<td class="span2"><strong>(.*?)</strong>', wordlist_first_page)

        for page_count in range(2, 1000):
            url_update = wordlist_url + '?page={}'.format(page_count)
            temp = re.findall(r'<td class="span2"><strong>(.*?)</strong>', s.get(url_update).text)
            if temp:
                vocabulary += temp
            else:
                break
        print('added {} words into the vocabulary\n'.format(len(vocabulary)-count_pin))

    print('******finished**********')

    # save the book
    with open(os.path.join(local_path, book_file), 'w') as f:
        json.dump(vocabulary, f)
    return book_name, list(zip(wordlist_ids, wordlist_titles, wordlist_descriptions)), vocabulary


def get_book2(book_id, s=None, local_path='.\\Books', url=None):
    """
    given a url of book on shanbay.com, automatically save the book in format of json
    if the book exists locally, load it
    separate wordlists
    :param book_id:
    :param s:
    :param local_path:
    :param url:
    :return: book name, word lists details, vocabulary
    """

    if not url:
        url = 'https://www.shanbay.com/wordbook/{}/'.format(book_id)
    if not s:
        s = login()
    print('Fetching book from shanbay.com...')
    try:
        book_page = s.get(url).text
        url_local = url[url.find('.com')+4:]
        book_name = re.findall(r'<div class="wordbook-title".*\n?\s*<a href="{}">(.*?)<'
                               .format(url_local), book_page)
        if not book_name:
            print('Didn\'t find the book, check the url and try again')
            sys.exit(-1)
        book_name = book_name[0]
        print('Book name:  ' + book_name)
    except requests.exceptions.RequestException as e:
        print(e)
        exit(0)

    # book exists alreay
    local_path = os.path.join(local_path, book_name)  # book folder
    if not os.path.exists(local_path):
        os.makedirs(local_path)
    book_file = book_name + '.json'
    if book_file in os.listdir(local_path):
        print('It is already saved. Read from local file')
        with open(os.path.join(local_path, book_file), 'r') as f:
            v = json.load(f)
            print('It contains {} wordlists.'.format(len(v)))
            return book_name, None, v

    # get book from shanbay
    wordlist_ids, wordlist_titles, _ = get_wordlists(book_id, s)
    print('\nThere are {} word lists:'.format(len(wordlist_ids)))
    for i in wordlist_ids:
        print(i)

    print('\n-------main process----------')
    vocabulary = []
    wordlist_descriptions = []  # a list of [wordlist_title, wordlist_description]
    for i in wordlist_ids:
        wordlist = []
        print('doing with wordlist {} ...'.format(i))
        wordlist_url = 'https://www.shanbay.com/wordlist/{}/{}/'.format(book_id, i)
        try:
            wordlist_first_page = s.get(wordlist_url).text
        except requests.exceptions.RequestException as e:
            print(e)
            sys.exit(1)

        # wordlist_title = re.findall(r'<h4>\n?\s*"(.*?)\n', wordlist_first_page)
        description = re.findall(r'wordlist-description-container">\n?\s*(.*?)\n\s*</div', wordlist_first_page)
        if description:
            wordlist_descriptions.append(description[0])
        else:
            wordlist_descriptions.append('')
        wordlist += re.findall(r'<td class="span2"><strong>(.*?)</strong>', wordlist_first_page)

        # deal with other subpages, avoid reading the pagination
        for page_count in range(2, 1000):
            url_update = wordlist_url + '?page={}'.format(page_count)
            temp = re.findall(r'<td class="span2"><strong>(.*?)</strong>', s.get(url_update).text)
            if temp:
                wordlist += temp
            else:
                break
        vocabulary.append(wordlist)
        print('added {} words into the vocabulary\n'.format(len(wordlist)))

    print('******finished**********')

    # save the book
    with open(os.path.join(local_path, book_file), 'w') as f:
        json.dump(vocabulary, f)
    return book_name, list(zip(wordlist_ids, wordlist_titles, wordlist_descriptions)), vocabulary


def create_list(book_id, name, description, s=None):
    if not s:
        s = login()
    s.headers['Referer'] = 'https://www.shanbay.com/wordbook/{}/'.format(book_id)
    url = 'https://www.shanbay.com/api/v1/wordbook/wordlist/'

    wordlist_data = {'name': name,
            'description': description,
            'wordbook_id': book_id,}
    try:
        s.post(url, data=wordlist_data, headers=s.headers)
        print('successfully created wordlist:')
        print(name)
        print(description)
        return 1
    except requests.exceptions.RequestException as e:
        print(e)
        return 0


def add_word(wordlist_id, word, s=None):
    if not s:
        s = login()
    # s.headers['Referer'] = 'https://www.shanbay.com/wordlist/{}/{}/'.format(book_id, wordlist_id)
    url = 'https://www.shanbay.com/api/v1/wordlist/vocabulary/'
    word_data = {'id': wordlist_id,
                 'word': word}

    try:
        s.post(url, data=word_data)
    except requests.exceptions.RequestException as e:
        print(e)
        return 0


# def update_dumb2(book_id, local_total, s=None):
#     """
#     after manually deleting some words, compare the online version with local version
#     add those dumb words into the dumb file
#     :param book_id:
#     :param local_total: should be a set
#     :param s:
#     :return:
#     """
#     dumb_path = '.\\Books\\Exclusion\\dumb.json'
#     if os.path.exists(dumb_path):
#         with open(dumb_path, 'r') as f:
#             dumb = json.load(f)
#             dumb = set(dumb)
#     else:
#         dumb = set()
#
#     _, _, v = get_book(book_id, s=s)
#     v = set(v)
#     print('There are {} words online'.format(len(v)))
#     dumb_ext = local_total - v
#     print('Found {} words are dumb'.format(len(dumb_ext)))
#     print(dumb_ext)
#     dumb = dumb.union(dumb_ext)
#
#     dumb = list(dumb)
#     with open(dumb_path, 'w') as f:
#         json.dump(dumb, f)
#     print('Added them into local dumb words')


def get_dumb(book_name):
    """
    make sure both online and local version of word book is stored correctly
    :param book_name:
    :return:
    """
    with open('.\\Books\\{}\\{}.json'.format(book_name, book_name), 'r') as f:
        book_online = json.load(f)
        book_online = set(itertools.chain(*book_online))
    with open('.\\Books\\{}\\{}-local.json'.format(book_name, book_name), 'r') as f:
        book_local = json.load(f)
        book_local = set(itertools.chain(*book_local))
    d = book_local - book_online
    print('There are {} words online and {} words locally, got {} dumb words.'
          .format(len(book_online), len(book_local), len(d)))
    return d


def update_dumb(dumb_ext):
    """
    given a dumb extension, update the local dumb file
    :param dumb_ext:
    :return:
    """
    dumb_path = '.\\Books\\Exclusion\\dumb.json'
    if os.path.exists(dumb_path):
        with open(dumb_path, 'r') as f:
            dumb = json.load(f)
            dumb = set(dumb)
    else:
        dumb = set()

    dumb = dumb.union(dumb_ext)
    with open(dumb_path, 'w') as f:
        json.dump(list(dumb), f)
    print('Added {} words into local dumb file.'.format(len(dumb_ext)))
    print('There are {} dumb words in total'.format(len(dumb)))
    return dumb


def fetch_book_by_id(book_id, s=None, local_path=None):
    """
    provide a book id, get the book from shanbay.com
    separated by wordlists
    :param book_id:
    :param s:
    :param local_path:
    :return: book(chapter separated), vocabulary(a set of words)
    """
    url = 'https://www.shanbay.com/wordbook/{}/'.format(book_id)
    if not s:
        s = login()

    print('Fetching book from shanbay.com...')
    try:
        book_soup = BS(s.get(url).content, 'lxml')
        book_name = book_soup.find('div', class_='wordbook-title').a.string
        if not book_name:
            print('Didn\'t find the book, check the url and try again')
            exit(-1)
        print('Book name:  ' + book_name)
    except requests.exceptions.RequestException as e:
        print(e)
        exit(0)

    # book exists alreay
    if not local_path:
        local_path = '.\\Books\\{}'.format(book_name)  # book folder
    if not os.path.exists(local_path):
        os.makedirs(local_path)
    book_file = book_name + '.json'
    if book_file in os.listdir(local_path):
        print('It is already saved. Read from local file...')
        with open(os.path.join(local_path, book_file), 'r') as f:
            book = json.load(f)
        vocabulary = set(itertools.chain(*book))
        print('It contains {} word lists and {} words.'.format(len(book), len(vocabulary)))
        return book, vocabulary

    # no local file, get book from shanbay
    book = []
    book_chapters = book_soup.find_all('td', class_='wordbook-wordlist-name')  # containers of wordlists
    print('\nThere are {} word lists:'.format(len(book_chapters)))
    for i in book_chapters:
        print(i.a.string)

    print('\n-------fetching----------')
    for i in book_chapters:
        wordlist = []
        print('doing with wordlist: {} ...'.format(i.a.string))
        wordlist_url = 'https://www.shanbay.com{}/'.format(i.a.get('href'))
        try:
            first_page_soup = BS(s.get(wordlist_url).content, 'lxml')
        except requests.exceptions.RequestException as e:
            print(e)
            exit(1)
        wordlist += [tr.td.string for tr in first_page_soup.find_all('tr', class_='row')]

        # deal with other subpages, avoid reading the pagination
        for page_count in range(2, 1000):
            url_update = wordlist_url + '?page={}'.format(page_count)
            page_soup = BS(s.get(url_update).content, 'lxml')
            temp = [tr.td.string for tr in page_soup.find_all('tr', class_='row')]
            if temp:  # until no more words
                wordlist += temp
            else:
                break
        book.append(wordlist)
        print('added {} words into the vocabulary\n'.format(len(wordlist)))

    print('******finished**********')

    # save the book
    vocabulary = set(itertools.chain(*book))
    with open(os.path.join(local_path, book_file), 'w') as f:
        json.dump(book, f)
        print('The book is saved at {}.'.format(local_path))
        print('It contains {} word lists and {} words.'.format(len(book), len(vocabulary)))
    return book, set(itertools.chain(*book))


def get_words_from_ass(path, codec='utf-16-le'):
    with open(path, 'r', encoding=codec) as f:
        d = enchant.Dict('en_US')  # to check words
        lmtzr = WordNetLemmatizer()  # transform words to the basic form
        extracted = set()
        notword = set()
        for line in f:
            if line.startswith('Dialogue'):
                seg = line[line.rfind('}') + 1:len(line) - 1].lower()
                # seg = ''.join([i for i in seg if i == ' ' or i in string.ascii_lowercase])
                # accept ', e.g. i'm
                seg = ''.join([i for i in seg if i == ' ' or i in string.ascii_lowercase])
                pieces = seg.split(' ')
                for piece in pieces:
                    # if piece != '':
                    # only consider words at least 3 characters
                    if len(piece) > 2:
                        word1 = lmtzr.lemmatize(piece)  # for noun.
                        if piece != word1:  # got the basic form
                            w = word1
                        else:  # maybe it's a verb, or just not a word
                            w = lmtzr.lemmatize(piece, 'v')  # if not a word, w is piece itself
                        if d.check(w):
                            extracted.add(w)
                        else:
                            notword.add(w)
    return extracted, notword





