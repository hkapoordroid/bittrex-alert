from __future__ import print_function
import json
import logging
import urllib2
import time
import os
import requests
import boto3

BUY_ORDERBOOK = 'buy'
SELL_ORDERBOOK = 'sell'
BOTH_ORDERBOOK = 'both'

TICKINTERVAL_ONEMIN = 'oneMin'
TICKINTERVAL_FIVEMIN = 'fiveMin'
TICKINTERVAL_HOUR = 'hour'
TICKINTERVAL_THIRTYMIN = 'thirtyMin'
TICKINTERVAL_DAY = 'Day'

ORDERTYPE_LIMIT = 'LIMIT'
ORDERTYPE_MARKET = 'MARKET'

TIMEINEFFECT_GOOD_TIL_CANCELLED = 'GOOD_TIL_CANCELLED'
TIMEINEFFECT_IMMEDIATE_OR_CANCEL = 'IMMEDIATE_OR_CANCEL'
TIMEINEFFECT_FILL_OR_KILL = 'FILL_OR_KILL'

CONDITIONTYPE_NONE = 'NONE'
CONDITIONTYPE_GREATER_THAN = 'GREATER_THAN'
CONDITIONTYPE_LESS_THAN = 'LESS_THAN'
CONDITIONTYPE_STOP_LOSS_FIXED = 'STOP_LOSS_FIXED'
CONDITIONTYPE_STOP_LOSS_PERCENTAGE = 'STOP_LOSS_PERCENTAGE'

BITTREX_GET_MARKETS_URL = "https://bittrex.com/api/v1.1/public/getmarkets"
BITTREX_GET_TICKS_URL = "https://bittrex.com/Api/v2.0/pub/market/GetTicks?marketName={0}&tickInterval={1}&_={2}"

DEFAULT_ALERT_PRICE_CHANGE_THRESHOLD = 5
DEFAULT_ALERT_VOLUME_CHANGE_THRESHOLD = 50
DEFAULT_ALERT_VOLUME_MIN_THRESHOLD = 100

HEALTHCHECK_SLACK_WEBHOOK = "https://hooks.slack.com/services/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"
LEADS_SLACK_WEBHOOK = "https://hooks.slack.com/services/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"
webhook_url = ""

logger = logging.getLogger()
logger.setLevel(logging.INFO)

client = boto3.client('sns')

def call_api(url):
    resp = urllib2.urlopen(url)
    return json.loads(resp.read())

def getMarketNames():
    '''
        this method gets all market names from bittrex
    '''

    resp = call_api(BITTREX_GET_MARKETS_URL)

    logging.debug('Get Markets Response : {0}'.format(resp))

    if not resp:
        raise Exception("Could not retrieve markets from bittrex")

    marketData = resp['result']

    if not marketData:
        raise Exception("Could not find market data in the bittrex response : {0}".format(resp))

    logging.debug("Market Data is {0}".format(marketData))

    marketNames = [x['MarketName'] for x in marketData]
    logging.debug("Market Names Retrieved are {0}".format(marketNames))

    return marketNames


def getCandles(market_name, interval):
    '''
        Get candles data for given market and interval
    '''
    timestamp = str(int(time.time()))
    url = BITTREX_GET_TICKS_URL.format(market_name, interval, timestamp)
    #form the urllib
    logging.info("Get candles data for market {0} using url {1}".format(market_name, url))

    resp = call_api(url)

    logging.debug('Get Ticks Response : {0}'.format(resp))

    tickData = resp['result']

    if not tickData:
        raise Exception("Could not find the ticks data in the bittrex response : {0}".format(resp))

    logging.debug("Tick Data for Market {0} is {1}".format(market_name, tickData))

    return tickData

def calculatePercentageDiff(start_val, end_val):
    '''
        Given 2 values it find the percentage increase or decrease between values_1 and value_2
    '''
    valDiff = abs(start_val - end_val)
    valPercDiff = valDiff/start_val if start_val < end_val else (valDiff/end_val)*-1

    return valPercDiff*100

