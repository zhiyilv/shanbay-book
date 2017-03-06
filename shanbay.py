import requests
import re
import sys
import os
import json
import itertools
from bs4 import BeautifulSoup as BS
import configparser
# from selenium import webdriver


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
    if r.status_code == 200:
        print('login successful')
        return s
    else:
        print('failed logging in, check manually')
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








