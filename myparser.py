import string
import enchant
# from enchant.tokenize import get_tokenizer
from nltk.stem.wordnet import WordNetLemmatizer


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
def get_words_from_ass_2(path):
    with open(path, 'r', encoding='utf-16-le') as f:
        d = enchant.Dict('en_US')  # to check words
        lmtzr = WordNetLemmatizer()  # transform words to the basic form
        extracted = set()
        notword = set()
        for line in f:
            if line.startswith('Dialogue'):
                seg = line[line.rfind('}') + 1:len(line) - 1].lower()
                seg = ''.join([i for i in seg if i == ' ' or i in string.ascii_lowercase])
                pieces = seg.split(' ')
                for piece in pieces:
                    if piece != '':
                        word1 = lmtzr.lemmatize(piece)  # for noun.
                        if piece != word1:
                            w = word1
                        else:
                            w = lmtzr.lemmatize(piece, 'v')  # probably not a noun.
                        if d.check(w):
                            extracted.add(w)
                        else:
                            notword.add(w)
    return extracted, notword


# def split_words(str, t=None):
#     if not t:
#         t = get_tokenizer('en_US')