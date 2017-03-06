import string
import enchant
# from enchant.tokenize import get_tokenizer
from nltk.stem.wordnet import WordNetLemmatizer
import os
import json


def get_words_from_ass(path):
    with open(path, 'r', encoding='utf-16-le') as f:
        extracted = []
        for line in f:
            if line.startswith('Dialogue'):
                seg = line[line.rfind('}')+1:len(line)-1].lower()
                seg = ''.join([i for i in seg if i == ' ' or i in string.ascii_lowercase])
                pieces = seg.split(' ')
                for piece in pieces:
                    if piece not in extracted:
                        extracted.append(piece)
    return extracted


# using enchant to exclude non-words
def get_words_from_ass_2(path, codec='utf-16-le'):
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


def get_book_local(book_name, subtitle_path, codec='utf-8'):
    """
    get the vocabulary of a book locally from a list of ass files
    :param book_name:
    :param subtitle_path:
    :param codec:
    :return:
    """
    obsolete = []
    exclusion_path = '.\Books\Exclusion'
    for d in os.listdir(exclusion_path):
        with open(os.path.join(exclusion_path, d), 'r') as f:
            obsolete += json.load(f)
    obsolete = set(obsolete)
    print('Got {} obsolete words from {}'.format(len(obsolete), exclusion_path))

    # if subtitle path is not provided, use default dropbox directory
    # if not subtitle_path:
    #     dropbox_info_path = os.path.join(os.environ['LOCALAPPDATA'], 'Dropbox\info.json')
    #     with open(dropbox_info_path, 'r') as f:
    #         d_info = json.load(f)
    #     subtitle_path = os.path.join(d_info['personal']['path'], 'Others\\Subtitles\\{}'.format(book_name))
    print('The subtitle is in {}'.format(subtitle_path))

    total = set()
    book = []
    for ass in os.listdir(subtitle_path):
        temp, _ = get_words_from_ass_2(os.path.join(subtitle_path, ass), codec=codec)
        temp -= obsolete  # temp is a set of words
        temp -= total
        total = total.union(temp)
        book.append(list(temp))
        print('Added {} words from {} \n'.format(len(temp), ass))

    with open('.\\Books\\{}\\{}-local.json'.format(book_name, book_name), 'w') as f:
        json.dump(book, f)
    return book, total





