import requests
import re
import sys
import os
import json


def login():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64)'
                         ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
               'X-CSRFToken': None}
    login_url = 'https://www.shanbay.com/api/v1/account/login/web/'
    s = requests.session()
    login_data = {'username': 'luokekela',
              'password': 'keepmoving',}
    try:
        s.put(login_url, data=login_data, headers=headers)
        return s
    except requests.exceptions.RequestException as e:
        print(e)


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


def get_book(book_id, s=None, local_path='D:\\Dropbox\\Python\\Words\\Books', url=None):
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










