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
    item_value = int(sys.argv[1])
    output_filename = sys.argv[2]  # this should be something like myfile.txt.gz

    print('Starting', item_value)

    gzip_file = gzip.GzipFile(output_filename, 'wb')
    
    num = 0
    
    while True:
        for shortcode in check(item_value, num):
            # Write the valid result one per line to the file
            line = '{0}\n'.format(shortcode)
            gzip_file.write(line.encode('ascii'))
        htmltext = requests.get('http://www.google.com/baraza/en/label?lid={0}&start={1}'.format(item_value, str(int(num)+20)), headers=DEFAULT_HEADERS).text
        if not 'No questions related to this label.' in htmltext:
            num = num + 20
        elif 'No questions related to this label.' in htmltext:
            break

    gzip_file.close()

    print('Done')


def check(item_value, num):
    url = 'http://www.google.com/baraza/en/label?lid={0}&start={1}'.format(item_value, num)
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
                yield 'id:{0}'.format(item_value)
                for thread in extract_threads(text):
                    yield 'thread:{0}'.format(thread)
                for user in extract_users(text):
                    yield 'user:{0}'.format(user)
            break  # stop the while loop

        counter += 1

def fetch(url):
    '''Fetch the URL and check if it returns OK.

    Returns True, returns the response text. Otherwise, returns None
    '''
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
    elif response.status_code == 404:
        # Does not exist
        return
    else:
        # Problem
        raise FetchError()

def extract_threads(text):
    '''Return a list of tags from the text.'''
    # Search for "http://onwonder.blogspot.com/"
    return re.findall(r'"/baraza/en/thread\?tid=([a-z0-9]+)', text)

def extract_threads(text):
    '''Return a list of tags from the text.'''
    # Search for "http://onwonder.blogspot.com/"
    return re.findall(r'"/baraza/en/user\?userid=([0-9]+)', text)

if __name__ == '__main__':
    main()
