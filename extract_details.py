
# load code modules
import re
import json
import spacy                                            # download first with: python -m spacy download en_core_web_lg
import pandas as pd
import pytextrank
import geonamescache

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from pprint import pprint

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words
from sumy.summarizers.text_rank import TextRankSummarizer

# when running for the first time:
#import nltk
#nltk.download('stopwords')
#nltk.download('punkt')

# set parameters
LANGUAGE = "english"
SENTENCES_COUNT = 3
METHOD = 'textrank'

nlp = spacy.load("en_core_web_lg")
nlp.add_pipe("textrank")

doc = None
rank_dict = dict()
person_org_list = list()

# define functions
def summarize(text, lang=LANGUAGE, count=SENTENCES_COUNT):
    parser = PlaintextParser.from_string(text, Tokenizer(lang))
    stemmer = Stemmer(lang)

    summarizer = TextRankSummarizer(stemmer)
    summarizer.stop_words = get_stop_words(lang)

    result = []
    for sentence in summarizer(parser.document, count):
        result.append(str(sentence))

    return result

def generate_short_text(title, text):
    sentence_list = summarize(text)
    temp_title = title if title.endswith('.') else title + "."
    sentence_list.append(temp_title)
    short_text = ' '.join(sentence_list)
    return short_text

def clean_list(input_list):
    temp = input_list.copy()
    result = list()
    while temp:
        flag = False
        x = temp.pop()
        for i in temp:
            if x.lower() in i.lower():
                flag = True
                break
        if not flag:
            result.append((x.lower()))
    return result


def get_rank_dict(spacy_doc):
    rank_dict = dict()
    for phrase in spacy_doc._.phrases:
        rank_dict[phrase.text.lower()] = phrase.rank
    return rank_dict

def get_person_org_list(spacy_doc):
    temp_entities = list()
    person_org_list = list()
    for ent in spacy_doc.ents:
        if (ent.label_ == 'PERSON' or ent.label_ == 'ORG'):
            if ent.text not in person_org_list:
                temp_entities.append(ent.text.lower())

    temp_entities = clean_list(temp_entities)

    person_org_list = list()
    for phrase in spacy_doc._.phrases:
        if phrase.text.lower() in temp_entities:
            person_org_list.append(phrase.text.lower())

    return person_org_list

def get_actor(text):
    doc = nlp(text)
    rank_dict = get_rank_dict(doc)
    person_org_list = get_person_org_list(doc)

    actor_dict = dict()
    for chunk in doc.noun_chunks:
        if chunk.root.dep_ in ['nsubj', 'nsubjpass']:
            if chunk.text.lower() not in stopwords.words('english'):

                actor = chunk.lemma_.lower()
                for entities in person_org_list:
                    if actor in entities:
                        actor = entities
                        break

                actor = re.sub(r'[^A-Za-z0-9 ]+', '', actor)
                actor = ' '.join([w for w in word_tokenize(actor) if not w.lower() in stopwords.words('english')])

                if actor in actor_dict:
                    actor_dict[actor] = actor_dict[actor] + 1
                else:
                    rankd_key = chunk.text.lower().replace("'", "")
                    actor_dict[actor] = rank_dict[rankd_key]

    return max(actor_dict, key=actor_dict.get) if actor_dict else None

def get_location_list(text):
    doc = nlp(text)
    locations = list()
    for ent in doc.ents:
        if ent.label_ in ['GPE', 'LOC']:
            locations.append(ent.text)
    return locations

def most_common(lst):
    return max(set(lst), key=lst.count) if lst else None

def format_countries(input_dict):
    country_dict = dict()
    for k, v in input_dict.items():
        country_dict[k] = v['name']
    return country_dict

def format_cities(input_dict):
    city_dict = dict()
    for k, v in input_dict.items():
        if v['name'] not in city_dict.keys():
            city_dict[v['name']] = [v['countrycode']]
        else:
            if v['countrycode'] not in city_dict[v['name']]:
                city_dict[v['name']].append(v['countrycode'])
    return city_dict

def get_location(text):
    gc = geonamescache.GeonamesCache()
    country_dict = format_countries(gc.get_countries())
    cities_dict = format_cities(gc.get_cities())

    location_list = get_location_list(text)

    result = list()
    for loc in location_list:

        if loc in country_dict.values():
            result.append(loc)
        elif loc in cities_dict.keys():
            print(loc)
            for code in cities_dict[loc]:
                result.append(country_dict[code])

    return max(set(result), key=result.count) if result else most_common(location_list)

TEXT = 'A debate over religious instruction in schools has emerged in an Australian court with a bid to have Satanism classes taught at some Queensland education institutions.\n\nClassroom. (File photo) Source: istock.com\n\nThe state government is being challenged in the Brisbane Supreme Court over its refusal to let the Noosa Temple of Satan offer religious instruction at four state schools.\n\nThe decision was based on the Education Department\'s position that the temple, created in 2019, is not a religious denomination or society, according to a letter written by department deputy director-general Peter Kelly.\n\nBut Noosa Temple of Satan leader Trevor Bell has asked the court to set aside the government\'s decision by declaring the temple is a religious denomination or society.\n\nThe action comes after the temple notified four schools; Centenary and Sunshine Beach state high schools and Tewantin and Wilston state schools, of its intention to provide religious instruction classes.\n\nThe group aimed to "provide students with information about the religion of Satanism, including belief in Satan as a supernatural being, the canons of conduct and the tenets" and "to help students analyse the information and critically evaluate the religion of Satanism", according to court documents.\n\nBell and Noosa temple founder Robin Bristow are listed as the accredited representatives to present the classes.\n\nBristow wrote an affidavit handed into court under the name Brother Samael Demo-Gorgon which he chose after searching on the internet for the most demonic name he could find, the court was told on Thursday.\n\nAlthough he said in media interviews he did not refer to himself as a Satanist, Bristow told the court he "had reconsidered that" and would now call himself a Satanist.\n\nHe agreed under questioning from Solicitor-General Sandy Thompson QC he began canvassing "to try and persuade" parents to request religious education through the temple at schools this year.\n\nBristow agreed he handed out leaflets outside a Queensland school while wearing a hood and cape - "very similar to yours", he told Thompson - and carrying a plastic skull he bought at Woolworths.\n\nThree sets of parents from different schools requested the temple provide classes, although the group "received support from other parents, but they didn\'t sign up", Bristow added.\n\nKelly wrote in March the department understood from statements publicly attributed to Bristow "the Temple was established in response to the Australian Government\'s proposal for a religious discrimination Bill and that most of the people who follow Satanism, do not believe that Satan exists".\n\n"Accordingly, the department considers there is a real question whether the Temple\'s true purpose is political as opposed to religious," Mr Kelly said in a letter contained in court documents.\n\n"There is also limited evidence to demonstrate that the Temple has sufficient membership in order to be regarded as a denomination or society."\n\nThe temple was created in response to the proposed Religious Discrimination Bill, but Mr Bristow didn\'t see how that was relevant to the decision, he said in response.\n\n"We do not know the proportion of Satanists who believe in Satan and neither does the Department," he added.\n\n"The same could be said of all religions. There are no doubt millions of nominal \'Christians\' who do not believe that Christ was the son of God."\n\nJustice Martin Burns will hand down his decision on a date yet to be confirmed.'
get_actor(TEXT)
get_location(TEXT)