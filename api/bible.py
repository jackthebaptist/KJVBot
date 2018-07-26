import json
import urllib.request, urllib.error, urllib.parse
import re
import configparser
import logging
from bs4 import BeautifulSoup
import pickle

#Importing configuration params
config = configparser.ConfigParser()
config.read('api/bible.cfg')

urls = config['URL']
defaults = config['DEFAULT']
EMPTY = defaults['empty_message']
default_version = defaults['version']

def strip_markdown(string):
    return string.replace('*', '').replace('_', '').replace('`', '')

"""
Search a specific passage (es. John 3:16)
params:
    passage: it explain itself
    version: es. ESV
    numeration: show verse number or not
    title: show passage title or not
output:
    dictionary(reference,version,text)
"""
def get_passage(passage, version=default_version, numeration=True, title=True):

    def to_sup(text):
        sups = {'0': '\u2070',
                '1': '\xb9',
                '2': '\xb2',
                '3': '\xb3',
                '4': '\u2074',
                '5': '\u2075',
                '6': '\u2076',
                '7': '\u2077',
                '8': '\u2078',
                '9': '\u2079',
                '-': '\u207b'}
        return ''.join(sups.get(char, char) for char in text)

    BG_URL = urls['passage']

    search = urllib.parse.quote(passage.lower().strip())
    url = BG_URL.format(search, version)

    try:
      result = urllib.request.urlopen(url)
    except urllib.error.URLError as e:
      logging.warning('Error fetching passage:\n' + str(e))

    html = result.read()
    soup = BeautifulSoup(html, 'lxml').select_one('.passage-text')

    if not soup:
        return EMPTY

    WANTED = 'bg-bot-passage-text'
    UNWANTED = '.passage-display, .footnote, .footnotes, .crossrefs, .publisher-info-bottom'

    if not numeration:
        UNWANTED += ', .chapternum, .versenum'
    if not title:
        UNWANTED += ', h1, h2, h3, h4, h5, h6'


    title = soup.select_one('.passage-display-bcv').text
    reference = strip_markdown(title.strip())

    for tag in soup.select(UNWANTED):
        tag.decompose()

    for tag in soup.select('h1, h2, h3, h4, h5, h6'):
        tag['class'] = WANTED
        text = tag.text.strip().replace('\\', ' ')
        tag.string = '*' + strip_markdown(text) + '*'

    needed_stripping = False

    for tag in soup.select('p'):
        tag['class'] = WANTED
        bad_strings = tag(text=re.compile('(\*|\_|\`)'))
        for bad_string in bad_strings:
            stripped_text = strip_markdown(str(bad_string))
            bad_string.replace_with(stripped_text)
            needed_stripping = True

    if needed_stripping:
        logging.info('Stripped markdown')

    for tag in soup.select('br'):
        tag.name = 'span'
        tag.string = '\n'

    for tag in soup.select('.chapternum'):
        num = tag.text.strip()
        if numeration:
            tag.string = '#' + strip_markdown(num) + '#'
        else:
            tag.string = ''

    for tag in soup.select('.versenum'):
        num = tag.text.strip()
        tag.string = to_sup(num)

    for tag in soup.select('.text'):
        tag.string = tag.text.rstrip()

    final_text = ''
    for tag in soup(class_=WANTED):
        final_text += tag.text.strip()

    return {'reference': reference, 'version': version, 'text': final_text.strip()}


"""
Get a specific Chapter
params:
    book: es (John)
    chapter: es 1
    version: es. ESV
    numeration: show verse number or not
    title: show passage title or not
output:
    dictionary(reference,version,text)
"""
def getChapterPassage(book, chapter, version=default_version, numeration=True, title=True):
    return get_passage(book+' '+chapter, version, numeration, title)

"""
Search specific words (es. Fruit Spirit)
params:
    search: words to search
    version: es. ESV
    searchype: Possible search type ALL, ANY, PHRASE
output:
    dictionary(reference,text)
"""

def get_search_result(search, version=default_version, searchtype='ALL'):

    BG_URL = urls['search']

    search = search.strip().replace(' ', '+')

    url = BG_URL.format(search, version, searchtype)

    try:
      result = urllib.request.urlopen(url)
    except urllib.error.URLError as e:
      logging.warning('Error fetching passage:\n' + str(e))

    html = result.read()
    soup = BeautifulSoup(html, 'lxml').select_one('.search-result-list')

    if not soup:
        return EMPTY

    WANTED = ''
    UNWANTED = '.bible-item-extras '

    list_results = {}

    for tag in soup.select(UNWANTED):
        tag.decompose()

    for item in soup.select('.bible-item'):

        tag_title = item.select_one('.bible-item-title')

        tag_text = item.select_one('.bible-item-text')
        text = tag_text.text.strip().replace('\\', ' ')
        tag_text.string = strip_markdown(text)

        list_results[tag_title.string] = tag_text.string


    return list_results

"""
Show verse of the day
params:
    version: es. ESV
output:
    dictionary(reference,version,text)
"""
#Verse of the day multi version implementation
def getVotd(version=default_version):

    url = urls['votd']
    response = urllib.request.urlopen(url)
    data = json.loads(response.read().decode('utf-8'))
    return {'reference': data['votd']['reference'], 'version': version, 'text': get_passage(data['votd']['reference'], version=default_version, numeration=False, title=False)['text']}

"""
Get Books List and chapter num for each book.
params:
    version: es. ESV
output:
    dictionary(book,chapter_num)
"""
def getBookList(version=default_version):

    BG_URL = urls['booklist']

    url = BG_URL.format(getVersionName(version))

    try:
        result = urllib.request.urlopen(url)
    except urllib.error.URLError as e:
        logging.warning('Error fetching passage:\n' + str(e))

    html = result.read()

    books = {}

    for td in BeautifulSoup(html, 'lxml').findAll("td", {"class": "toggle-collapse2 book-name"}):

        for tag in td.select("span"):
            tag.decompose()

        #get Chapter num for each book
        last_a = None
        for last_a in td.findNext('td').findAll('a'): pass
        if last_a:
            books[td.getText()] =last_a.text


    return books

def updateVersionsList():

    url = urls['update_version']

    try:
        result = urllib.request.urlopen(url)
    except urllib.error.URLError as e:
        logging.warning('Error fetching passage:\n' + str(e))

    html = result.read()

    versions = {}

    eng = False
    for opt in BeautifulSoup(html, 'lxml').find('select').find_all('option'):
        #Add -Bible string to English Bible version
        if opt.has_attr('class') and opt['class'][0] == 'lang':

                if opt['value']=='KJ21':
                    eng=True
                else:
                    eng=False

        if not opt.has_attr('class'):
            text = opt.text.replace(' ', '-').replace('(', '').replace(')', '')
            if eng:
                text += '-Bible'

            versions[opt['value']]= text


    with open(defaults['version_file'], "wb") as fp:
        pickle.dump(versions, fp)

"""
Get Version description useful to get booklist
"""
#Get Version description for Books
def getVersionName(version=default_version):

    with open(defaults['version_file'], 'rb') as fp:
        dict = pickle.load(fp)

    return dict[version]
