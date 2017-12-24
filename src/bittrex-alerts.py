from __future__ import print_function
import json
import logging
import urllib2
import time
import os
import requests
import boto3
from utils import *
from candles import candle, candlesInsights
import time

BUY_ORDERBOOK = 'buy'
SELL_ORDERBOOK = 'sell'
BOTH_ORDERBOOK = 'both'

TICKINTERVAL_ONEMIN = 'oneMin'
TICKINTERVAL_FIVEMIN = 'fiveMin'
TICKINTERVAL_HOUR = 'hour'
TICKINTERVAL_THIRTYMIN = 'thirtyMin'
TICKINTERVAL_DAY = 'Day'

INTERVALS_TO_CONSIDER = 6

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

BITTREX_ALERT_TITLE = "Bittrex Alert!"

BITTREX_GET_MARKETS_URL = "https://bittrex.com/api/v1.1/public/getmarkets"
BITTREX_GET_TICKS_URL = "https://bittrex.com/Api/v2.0/pub/market/GetTicks?marketName={0}&tickInterval={1}&_={2}"
BITTREX_GET_BTC_PRICE_URL = "https://bittrex.com/api/v2.0/pub/currencies/GetBTCPrice"
BITTREX_GET_ETH_PRICE_URL = "https://bittrex.com/Api/v2.0/pub/market/GetLatestTick?marketName=BTC-ETH&tickInterval=oneMin&_={0}"

DEFAULT_ALERT_PRICE_CHANGE_THRESHOLD = 3
DEFAULT_ALERT_VOLUME_CHANGE_THRESHOLD = 50
DEFAULT_ALERT_VOLUME_MIN_THRESHOLD = 50

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

def getBTCPrice():
    '''
        Returns BTC price in USD
    '''

    resp = call_api(BITTREX_GET_BTC_PRICE_URL)

    logging.debug('Get BTC Price response : {0}'.format(resp))

    if not resp:
        raise Exception("Could not retrieve btc price from bittrex")

    resultData = resp['result']

    if not resultData:
        raise Exception('Could not find result data in the bittrex get btc price response : {0}'.format(resp))

    btcPrice = resultData['bpi']['USD']['rate']

    return btcPrice

def getETHPrice(btc_price):
    '''
        Takes btc price in usd and returns eth price in USDT
    '''
    timestamp = str(int(time.time()))
    url = BITTREX_GET_ETH_PRICE_URL.format(timestamp)

    resp = call_api(url)

    logging.debug('Get Last ETH Ticks Response : {0}'.format(resp))

    tickData = resp['result']

    if not tickData:
        raise Exception("Could not find the ticks data in the bittrex response : {0}".format(resp))

    ethPriceInBTC = tickData[0]['C']

    return ethPriceInBTC*btc_price


