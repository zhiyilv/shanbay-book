import requests
import re
import sys
import os
import json
# from selenium import webdriver


# def show_cookies(s):
#     for i in s.cookies.keys():
#         print(i+': '+s.cookies[i])
#

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
    login_data = {'username': usr,
              'password': psw,}
    r = s.put(login_url, data=login_data)
    if r.status_code == 200:
        print('login successful')
        return s
    else:
        print('failed logging in, check manually')
        return None

#
# def login():
#     cl = webdriver.Chrome()
#     cl.get('https://www.shanbay.com/web/account/login/')
#     cl.find_element_by_name('username').send_keys('...')
#     cl.find_element_by_name('password').send_keys('...')
#     cl.find_element_by_css_selector('button.login-button').click()
#     return cl.get_cookies()


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
        sys.exit(0)

    # book exists alreay
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


def get_dumb(book_id, local_total, s=None):
    """
    after manually deleting some words, compare the online version with local version
    add those dumb words into the dumb file
    :param book_id:
    :param local_total:
    :param s:
    :return:
    """
    dumb_path = '.\\Books\\Exclusion\\dumb.json'
    if os.path.exists(dumb_path):
        with open(dumb_path, 'r') as f:
            dumb = json.load(f)
            dumb = set(dumb)
    else:
        dumb = set()

    _, _, v = get_book(book_id, s=s)
    v = set(v)
    print('There are {} words online'.format(len(v)))
    dumb_ext = local_total - v
    print('Found {} words are dumb'.format(len(dumb_ext)))
    print(dumb_ext)
    dumb = dumb.union(dumb_ext)

    dumb = list(dumb)
    with open(dumb_path, 'w') as f:
        json.dump(dumb, f)
    print('Added them into local dumb words')










