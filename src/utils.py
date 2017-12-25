from __future__ import print_function
import logging
from constants import *

logger = logging.getLogger()

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