def getCandles(market_name, interval_size, intervals_to_retrieve=6):
    '''
        Get latest candles data for given market, interval size and interval numbers
    '''
    timestamp = str(int(time.time()))
    url = BITTREX_GET_TICKS_URL.format(market_name, interval_size, timestamp)
    #form the urllib
    logging.debug("Get candles data for market {0} using url {1}".format(market_name, url))

    resp = call_api(url)

    logging.debug('Get Ticks Response : {0}'.format(resp))

    tickData = resp['result']

    if not tickData:
        raise Exception("Could not find the ticks data in the bittrex response : {0}".format(resp))

    logging.debug("Tick Data for Market {0} is {1}".format(market_name, tickData))

    if len(tickData) < intervals_to_retrieve:
        intervals_to_retrieve = len(tickData)

    candles = list()
    for data in tickData[-intervals_to_retrieve:]:
        c = candle(data['H'], data['L'], data['O'], data['C'], data['V'], interval_size, data['T'])
        candles.append(c)
        logging.debug(c)

    return candles

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

    marketsToWatch = ["BTC-LTC", "BTC-ETH", "BTC-BCC", "BTC-XRP", "BTC-ADA", "BTC-DASH", "BTC-XMR", "BTC-BTG", "BTC-XLM",
    "BTC-NEO", "BTC-NEOS", "BTC-ETC", "BTC-QTUM", "BTC-LSK", "BTC-OMG", "BTC-ZEC", "BTC-WAVES", "BTC-STRAT", "BTC-ARDR", "BTC-NXT",
    "BTC-XVG", "BTC-MONA", "BTC-DOGE", "BTC-SNT", "BTC-STEEM", "BTC-ARK", "BTC-DCR", "BTC-EMC2", "BTC-KMD", "BTC-SALT", "BTC-REP",
    "BTC-SC", "BTC-PIVX", "BTC-GNT", "BTC-PAY", "BTC-VTC", "BTC-GBYTE", "BTC-DGB",
    "ETH-LTC","ETH-BCC","ETH-XRP","ETH-ADA", "ETH-DASH", "ETH-XMR", "ETH-BTG", "ETH-XLM","ETH-NEO", "ETH-ETC", "ETH-QTUM", "ETH-OMG",
    "ETH-ZEC", "ETH-WAVES", "ETH-STRAT", "ETH-MCO", "ETH-SNT", "ETH-SALT", "ETH-REP", "ETH-SC", "ETH-GNT", "ETH-PAY", "ETH-DGB"]

    #marketsToWatch = ["BTC-SC"]
    #marketsToWatch = ["ETH-XRP"]

    #Get the algorithm configuration params from env if exists else use defaults
    priceChangeThreshold = int(os.environ.get('ALERT_PRICE_CHANGE_THRESHOLD')) if os.environ.get('ALERT_PRICE_CHANGE_THRESHOLD') else DEFAULT_ALERT_PRICE_CHANGE_THRESHOLD
    volumeChangeThreshold = int(os.environ.get('ALERT_VOLUME_CHANGE_THRESHOLD')) if os.environ.get('ALERT_VOLUME_CHANGE_THRESHOLD') else DEFAULT_ALERT_VOLUME_CHANGE_THRESHOLD
    volumeMinThreshold = int(os.environ.get('ALERT_VOLUME_MIN_THRESHOLD')) if os.environ.get('ALERT_VOLUME_MIN_THRESHOLD') else DEFAULT_ALERT_VOLUME_MIN_THRESHOLD
    intervalSize = os.environ.get('ALERT_INTERVAL') if os.environ.get('ALERT_INTERVAL') else TICKINTERVAL_FIVEMIN
    intervalsToConsider = os.environ.get('INTERVALS_TO_CONSIDER') if os.environ.get('INTERVALS_TO_CONSIDER') else INTERVALS_TO_CONSIDER
    snsTopicARN = os.environ.get('SNS_TOPIC_ARN')

    if not snsTopicARN:
        raise Exception('Please provide sns topic arn as environment variable.')
        #example: prod : 'arn:aws:sns:us-east-1:787766881935:bittrex-alerts'
        #beta : 'arn:aws:sns:us-east-1:787766881935:beta-bittrex-alerts'

    logging.info("ALERT_PRICE_CHANGE_THRESHOLD : {0}\n \
    ALERT_VOLUME_CHANGE_THRESHOLD : {1}\n \
    ALERT_VOLUME_MIN_THRESHOLD : {2}\n \
    ALERT_INTERVALS : {3}\n".format(priceChangeThreshold,
    volumeChangeThreshold, volumeMinThreshold, intervalSize))

    markets = marketsToWatch if marketsToWatch else allMarketNames

    #Get the BTC Price
    btcPrice = float(getBTCPrice().replace(",",""))
    ethPrice = float(getETHPrice(btcPrice))
    logging.info("Current BTC Price {0}".format(btcPrice))
    logging.info("Current ETH Price {0}".format(ethPrice))

    logging.debug("Going to watch following markets {0}".format(markets))
    alertMsgBuilder = list()
    alertFound = False
    for market in markets:

        logging.info("Processing market {0}".format(market))
        time.sleep(1)#in order to avoid getting throtled

        dollarMultipler = None

        if market.startswith("BTC"):
            dollarMultipler = btcPrice
        elif market.startswith("ETH"):
            dollarMultipler = ethPrice
        else:
            raise Exception("Unsupported Market being analyzed {0}".format(market))

        candlesList = getCandles(market, intervalSize, intervalsToConsider)
        candlesInsightsObj = candlesInsights(candlesList)

        #alertMsg = alertOnDiffInPriceAndVolume(market, candles, priceChangeThreshold, volumeChangeThreshold, volumeMinThreshold)
        priceTrendData = candlesInsightsObj.getPriceTrend()
        volumeTrendData = candlesInsightsObj.getVolumeTrend()

        #apply the alert threshold rules
        #priceTrendData is tuple of format (priceDiff, greenCandlesCount, redCandlesCount, priceTrend, intervalsOpenPrice, intervalsClosePrice. lastIntervalTimestamp)
        #volumeTrendData is tuple of format (volumeDiff, volumeTrend, firstIntervalVolume, lastIntervalVolume)
        if abs(priceTrendData[0]) > priceChangeThreshold and volumeTrendData[3] > volumeMinThreshold:
            alertText = "Time: {0}\n\nPriceTrend: {1}\nPriceDiff: {2:.2f}%\n\nVolumeTrend: {3}\n\
VolumeDiff: {4:.2f}%\n\nLastIntervalVolume: {5:.2f} BTC\nIntervalsOpenPrice: ${6:.4f}\n\
IntervalsClosePrice: ${7:.4f}\nGreenCandles: {8}\nRedCandles: {9}\nIntervalSize: {10}\n\
IntervalsConsidered: {11}".format(priceTrendData[6], priceTrendData[3], priceTrendData[0],
volumeTrendData[1], volumeTrendData[0], volumeTrendData[3], priceTrendData[4]*dollarMultipler,
priceTrendData[5]*dollarMultipler, priceTrendData[1], priceTrendData[2],
intervalSize, intervalsToConsider)

            msgColor = MIX_COLOR
            if priceTrendData[3] == BULLISH_TREND and volumeTrendData[1] == BULLISH_TREND:
                msgColor = BULLISH_COLOR
            elif priceTrendData[3] == BEARISH_TREND and volumeTrendData[1] == BEARISH_TREND:
                msgColor = BEARISH_COLOR

            publishMsg = formatSlackAlertMessage(BITTREX_ALERT_TITLE, market, market, alertText, msgColor)
            logging.info(publishMsg)
            alertMsgBuilder.append(publishMsg)
            alertFound = True

    if not alertFound:
        publishMsg = formatSlackHealthMessage("Boring Market!\nNothing to alert on based on current thresholds.")
        alertMsgBuilder.append(publishMsg)
        webhook_url = HEALTHCHECK_SLACK_WEBHOOK
    else:
        webhook_url = LEADS_SLACK_WEBHOOK

    if event: #this prevents from sending alerts during testing on local machine
        for msg in alertMsgBuilder:
            '''
            client.publish(TopicArn=snsTopicARN,
            Message=snsAlertMsg,
            Subject='Bittrex Alert!',
            MessageStructure='string')
            logging.info('Published to SNS Topic {0}'.format(snsTopicARN))
            '''

            response = requests.post(webhook_url, data=json.dumps(msg), headers={'Content-Type': 'application/json'})
            if response.status_code != 200:
                raise ValueError(
                    'Request to slack returned an error %s, the response is:\n%s' % (response.status_code, response.text)
                    )


if __name__ == '__main__':
    main(None, None)
