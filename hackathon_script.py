# https://gdelt.github.io/#api=doc&query=&contentmode=ArtList&maxrecords=75&timespan=1d

# load code modules
from bs4 import BeautifulSoup
from datetime import datetime
from gdelt import gdelt
from urllib.parse import urlencode
from uuid import UUID

import hashlib
import os
import pandas as pd
import requests
import time
import warnings

gd2 = gdelt(version=2)

# functions

# define function to query GDELT
def gdelt_get_article_urls(dest, art_file='', query='', country='', start='01-01-2017', end=datetime.now().strftime('%d-%m-%Y')):
    """
    Note: 01.01.2017 is the earliest possible start date.
    """

    # initialize parameters
    params = {
        'query': query,
        'sourcecountry': country,
        'sourcelang': 'eng',
        'mode': 'ArtList',
        'maxrecords': '250',
        'sort': 'DateDesc',
        'format': 'json'
    }

    # adjust parameters based on function input
    start = datetime.strptime(start, '%d-%m-%Y')
    params['startdatetime'] = int(start.strftime('%Y%m%d%H%M%S'))

    end = datetime.strptime(end, '%d-%m-%Y')
    params['enddatetime'] = int(end.strftime('%Y%m%d%H%M%S'))

    if country == '':
        params.pop('sourcecountry')

    # create url based on parameters
    url = 'https://api.gdeltproject.org/api/v2/doc/doc' + "?" + urlencode(params)

    # modify parameters for json
    url = url.replace('&sourcelang=', '%20sourcelang:')
    if country != None:
        url = url.replace('&sourcecountry=', '%20sourcecountry:')

    r = requests.get(url)                                               # send request
    time.sleep(2)                                                       # pause to prevent server overload
    if r.content == b'{}' or r.content[:11] == b'Your search':          # exit if there are no articles are returned
        return

    articles = r.json().get('articles', [])                                 # extract articles from json response
    articles = pd.DataFrame(articles)                                       # convert articles to dataframe
    articles = articles.drop_duplicates(subset=['url'], keep='first')       # remove duplicate entries

    if len(articles.index) == 250:
        warnings.warn('Maximum number of extractable records reached. There is a possibility that some records '+
                      'are not shown. To see all articles query by day.\nQuery: '+
                      query+'\n ---')

    # format results for upload to Elasticsearch
    articles = articles.rename(columns={'seendate': 'date', 'sourcecountry': 'country'})    # rename columns
    articles['date'] = [x[6:8]+'-'+x[4:6]+'-'+x[0:4] for x in articles['date']]             # convert date
    articles = articles[['url', 'title', 'date', 'country']]                                # delete obsolete columns

    # sets unique id to each article
    id = []
    for u in articles['url']:
        hash = hashlib.md5()
        hash.update(u.encode('utf-8'))
        id = id + [UUID(hash.hexdigest())]
    articles['id'] = id

    # stores articles to file
    if art_file != '':
        art_file = art_file if art_file != 'dest' else dest
        if art_file in os.listdir():
            old_articles = pd.read_csv(art_file)
            articles = old_articles.append(articles, ignore_index=True)

    articles.to_csv(dest, index=False)

# get keywords for attacks against human rights defenders
hrd_nouns = []
with open('hrd_nouns.txt', 'r') as f:
  for line in f:
    hrd_nouns.append(line.strip())

hrd_verbs = []
with open('hrd_verbs.txt', 'r') as f:
  for line in f:
    hrd_verbs.append(line.strip())

# get all articles in ukraine related to all keywords
i = 1
for n in hrd_nouns:
    for v in hrd_verbs:
        print('Scraping (', i, '/', len(hrd_nouns)*len(hrd_verbs), '): ', n, ' - ', v, sep='')
        i = i + 1
        gdelt_get_article_urls(dest='articles_database.csv',    # string: path to where to store the csv
                               art_file='dest',                 # string: path to existing database (dest for same as destination)
                               query=n+' '+v,                   # string: query
                               country='UP',                    # string: check https://gdelt.github.io/ html for codes
                               start='01-01-2022')              # string: start date not before 01.01.2017


# DELETE IDENTICAL TITLE!