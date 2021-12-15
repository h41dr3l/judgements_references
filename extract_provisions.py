import spacy 
import en_core_web_sm
from spacy.matcher import Matcher
from spacy.util import DummyTokenizer
from spacy.matcher import PhraseMatcher

class TokenizerWithFormatting(DummyTokenizer):
    # https://github.com/explosion/spaCy/issues/4160
    # https://github.com/explosion/spaCy/issues/5698
    def __init__(self, nlp):
        self.vocab = nlp.vocab
        self.tokenizer = nlp.tokenizer
        
        self.orph_paren_matcher = Matcher(self.vocab)
        pattern = [{'TEXT': {'REGEX': r'.\([^\(\)]+$'}}, {'ORTH': ')'}] # e.g. SLR(R ) and 8(b)(i ) 
        self.orph_paren_matcher.add('OrphanedParenthesis', [pattern])

    def __call__(self, text):
        doc = self.tokenizer(text)
        matches = self.orph_paren_matcher(doc)
        with doc.retokenize() as retokenizer:
            for _, start, end in matches:
                retokenizer.merge(doc[start:end]) # SLR(R ) => SLR(R)
        return doc

def num_pos_tagger(doc):
    for token in doc:
        for ch in token.text:
            if ch.isdigit():
                token.pos_ = 'NUM'
                break
    return doc

def get_text(filename):
    with open(filename, 'r') as f:
        test = f.read().replace('\n', ' ')#.split('.')[:-1]
    return test

#gets the list of titles and code of a statute 
titles = []
codes = []
with open('legis_name.txt', 'r') as f:
    text = f.read()
    statutes = text.split('\n')[1:-1]
    for item in statutes:
        item = item.split(',')
        title = item[0].strip()
        shorthand = item[1].strip()
        index = 0
        for i in range(len(shorthand)):
            if shorthand[i].isdigit():
                index = i
                break
        statute_code = shorthand[:index]
        titles.append(title)
        codes.append(statute_code)


def extract_ref_sentences(filename):
    test = get_text(filename)
    #change to custom tokenizer 
    nlp = en_core_web_sm.load()
    nlp.tokenizer = TokenizerWithFormatting(nlp)
    nlp.add_pipe(num_pos_tagger, name="pos_num", after='tagger')
    matchlist = []

    matcher = Matcher(nlp.vocab, validate=True)
    pattern = [
        [{"POS": "NUM"},{"LOWER":"of"},{"LOWER":"the"},{"TEXT":{"IN": codes}}],
        [{"POS": "NUM"},{"LOWER":"of"},{"TEXT":{"IN": codes}}],
        [{"POS": "NUM"},{"TEXT":{"IN": codes}}],
        [{"POS": "PROPN"}, {"LOWER":"schedule"}]
    ]
    matcher.add("FindStatute", pattern)

    titles_matcher = PhraseMatcher(nlp.vocab)
    patterns = [nlp.make_doc(text) for text in titles]
    titles_matcher.add("TermsList", patterns)

    for sentence in nlp(test).sents:
        sentence = str(sentence)
        doc = nlp(sentence)
        matches = matcher(doc)
        for match_id, start, end in matches:
            string_id = nlp.vocab.strings[match_id]
            match_span = doc[start:end] #gives specific reference to the statute
            item = (match_span, sentence) #gives start index of match as well
            if item not in matchlist: #handles duplicates
                matchlist.append(item)
        title_matches = titles_matcher(doc)
        if len(title_matches) != 0:
            for match_id, start, end in matches:
                original_start = start
                for i in range(end-1, 0, -1):
                    if doc[i].pos_ == "NUM": #finds reference to provision number in the sentence
                        start = i
                        break
                if start == end:
                    start = 0
                match_span = doc[start:end] #gives specific reference to the statute 
                item = (match_span, sentence) #gives start index of match as well
                if item not in matchlist: #handles duplicates
                    matchlist.append(item)
    return matchlist


# print(extract_ref_sentences("2000_SGCA_55.txt"))