def alertOnDiffInPriceAndVolume(market_name, candles, priceChangeThreshold, volumeChangeThreshold, volumeMinThreshold):
    '''
        This method checks past 2 intervals data to see if there is increase or decrease in price more than threshold
    '''

    if len(candles) < 2:
        raise Exception("Need atleast 2 intervals of candles data, {0}".format(candles))

    firstCandle = candles[-2]
    secondCandle = candles[-1]

    logging.debug("First Candle : {0}\n Second Candle : {1}".format(firstCandle, secondCandle))
    logging.debug("priceChangeThreshold : {0} \n volumeChangeThreshold : {1} \n volumeMinThreshold : {2}".format(priceChangeThreshold,
    volumeChangeThreshold,volumeMinThreshold))

    firstOpen = firstCandle['O']
    firstClose = firstCandle['C']
    firstVol = firstCandle['V']
    secondOpen = secondCandle['O']
    secondClose = secondCandle['C']
    secondVol = secondCandle['V']
    secondTime = secondCandle['T']

    if market_name.startswith("BTC"):
        multipler = 100000000
    else:
        multipler = 1

    firstPriceDiff = calculatePercentageDiff(firstOpen*multipler, firstClose*multipler)
    secondPriceDiff = calculatePercentageDiff(secondOpen*multipler, secondClose*multipler)
    volumeDiff = calculatePercentageDiff(firstVol, secondVol)

    #first lets check if volume has increase or decreased
    volumeTrend = "Down"
    if secondVol > firstVol:
        volumeTrend = "UP"

    #lets check trend of price change
    priceTrend = "NA"
    if firstClose > firstOpen and secondClose > secondOpen:
        priceTrend = 'UP'
    elif firstClose < firstOpen and secondClose < secondOpen:
        priceTrend = 'Down'
    else:
        priceTrend = 'Mix'

    #lets check against the threshold values
    logging.info('secondPriceDiff : {0}\n secondVol : {1}\n priceChangeThreshold : {2}\n volumeMinThreshold : {3}'.format(
        secondPriceDiff, secondVol, priceChangeThreshold, volumeMinThreshold))
    sendAlert = False

    if abs(secondPriceDiff) > priceChangeThreshold and secondVol > volumeMinThreshold:
        sendAlert = True

    #if int(secondVol) >= volumeMinThreshold:
    #    sendAlert = True
    #    logging.info("send alert true for market {0}".format(market_name))
    #if abs(volumeDiff) > ALERT_VOLUME_CHANGE_THRESHOLD:
    #    sendAlert = True

    priceSymbol = ""
    if market_name.startswith("USDT"):
        priceSymbol = "$"
    elif market_name.startswith("BTC"):
        priceSymbol = "BTC"
    elif market_name.startswith("LTC"):
        priceSymbol = "LTC"
    elif market_name.startswith("ETH"):
        priceSymbol = "ETH"

    alertMsg = None
    if sendAlert:
        alertMsg = "Market:{0}\n \
        Time:{1}\n \
        PriceTrend:{2}\n \
        PriceDiff:{3:.2f}%\n \
        VolumeTrend:{4}\n \
        VolumeDiff:{5:.2f}%\n \
        LastIntervalVolume:{6:.2f}\n \
        LastPrice:{7}{8}\n \
        https://bittrex.com/Market/Index?MarketName={9}\n\n".format(market_name, secondTime, priceTrend, secondPriceDiff, volumeTrend, volumeDiff,
        secondVol, priceSymbol, secondClose,market_name)

    return alertMsg


