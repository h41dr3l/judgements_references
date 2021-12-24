#splits up provision number and act i.e. "s 43" PROV and "Company Act" LEGISLATION
import spacy 
import en_core_web_sm
from spacy.language import Language
from spacy.util import DummyTokenizer
from spacy.matcher import Matcher
from spacy.tokens import Doc, Span, Token

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

#reads the file
def get_text(filename):
    with open(filename, 'r', encoding="utf8") as f:
        test = f.read().replace('\n', ' ')
    return test

#custom component to label numbers including provision numbers
def is_num_getter(token):
    for ch in token.text:
        if ch.isdigit():
            token.pos_ = 'NUM'
            return True
    return False

#gets the list of titles and code of a statute 
titles = []
codes = []
with open('legis_name.txt', 'r') as f:
    text = f.read()
    statutes = text.split('\n')[1:-1]
    for item in statutes:
        item = item.split('|')
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
    nlp = en_core_web_sm.load()
    nlp.tokenizer = TokenizerWithFormatting(nlp)
    # nlp.add_pipe("num_pos_tagger", before="tagger")
    ruler = nlp.add_pipe("entity_ruler", config={"validate": True}, before='ner')
    Token.set_extension("is_number", getter=is_num_getter)
    
    legis_title_pattern = []
    for title in titles: #create patterns for each title
        title = title.split()
        title_pattern = []
        for word in title: #add all the words in the title to the pattern
            if word.isdigit() == True: #for statutes with years in the title
                title_pattern.append({"TEXT": word, "OP":"?"})
            elif word[-1] in ",')": #if word in statute title has close bracket, comma, punctuation etc.
                title_pattern.extend(({"LOWER": word[0:-1].lower()},{"ORTH": word[-1]}))
            elif word[-1] in "(": #if word in statute title has open bracket
                title_pattern.extend(({"ORTH": word[0]},{"LOWER": word[1:].lower()}))
            else: #word is a normal text            
                title_pattern.append({"LOWER": word.lower()})
        legis_title_pattern.append({"label": "LEGISLATION", "pattern": title_pattern})

    ruler.add_patterns(legis_title_pattern)

    #labelling abbreviations
    ruler.add_patterns([
        {'label': 'ABBREVIATION',
        'pattern': [
            {'ORTH': '('},
            {'LOWER':'the', 'OP':'?'},
            {'ORTH': '“'}, 
            {'IS_ALPHA': True, 'OP': '+'}, #assumes abbreviations have max 5 words TODO: more efficient way?
            {'IS_ALPHA': True, 'OP': '?'},
            {'IS_ALPHA': True, 'OP': '?'},
            {'IS_ALPHA': True, 'OP': '?'},
            {'IS_ALPHA': True, 'OP': '?'},
            {'ORTH': '”'},
            {'ORTH': ')'}
        ]},
    #labelling edition of legislation used
        {'label': 'EDITION',
        'pattern': [
            {'ORTH': '('},
            {'IS_TITLE': True, "TEXT":"Cap"}, 
            {'IS_DIGIT': True}, 
            {'ORTH': ","},
            {'IS_DIGIT': True},
            {'IS_TITLE': True, 'TEXT': 'Rev'},
            {'IS_TITLE': True, 'TEXT': 'Ed'},
            {'ORTH':')'}
        ]},
        {'label': 'EDITION',
        'pattern': [
            {'ORTH': '('},
            {'IS_TITLE': True, "TEXT":"Act"}, 
            {'IS_DIGIT': True}, 
            {'LOWER': "of"},
            {'IS_DIGIT': True},
            {'ORTH':')'}
        ]},
    #labelling provision patterns 
        {'label':'PROVISION', 
        'pattern': [
            {"LOWER": {"IN":['s','section','ss']}},
            {"IS_PUNCT": False, '_': {'is_number': True}, "OP":"+"} 
        ]},
        {'label':'PROVISION', 
        'pattern': [
            {"POS": "PROPN"},
            {"LOWER":"schedule"}, 
        ]}          
        ])

    #get doc
    doc = nlp(test)
 
    #Debugging code for printing labels and tokens
    # for ent in doc.ents:
    #     if ent.label_ == "PROVISION" or ent.label_ =="ABBREVIATION" or ent.label_=="EDITION":
    #         print(ent.text, ent.label_)   
    # for token in doc:
    #     print(token, token.pos_)

    #gets list of abbreviations, if no abbreviations, will display on displacy
    legis_abbrev = match_legis_abbrev(doc)
    if len(legis_abbrev) == 0:
        spacy.displacy.serve(doc, style="ent")
        return 0
    
    #setting entity label to 'PROVISION' for abbreviations
    pattern_abbrev = []
    for match in legis_abbrev:
        abbrev = match[1]
        if abbrev not in titles:
            abbrev = abbrev.split()
            abb_pattern = []               
            for word in abbrev: #add all the words in the title to the pattern          
                abb_pattern.append({"LOWER": word.lower()})
            pattern_abbrev.append({"label": "LEGISLATION", "pattern": abb_pattern})
    if len(pattern_abbrev) != 0:
        ruler.add_patterns(pattern_abbrev)
        doc = nlp(test)
    spacy.displacy.serve(doc, style="ent")
    return 1

#Adds all entities into a list with entity text in the following tuple format: (entity_text, entity_label)
def get_entity_labels(doc):
    entity_labels = []
    for ent in doc.ents:
        entity_labels.append((ent.text, ent.label_))
    return entity_labels

#gets abbreviations for legislation
def match_legis_abbrev(doc):
    entity_labels = get_entity_labels(doc)
    matches = []
    for i in range(0, len(entity_labels)-2):
        current_entity, current_entity_label = entity_labels[i] #legis title/code
        second_entity, second_entity_label = entity_labels[i+1] #edition
        third_entity, third_entity_label = entity_labels[i+2] #abbreviation attached 
        if (current_entity_label == "LEGISLATION" 
        and second_entity_label =="EDITION" and third_entity_label =='ABBREVIATION'):
            index = third_entity.index('“')
            matches.append((current_entity, third_entity[index+1:-2]))
    print(matches) #see which abbreviations are for which legislation
    return matches

#calling the main function 
extract_ref_sentences("./html/2017_SGHC_122.txt")