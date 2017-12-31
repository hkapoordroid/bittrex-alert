from __future__ import print_function
import logging
from constants import *
import urllib2
import json

logger = logging.getLogger()

def call_api(url):
    resp = urllib2.urlopen(url)
    return json.loads(resp.read())

def median(lst):
    n = len(lst)
    if n < 1:
            return None
    if n % 2 == 1:
            return sorted(lst)[n//2]
    else:
            return sum(sorted(lst)[n//2-1:n//2+1])/2.0

def formatSlackAlertMessage(alert_name, market_name, title, text, color):
    return {
        "attachments": [
        {
            "pretext": alert_name,
            "title": title,
            "title_link": "https://bittrex.com/Market/Index?MarketName="+market_name,
            "text": text,
            "color": color
        }
    ]
}

def formatSlackHealthMessage(text):
    return {
        "text": text, #message you want to send
    }
