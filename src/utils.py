from __future__ import print_function
import logging
from constants import *
import urllib2
import json
import math
from datetime import datetime, timedelta
import pytz

pst_tz = pytz.timezone('US/Pacific')
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

def formatTelegramVolatilityLeadPlainTextMessage(market_name, text):
    return {
        'chat_id' : CRYPTO_VOLATILITY_LEADS_CHAT_ID,
        'text' : "https://bittrex.com/Market/Index?MarketName="+market_name+'\n'+text, 
    }

def formatTelegramCryptoMoversLeadPlainTextMessage(hours, price_market_name, price_gained, price_start_time, price_end_time, price_start,
price_end, volume_market_name, volume_gained, volume_start_time, volume_end_time, volume_start, volume_end):
    return {
        'chat_id' : CRYPTO_MOVERS_LEADS_CHAT_ID,
        'text' : 'Biggest Movers in past {0} hours\n\n\
Price Based\n\
https://bittrex.com/Market/Index?MarketName={1}\n\
Price Gained = {2:.5f}\n\
StartTime = {3}\n\
EndTime = {4}\n\
StartPrice = {5:.5f}\n\
EndPrice = {6:.5f}\n\
\n\n\
Volume Based\n\
https://bittrex.com/Market/Index?MarketName={7}\n\
Volume Gained = {8:.5f}\n\
StartTime = {9}\n\
EndTime = {10}\n\
StartVolume = {11:.5f}\n\
EndVolume = {12:.5f}'.format(str(hours), price_market_name, price_gained, price_start_time, price_end_time, price_start,
price_end,volume_market_name, volume_gained, volume_start_time, volume_end_time, volume_start, volume_end)
}





def formatTelegramCryptoMoversLeadHtmlMessage():
    return '<b>Biggest Movers in past {0} hours</b>\n\
        Price Based\n \
        <a href="https://bittrex.com/Market/Index?MarketName={1}" \
        Price Gained = {2}\n \
        StartTime = {3}\n \
        EndTime = {4}\n \
        StartPrice = {5}\n \
        EndPrice = {6}\n \
        \n\n \
        Volume Based\n \
        <a href="https://bittrex.com/Market/Index?MarketName={7}" \
        Volume Gained = {8}\n \
        StartTime = {9}\n \
        EndTime = {10}\n \
        StartVolume = {11}\n \
        EndVolume = {12}\n \
    '

def formatSlackHealthMessage(text):
    return {
        "text": text, #message you want to send
    }

def calculateIntervalNumber(timestamp, interval_size):
    '''
        this method takes in timestamp (datetime) and returns interval number starting from mid night.
        For example: 1:05 AM and interval size 5 min will return interval 13 since its been 13 5 minute inteval since midnight.
    '''
    d1 = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
    d2 = timestamp

    return int(math.ceil((d2-d1).total_seconds()/60/interval_size))

def utc_to_pst(input):
    return input.replace(tzinfo=pytz.utc).astimezone(pst_tz)

def convert_bittrex_timestamp_to_datetime(input):
    if "." in input:
        return datetime.strptime(input, '%Y-%m-%dT%H:%M:%S.%f').replace(microsecond=0)
    else:
        return datetime.strptime(input, '%Y-%m-%dT%H:%M:%S')

def get_epoch_time(input):
    epoch = datetime(1970,1,1)
    return (input-epoch).total_seconds()

def getPreviousDateInterval(inputdate, current_interval, go_back_intervals):
    if go_back_intervals > 288:
        raise Exception('Cannot go back more than 24 hours')

    new_interval = (((288 + current_interval) - abs(go_back_intervals)) % 288)+1

    return (inputdate - timedelta(days=1)).strftime("%Y-%m-%d") + "#" + str(new_interval) if (new_interval > current_interval) else inputdate.strftime("%Y-%m-%d") + "#" + str(new_interval)

def convertToDollar(price, btc_price, eth_price, market_name):
    if market_name.startswith('BTC'):
        return float(price) * btc_price
    elif market_name.startswith('ETH'):
        return float(price) * eth_price
    else:
        raise Exception('Invalid data provided to convertToDollar')

if __name__ == "__main__":
    #unit test
    #print(datetime.now())
    #print(calculateIntervalNumber(datetime.now(), 5))
    #print(calculateIntervalNumber(datetime.now(), 15))
    #print(utc_to_pst(datetime.strptime('2018-01-06T01:55:44.707', '%Y-%m-%dT%H:%M:%S.%f')))
    #print(get_epoch_time(datetime.now()))
    #print(getPreviousDateInterval(datetime.now(), 100, 1))
    #print(getPreviousDateInterval(datetime.now(), 100, 3))
    #print(getPreviousDateInterval(datetime.now(), 100, 36))
    #print(getPreviousDateInterval(datetime.now(), 100, 72))
    #print(getPreviousDateInterval(datetime.now(), 100, 144))
    print(formatTelegramCryptoMoversLeadPlainTextMessage())
