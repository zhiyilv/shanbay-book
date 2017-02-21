import string
import enchant
from enchant.tokenize import get_tokenizer


def get_words_from_ass(path):
    with open(path, 'r', encoding='utf-16-le') as f:
        extracted = []
        for line in f:
            if line.startswith('Dialogue'):
                seg = line[line.rfind('}')+1:len(line)-1].lower()
                seg = ''.join([i for i in seg if i==' ' or i in string.ascii_lowercase])
                pieces = seg.split(' ')
                for piece in pieces:
                    if piece not in extracted:
                        extracted.append(piece)
    return extracted


def get_words_from_ass_2(path):
    with open(path, 'r', encoding='utf-16-le') as f:
        extracted = []
        for line in f:
            if line.startswith('Dialogue'):
                seg = line[line.rfind('}') + 1:len(line) - 1].lower()
                seg = ''.join([i for i in seg if i == ' ' or i in string.ascii_lowercase])
                pieces = seg.split(' ')
                for piece in pieces:
                    if piece not in extracted:
                        extracted.append(piece)
    return extracted


def split_words(str, t=None):
    if not t:
        t = get_tokenizer('en_US')