def main(event, context):
    '''
        main function which executes the alerts
    '''
    allMarketNames = getMarketNames()
    marketsToWatch = ["USDT-BTC", "BTC-LTC", "BTC-ETH", "BTC-BCC", "BTC-XRP", "BTC-ADA", "BTC-DASH", "BTC-XMR", "BTC-BTG", "BTC-XLM",
    "BTC-NEO", "BTC-NEOS", "BTC-ETC", "BTC-QTUM", "BTC-LSK", "BTC-OMG", "BTC-ZEC", "BTC-WAVES",
    "BTC-STRAT", "BTC-ARDR", "BTC-NXT", "BTC-XVG", "BTC-MONA", "BTC-DOGE", "BTC-SNT", "BTC-STEEM", "BTC-ARK", "BTC-DCR", "BTC-EMC2",
    "BTC-KMD", "BTC-SALT", "BTC-REP", "BTC-SC", "BTC-PIVX", "BTC-GNT", "BTC-PAY", "BTC-VTC", "BTC-GBYTE", "BTC-DGB"]

    #marketsToWatch = ["BTC-QTUM"]

    #Get the algorithm configuration params from env if exists else use defaults
    priceChangeThreshold = int(os.environ.get('ALERT_PRICE_CHANGE_THRESHOLD')) if os.environ.get('ALERT_PRICE_CHANGE_THRESHOLD') else DEFAULT_ALERT_PRICE_CHANGE_THRESHOLD
    volumeChangeThreshold = int(os.environ.get('ALERT_VOLUME_CHANGE_THRESHOLD')) if os.environ.get('ALERT_VOLUME_CHANGE_THRESHOLD') else DEFAULT_ALERT_VOLUME_CHANGE_THRESHOLD
    volumeMinThreshold = int(os.environ.get('ALERT_VOLUME_MIN_THRESHOLD')) if os.environ.get('ALERT_VOLUME_MIN_THRESHOLD') else DEFAULT_ALERT_VOLUME_MIN_THRESHOLD
    intervals = os.environ.get('ALERT_INTERVAL') if os.environ.get('ALERT_INTERVAL') else TICKINTERVAL_THIRTYMIN
    snsTopicARN = os.environ.get('SNS_TOPIC_ARN')

    if not snsTopicARN:
        raise Exception('Please provide sns topic arn as environment variable.')
        example: prod : 'arn:aws:sns:us-east-1:787766881935:bittrex-alerts'
        beta : 'arn:aws:sns:us-east-1:787766881935:beta-bittrex-alerts'

    logging.info("ALERT_PRICE_CHANGE_THRESHOLD : {0}\n \
    ALERT_VOLUME_CHANGE_THRESHOLD : {1}\n \
    ALERT_VOLUME_MIN_THRESHOLD : {2}\n \
    ALERT_INTERVALS : {3}\n".format(priceChangeThreshold,
    volumeChangeThreshold, volumeMinThreshold, intervals))

    markets = marketsToWatch if marketsToWatch else allMarketNames

    logging.info("Going to watch following markets {0}".format(markets))
    snsAlertMsg = ""
    alertFound = False
    for market in markets:
        if market.startswith("BTC"):
            candles = getCandles(market, intervals)
            alertMsg = alertOnDiffInPriceAndVolume(market, candles, priceChangeThreshold, volumeChangeThreshold, volumeMinThreshold)
            logging.debug("Alert Message : {0}".format(str(alertMsg)))

            if alertMsg:
                snsAlertMsg = snsAlertMsg + '\n' + alertMsg
                alertFound = True
                webhook_url = LEADS_SLACK_WEBHOOK

    if not alertFound:
        snsAlertMsg = "Nothing to alert on based on current thresholds. Min Volume {0} and Price Diff {1}".format(volumeMinThreshold,
        priceChangeThreshold)
        webhook_url = HEALTHCHECK_SLACK_WEBHOOK

    logging.info("Final SNS Message to publish : {0}".format(snsAlertMsg))

    payload = {
        "text": snsAlertMsg, #message you want to send
    }

    if event: #this prevents from sending alerts during testing on local machine
        client.publish(TopicArn=snsTopicARN,
        Message=snsAlertMsg,
        Subject='Bittrex Alert!',
        MessageStructure='string')
        logging.info('Published to SNS Topic {0}'.format(snsTopicARN))
        response = requests.post(webhook_url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        if response.status_code != 200:
            raise ValueError(
                'Request to slack returned an error %s, the response is:\n%s' % (response.status_code, response.text)
                )

if __name__ == '__main__':
    main(None, None)
