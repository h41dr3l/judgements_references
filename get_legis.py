import spacy 
import en_core_web_sm
from spacy.matcher import Matcher
from spacy.util import DummyTokenizer

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


#test text
test ="""Burswood Nominees similarly involved the registration of an Australian judgment for 
gambling debts under the RECJA. In fact, like the present case, the underlying debt giving rise to 
the Australian judgment in Burswood Nominees was also a debt incurred pursuant to an Australian casino’s 
CCF (at [3]). The court held that, although the debt arising from the CCF took the form of a loan, it was 
in substance a claim for money won upon a wager, which would have been caught by s 5(2) of the CLA if the 
claim had been brought in a Singapore court in the first instance (at [21]–[22]). However, the court went 
on to hold that, while s 5(2) of the CLA elucidates Singapore’s domestic public policy, s 3(2)(f) of the 
RECJA requires a higher threshold of public policy to be met in order for the registration of a foreign judgment 
to be refused (at [24]). The meeting of this higher threshold of public policy, described by the court as 
“international” public policy, involves asking whether the domestic public policy in question was so important as to 
form part of the core of essential principles of justice and morality shared by all nations (at [42]). The court held 
that the domestic public policy encapsulated in s 5(2) of CLA did not meet this higher threshold (at [42]–[46]). 
It therefore declined to set aside the registration of the Australian judgment."""

test2 = "I will turn to the defence Dr Goh put up at the contempt proceedings before me momentarily. Before I do so, however, it is worth nothing that, prior to the hearing, the Plaintiff commenced bankruptcy examination proceedings under s 83 of the Bankruptcy Act (Cap 20, 2009 Rev Ed) against Dr Goh. This took place on 12 and 13 April 2021 before Assistant Registrar Sim Junhui (the “Examination Proceedings”). During these proceedings, Dr Goh said that the “Chinese businessmen” referenced in his earlier 22 September 2020 email were, in fact, casino junkets. He claimed to be a very big gambler, and that he had lost the Funds in the HSBC-GZ Account on gambling in Macau. Specifically, he stated that both amounts of ¥39,428,736 and ¥46,720,151.01 – forming the subject of the HSBC Orders – were completely lost in this way.  This was first time Dr Goh raised his gambling habit (cross-reference [11] above), and it was a position he maintained during the contempt proceedings."

#change to custom tokenizer 
nlp = en_core_web_sm.load()
nlp.tokenizer = TokenizerWithFormatting(nlp)
doc = nlp(test)
matcher = Matcher(nlp.vocab, validate=True)

#TODO add to patterns 
#for statute codes
pattern = [
    [{"POS": "NUM"},{"LOWER":"of"},{"LOWER":"the"},{"TEXT":{"IN": codes}}],
    [{"POS": "NUM"},{"LOWER":"of"},{"TEXT":{"IN": codes}}]
]
matcher.add("FindStatute", pattern)

#for statute titles
# pattern2 = [nlp(text) for text in titles]
# matcher.add("FindTitle", pattern)

#get matches
matches = matcher(doc)
matchlist = []
for match_id, start, end in matches:
    string_id = nlp.vocab.strings[match_id]  # Get string representation
    span = doc[start:end]  # The matched span, including section number --> this assumes section number comes before
    matchlist.append((start, span))
    # print(match_id, string_id, start-2, end, span.text) --> if required


#retreive the titles for respective statute codes found 
match_with_titles = []
for match in matchlist:
    index_of_doc = match[0]
    words = str(match[1]).split(' ')
    title = ''
    for word in words:
        if word in codes:
            index = codes.index(word)
            title = titles[index]
            break
    matched_word = ' '.join(words) 
    match_with_titles.append(f"{str(index_of_doc)}: {matched_word} ({title})")

#output
print(match_with_titles)