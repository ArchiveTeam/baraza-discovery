import gzip
import re
import requests
import string
import sys
import time
import random

DEFAULT_HEADERS = {'User-Agent': 'ArchiveTeam'}


class FetchError(Exception):
    '''Custom error class when fetching does not meet our expectation.'''


def main():
    # Take the program arguments given to this script
    # Normal programs use 'argparse' but this keeps things simple
    item_value = sys.argv[1]
    output_filename = sys.argv[2]  # this should be something like myfile.txt.gz
    lang = sys.argv[3]
    langcode = sys.argv[4]
    item_type = sys.argv[5]

    print('Starting', item_value)

    gzip_file = gzip.GzipFile(output_filename, 'wb')
    
    num = 0

    if item_type == "label" or item_type == "labelfr" or item_type == "labelru":
        while True:
            for shortcode in check(item_value, num, lang, langcode, item_type):
                # Write the valid result one per line to the file
                line = '{0}\n'.format(shortcode)
                print(line)
                sys.stdout.flush()
                gzip_file.write(line.encode('ascii'))
            htmlreq = requests.get('http://{2}/label?lid={0}&start={1}'.format(item_value, str(int(num)+20), lang), headers=DEFAULT_HEADERS)
            htmltext = htmlreq.text
            htmlstat = htmlreq.status_code
            if not ('"itlc mrow"' in htmltext or htmlstat == 404):
                num = num + 20
            else:
                break
    elif item_type == "useren" or item_type == "userfr" or item_type == "userru":
        while True:
            for shortcode in check(item_value, num, lang, langcode, item_type):
                # Write the valid result one per line to the file
                line = '{0}\n'.format(shortcode)
                print(line)
                sys.stdout.flush()
                gzip_file.write(line.encode('ascii'))
            htmlreq = requests.get('http://{2}/user?userid={0}&tab=wtmtoa&start={1}'.format(item_value, str(int(num)+20), lang), headers=DEFAULT_HEADERS)
            htmltext = htmlreq.text
            htmlstat = htmlreq.status_code
            if not ('"itlc mrow"' in htmltext or htmlstat == 404):
                num = num + 20
            else:
                break
        num = 0
        while True:
            for shortcode in check(item_value, num, lang, langcode, "{0}2".format(item_type)):
                # Write the valid result one per line to the file
                line = '{0}\n'.format(shortcode)
                print(line)
                sys.stdout.flush()
                gzip_file.write(line.encode('ascii'))
            htmlreq = requests.get('http://{2}/user?userid={0}&tab=wtmtor&start={1}'.format(item_value, str(int(num)+20), lang), headers=DEFAULT_HEADERS)
            htmltext = htmlreq.text
            htmlstat = htmlreq.status_code
            if not ('"itlc mrow"' in htmltext or htmlstat == 404):
                num = num + 20
            else:
                break
    else:
        for shortcode in check(item_value, num, lang, langcode, item_type):
            line = '{0}\n'.format(shortcode)
            print(line)
            sys.stdout.flush()
            gzip_file.write(line.encode('ascii'))

    gzip_file.close()

    print('Done')


def check(item_value, num, lang, langcode, item_type):
    if item_type == "label" or item_type == "labelfr" or item_type == "labelru":
        url = 'http://{2}/label?lid={0}&start={1}'.format(item_value, num, lang)
    elif item_type == "threaden" or item_type == "threadfr" or item_type == "threadru":
        url = 'http://{1}/thread?tid={0}'.format(item_value, lang)
    elif item_type == "useren" or item_type == "userfr" or item_type == "userru":
        url = 'http://{2}/user?userid={0}&tab=wtmtoa&start={1}'.format(item_value, num, lang)
    elif item_type == "useren2" or item_type == "userfr2" or item_type == "userru2":
        url = 'http://{2}/user?userid={0}&tab=wtmtor&start={1}'.format(item_value, num, lang)
    counter = 0
    while True:
        # Try 4 times before giving up
        if counter > 4:
            # This will stop the script with an error
            raise Exception('Giving up!')
        try:
            text = fetch(url)
        except FetchError:
            # The server may be overloaded so wait a bit
            print('Sleeping...')
            sys.stdout.flush()
            time.sleep(10)
        else:
            if text:
                yield 'id{1}:{0}'.format(item_value, langcode)
                for thread in extract_threads(text, lang, item_type):
                    yield 'thread{1}:{0}'.format(thread, langcode)
                for user in extract_users(text, lang, item_type):
                    yield 'user{1}:{0}'.format(user, langcode)
                for label in extract_labels(text, lang, item_type):
                    yield 'label{1}:{0}'.format(label, langcode)
            break  # stop the while loop

        counter += 1

def fetch(url):
    '''Fetch the URL and check if it returns OK.

    Returns True, returns the response text. Otherwise, returns None
    '''
    time.sleep(random.randint(5, 10))
    print('Fetch', url)
    sys.stdout.flush()

    response = requests.get(url, headers=DEFAULT_HEADERS)

    # response doesn't have a reason attribute all the time??
    print('Got', response.status_code, getattr(response, 'reason'))

    sys.stdout.flush()

    if response.status_code == 200:
        # The item exists
        if not response.text:
            # If HTML is empty maybe server broke
            raise FetchError()

        return response.text
    elif response.status_code == 404 or response.status_code == 400:
        # Does not exist
        return
    else:
        # Problem
        raise FetchError()

def extract_threads(text, lang, item_type):
    '''Return a list of tags from the text.'''
    if lang == "otvety.google.ru/otvety":
        return re.findall(r'"\/otvety\/thread\?tid=([a-z0-9]+)', text)
    else:
        return re.findall(r'"\/baraza\/[a-z][a-z]\/thread\?tid=([a-z0-9]+)', text)

def extract_users(text, lang, item_type):
    '''Return a list of tags from the text.'''
    if lang == "otvety.google.ru/otvety":
        return re.findall(r'"\/otvety\/user\?userid=([0-9]+)', text)
    else:
        return re.findall(r'"\/baraza\/[a-z][a-z]\/user\?userid=([0-9]+)', text)

def extract_labels(text, lang, item_type):
    '''Return a list of tags from the text.'''
    if lang == "otvety.google.ru/otvety":
        return re.findall(r'"\/otvety\/label\?lid=([a-z0-9]+)', text)
    else:
        return re.findall(r'"\/baraza\/[a-z][a-z]\/label\?lid=([a-z0-9]+)', text)

if __name__ == '__main__':
    main()
