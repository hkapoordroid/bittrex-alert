from __future__ import print_function
import json
import boto3
import logging
import urllib2
import time


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

ALERT_PRICE_CHANGE_THRESHOLD = 5
ALERT_VOLUME_CHANGE_THRESHOLD = 50
ALERT_VOLUME_MIN_THRESHOLD = 100


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

def alertOnDiffInPriceAndVolume(market_name, candles):
    '''
        This method checks past 2 intervals data to see if there is increase or decrease in price more than threshold
    '''

    if len(candles) < 2:
        raise Exception("Need atleast 2 intervals of candles data, {0}".format(candles))

    firstCandle = candles[-2]
    secondCandle = candles[-1]

    logging.debug("First Candle : {0}\n Second Candle : {1}".format(firstCandle, secondCandle))

    firstOpen = firstCandle['O']
    firstClose = firstCandle['C']
    firstVol = firstCandle['V']
    secondOpen = secondCandle['O']
    secondClose = secondCandle['C']
    secondVol = secondCandle['V']
    secondTime = secondCandle['T']

    firstPriceDiff = calculatePercentageDiff(firstOpen, firstClose)
    secondPriceDiff = calculatePercentageDiff(secondOpen, secondClose)
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
    sendAlert = False
    if abs(secondPriceDiff) > ALERT_PRICE_CHANGE_THRESHOLD and secondVol >= ALERT_VOLUME_MIN_THRESHOLD:
        sendAlert = True
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
        LastPrice:{7}{8}".format(market_name, secondTime, priceTrend, secondPriceDiff, volumeTrend, volumeDiff,
        secondVol, priceSymbol, secondClose)

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
    #marketsToWatch = None

    markets = marketsToWatch if marketsToWatch else allMarketNames

    logging.info("Going to watch following markets {0}".format(markets))
    snsAlertMsg = ""
    alertFound = False
    for market in markets:
        if market.startswith("BTC"):
            candles = getCandles(market, TICKINTERVAL_THIRTYMIN)
            alertMsg = alertOnDiffInPriceAndVolume(market, candles)
            logging.debug("Alert Message : {0}".format(str(alertMsg)))

            if alertMsg:
                snsAlertMsg = snsAlertMsg + '\n' + alertMsg
                alertFound = True

    if not alertFound:
        snsAlertMsg = "Nothing to alert on based on current thresholds. Min Volume {0} and Price Diff {1}".format(ALERT_VOLUME_MIN_THRESHOLD,
        ALERT_PRICE_CHANGE_THRESHOLD)

    logging.info("Final SNS Message to publish : {0}".format(snsAlertMsg))
    client.publish(TopicArn='arn:aws:sns:us-east-1:787766881935:bittrex-alerts',
    Message=snsAlertMsg,
    Subject='Bittrex Alert!',
    MessageStructure='string')



if __name__ == '__main__':
    main(None, None)
