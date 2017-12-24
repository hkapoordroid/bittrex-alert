from __future__ import print_function
import logging

logger = logging.getLogger()

BULLISH_COLOR = "#07EC23"
BEARISH_COLOR = "#FD2E02"
MIX_COLOR = "#F9F903"
DEFAULT_COLOR = "#FFFFFF"

BULLISH_TREND = "UP"
BEARISH_TREND = "DOWN"
MIX_TREND = "MIX"

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
