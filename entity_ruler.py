import spacy 
import en_core_web_sm
from spacy.language import Language


def get_text(filename):
    with open(filename, 'r', encoding="utf8") as f:
        test = f.read().replace('\n', ' ')#.split('.')[:-1]
    return test

@Language.component("num_pos_tagger")
def num_pos_tagger(doc):
    for token in doc:
        for ch in token.text:
            if ch.isdigit():
                token.pos_ = 'NUM'
                break
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


def extract_ref_sentences(filename):
    test = get_text(filename)
    nlp = en_core_web_sm.load()
    nlp.add_pipe("num_pos_tagger", after="tagger") #TODO: this does not successfuly retag provision numbers into "NUM"
    ruler = nlp.add_pipe("entity_ruler", config={"validate": True}, before='ner')

    pattern = []
    for title in titles: #create patterns for each title
        title = title.split()
        prov_pattern1 = [{"LOWER": "s", "OP":"?"},
                        {"POS": "NUM", "OP":"+"}, 
                        {"ORTH": ")", "OP": "?"},
                        {"LOWER":"of", "OP":"?"}, 
                        {"LOWER": "the", "OP": "?"}]
        prov_pattern2 = [{"LOWER": "s", "OP":"?"},
                        {"POS": "X", "OP":"+"}, 
                        {"ORTH": ")", "OP": "?"},
                        {"LOWER":"of", "OP":"?"}, 
                        {"LOWER": "the", "OP": "?"}]
        prov_pattern3 = [{"LOWER": "s", "OP":"?"},
                        {"POS": "PROPN", "OP":"+"}, 
                        {"ORTH": ")", "OP": "?"},
                        {"LOWER":"of", "OP":"?"}, 
                        {"LOWER": "the", "OP": "?"}]
        schedule_pattern = [{"POS": "PROPN", "OP": "?"},
                {"LOWER":"schedule"}, 
                {"LOWER":"of", "OP":"?"},
                {"LOWER":"to", "OP":"?"}, 
                {"LOWER": "the", "OP": "?"}]                
        for word in title: #add all the words in the title to the pattern
            prov_pattern1.append({"LOWER": word.lower()})
            prov_pattern2.append({"LOWER": word.lower()})
            prov_pattern3.append({"LOWER": word.lower()})
            schedule_pattern.append({"LOWER": word.lower()})
        pattern.append({"label": "PROVISION", "pattern": prov_pattern1})
        pattern.append({"label": "PROVISION", "pattern": prov_pattern2})
        pattern.append({"label": "PROVISION", "pattern": prov_pattern3})
        pattern.append({"label": "PROVISION", "pattern": schedule_pattern})
    ruler.add_patterns(pattern)
 
    pattern_codes = []
    for code in codes: #create patterns for each code
        prov_pattern1 = [{"LOWER": "s", "OP":"?"},
                        {"POS": "NUM", "OP":"+"}, 
                        {"ORTH": ")", "OP": "?"},
                        {"LOWER":"of", "OP":"?"}, 
                        {"LOWER": "the", "OP": "?"},
                        {"TEXT": code}]
        prov_pattern2 = [{"LOWER": "s", "OP":"?"},
                {"POS": "X", "OP":"+"}, 
                {"ORTH": ")", "OP": "?"},
                {"LOWER":"of", "OP":"?"}, 
                {"LOWER": "the", "OP": "?"},
                {"TEXT": code}]
        prov_pattern3 = [{"LOWER": "s", "OP":"?"},
                        {"POS": "PROPN", "OP":"+"}, 
                        {"ORTH": ")", "OP": "?"},
                        {"LOWER":"of", "OP":"?"}, 
                        {"LOWER": "the", "OP": "?"},
                        {"TEXT": code}]
        schedule_pattern = [{"POS": "PROPN", "OP": "?"},
                {"LOWER":"schedule"}, 
                {"LOWER":"of", "OP":"?"},
                {"LOWER":"to", "OP":"?"}, 
                {"LOWER": "the", "OP": "?"},
                {"TEXT": code}]                
        pattern_codes.append({"label": "PROVISION", "pattern": prov_pattern1})
        pattern_codes.append({"label": "PROVISION", "pattern": prov_pattern2})
        pattern_codes.append({"label": "PROVISION", "pattern": prov_pattern3})
        pattern_codes.append({"label": "PROVISION", "pattern": schedule_pattern})
    ruler.add_patterns(pattern_codes)

    doc = nlp(test)
    for ent in doc.ents:
        if ent.label_ == "PROVISION":
            print(ent.text, ent.label_)
    # for token in doc:
    #     print(token, token.pos_)
    spacy.displacy.serve(doc, style="ent")


extract_ref_sentences("./html/2021_SGHC_16.txt")


