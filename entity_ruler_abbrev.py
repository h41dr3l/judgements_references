import spacy 
import en_core_web_sm
from spacy.matcher import Matcher

#reads the file
def get_text(filename):
    with open(filename, 'r', encoding="utf8") as f:
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
    nlp = en_core_web_sm.load()
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
                        {"ENT_TYPE": "CARDINAL", "OP":"+"}, 
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
                        {"ENT_TYPE": "CARDINAL", "OP":"+"}, 
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

    #labelling abbreviations
    ruler.add_patterns([
        {
        'label': 'ABBREVIATION',
        'pattern': [
            {'ORTH': '('},
            {'ORTH': '“'}, 
            {'IS_ALPHA': True, 'OP': '+'}, #assumes abbreviations have max 5 words TODO: more efficient way?
            {'IS_ALPHA': True, 'OP': '?'},
            {'IS_ALPHA': True, 'OP': '?'},
            {'IS_ALPHA': True, 'OP': '?'},
            {'IS_ALPHA': True, 'OP': '?'},
            {'ORTH': '”'},
            {'ORTH': ')'}
        ]
        },
    #labelling edition of legislation used 
        {
        'label': 'EDITION',
        'pattern': [
            {'ORTH': '('},
            {'IS_TITLE': True, "TEXT":"Cap"}, 
            {'IS_DIGIT': True}, 
            {'ORTH': ","},
            {'IS_DIGIT': True},
            {'IS_TITLE': True, 'TEXT': 'Rev'},
            {'IS_TITLE': True, 'TEXT': 'Ed'},
            {'ORTH':')'}
        ]
        }       
        ])

    #get doc
    doc = nlp(test)

    #Debugging code for printing labels and tokens
    # for ent in doc.ents:
    #     if ent.label_ == "PROVISION" or ent.label_ =="ABBREVIATION" or ent.label_=="EDITION":
    #         print(ent.text, ent.label_)   
    # for token in doc:
    #     print(token, token.pos_)
    # spacy.displacy.serve(doc, style="ent")

    legis_abbrev = match_legis_abbrev(doc,nlp)
    if len(legis_abbrev) == 0:
        spacy.displacy.serve(doc, style="ent")
        return 0
    
    #getting entity for abbreviations
    pattern_abbrev = []
    for match in legis_abbrev:
        abbrev = match[1]
        abbrev = abbrev.split()
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
                        {"ENT_TYPE": "CARDINAL", "OP":"+"}, 
                        {"ORTH": ")", "OP": "?"},
                        {"LOWER":"of", "OP":"?"}, 
                        {"LOWER": "the", "OP": "?"}]
        schedule_pattern = [{"POS": "PROPN", "OP": "?"},
                {"LOWER":"schedule"}, 
                {"LOWER":"of", "OP":"?"},
                {"LOWER":"to", "OP":"?"}, 
                {"LOWER": "the", "OP": "?"}]                
        for word in abbrev: #add all the words in the title to the pattern
            prov_pattern1.append({"LOWER": word.lower()})
            prov_pattern2.append({"LOWER": word.lower()})
            prov_pattern3.append({"LOWER": word.lower()})
            schedule_pattern.append({"LOWER": word.lower()})
        pattern_abbrev.append({"label": "PROVISION", "pattern": prov_pattern1})
        pattern_abbrev.append({"label": "PROVISION", "pattern": prov_pattern2})
        pattern_abbrev.append({"label": "PROVISION", "pattern": prov_pattern3})
        pattern_abbrev.append({"label": "PROVISION", "pattern": schedule_pattern})
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
def match_legis_abbrev(doc, nlp):
    entity_labels = get_entity_labels(doc)
    matches = []
    for i in range(0, len(entity_labels)-2):
        current_entity, current_entity_label = entity_labels[i]
        next_entity, next_entity_label = entity_labels[i+1]
        after_entity, after_entity_label = entity_labels[i+2]
        if current_entity_label == "PROVISION" and next_entity_label =="EDITION" and after_entity_label =='ABBREVIATION':
            matches.append((current_entity, after_entity[2:-2]))
    print(len(matches))
    print(matches)
    return matches

#calling the main function 
extract_ref_sentences("./html/2021_SGHC_81.txt")


