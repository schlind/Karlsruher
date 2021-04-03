'''See https://pegelonline.wsv.de/webservice/guideRestapi'''

import json
import sys
import requests

API_URL = 'https://pegelonline.wsv.de/webservices/rest-api/v2' \
          + '/stations/b6c6d5c8-e2d5-4469-8dd8-fa972ef7eaea/{}/currentmeasurement.json'

TWEET = 'Der Rhein bei Maxau steht bei {0} cm ({1}) und fliesst mit {2} m^3/s ({3}) weiter.'

def fetch(api_url):
    '''Fetch requested value from webservice.'''
    response = requests.get(api_url, headers={})
    if response.status_code == 200:
        data = json.loads(response.content.decode('utf-8'))
        return int(data['value']) if 'value' in data else -1
    return -1

def rhein(karlsruher):
    '''Tweet Rhine's current pegel and flow.'''
    pegel = fetch(API_URL.format('W'))
    fluss = fetch(API_URL.format('Q'))
    old_pegel = karlsruher.brain.get('rhein', 'pegel')
    old_fluss = karlsruher.brain.get('rhein', 'fluss')
    karlsruher.brain.store('rhein', 'pegel', pegel)
    karlsruher.brain.store('rhein', 'fluss', fluss)
    pegel_diff = pegel - int(old_pegel) if old_pegel else 0
    fluss_diff = fluss - int(old_fluss) if old_fluss else 0
    tweet = TWEET.format(pegel, pegel_diff, fluss, fluss_diff).strip()
    karlsruher.logger.info(tweet)
    if '--tweet' in sys.argv:
        karlsruher.tweet(tweet)
