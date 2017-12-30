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
import sys
from dao import *
from constants import *

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

def main(event, context):
    '''
        main function which executes the alerts
    '''
    allMarketNames = getMarketNames()


    #removed on 12/30/2017
    #"BTC-ETC", "BTC-BTG", "BTC-WAVES", "BTC-STRAT", "BTC-ARDR", "BTC-MONA", "BTC-DOGE", "BTC-SNT", "BTC-DCR", "BTC-EMC2", "BTC-KMD", "BTC-PIVX",
    # "BTC-PAY", "BTC-VTC", "BTC-GBYTE",
    # "ETH-BTG", "ETH-ETC", "ETH-WAVES", "ETH-STRAT", "ETH-MCO", "ETH-SNT", "ETH-PAY", 

    marketsToWatch = ["BTC-LTC", "BTC-ETH", "BTC-BCC", "BTC-XRP", "BTC-ADA", "BTC-DASH", "BTC-XMR", "BTC-XLM",
    "BTC-NEO", "BTC-NEOS", "BTC-QTUM", "BTC-LSK", "BTC-OMG", "BTC-ZEC", "BTC-NXT",
    "BTC-XVG", "BTC-STEEM", "BTC-ARK", "BTC-SALT", "BTC-REP", "BTC-SC", "BTC-GNT", "BTC-DGB",
    "ETH-LTC", "ETH-BCC", "ETH-XRP", "ETH-ADA", "ETH-DASH", "ETH-XMR", "ETH-XLM","ETH-NEO", "ETH-QTUM", "ETH-OMG",
    "ETH-ZEC", "ETH-SALT", "ETH-REP", "ETH-SC", "ETH-GNT", "ETH-DGB"]

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

        candlesList = None
        try:
            candlesList = getCandles(market, intervalSize, intervalsToConsider)
        except:
            logging.error("Couldn't find data for market {0} : {1}".format(market, sys.exc_info()[0]))

        if candlesList:
            candlesInsightsObj = candlesInsights(candlesList)

            #alertMsg = alertOnDiffInPriceAndVolume(market, candles, priceChangeThreshold, volumeChangeThreshold, volumeMinThreshold)
            priceTrendData = candlesInsightsObj.getPriceTrend()
            volumeTrendData = candlesInsightsObj.getVolumeTrend()

            #apply the alert threshold rules
            #priceTrendData is tuple of format (priceDiff, greenCandlesCount, redCandlesCount, priceTrend, intervalsOpenPrice, intervalsClosePrice. lastIntervalTimestamp)
            #volumeTrendData is tuple of format (volumeDiff, volumeTrend, firstIntervalVolume, lastIntervalVolume)
            logging.info("PriceDiff {0}\nLastIntervalVolume {1}\npriceChangeThreshold {2}\nvolumeMinThreshold {3}".format(
            abs(float(priceTrendData[0])), abs(float(volumeTrendData[3])), priceChangeThreshold, volumeMinThreshold))

            if abs(float(priceTrendData[0])) > float(priceChangeThreshold) and abs(float(volumeTrendData[3])) > float(volumeMinThreshold):
                alertText = "Time: {0}\n\nPriceTrend: {1}\nPriceDiff: {2:.2f}%\n\nVolumeTrend: {3}\n\
    VolumeDiff: {4:.2f}%\n\nLastIntervalVolume: {5:.2f} BTC\nIntervalsOpenPrice: ${6:.4f}\n\
    IntervalsClosePrice: ${7:.4f}\nGreenCandles: {8}\nRedCandles: {9}\nIntervalSize: {10}\n\
    IntervalsConsidered: {11}".format(priceTrendData[6], priceTrendData[3], priceTrendData[0],
    volumeTrendData[1], volumeTrendData[0], volumeTrendData[3], priceTrendData[4]*dollarMultipler,
    priceTrendData[5]*dollarMultipler, priceTrendData[1], priceTrendData[2],
    intervalSize, intervalsToConsider)

                msgColor = MIX_COLOR
                signalType = SIGNAL_TYPE_NA
                if priceTrendData[3] == BULLISH_TREND and volumeTrendData[1] == BULLISH_TREND:
                    msgColor = BULLISH_COLOR
                    signalType = SIGNAL_TYPE_BUY
                elif priceTrendData[3] == BEARISH_TREND and volumeTrendData[1] == BEARISH_TREND:
                    msgColor = BEARISH_COLOR
                    signalType = SIGNAL_TYPE_SELL

                #persist the signal which we are about to send for later analysis
                if signalType in [SIGNAL_TYPE_BUY, SIGNAL_TYPE_SELL]:
                    publishMsg = formatSlackAlertMessage(BITTREX_ALERT_TITLE, market, market, alertText, msgColor)
                    logging.debug(publishMsg)
                    alertMsgBuilder.append(publishMsg)
                    alertFound = True
                    logging.info("Alert Found!")
                    insertSignal(market_name=market, timestamp=priceTrendData[6], signal_type=signalType, price_trend=priceTrendData[3],
                    price_diff=priceTrendData[0], volume_trend=volumeTrendData[1], volume_diff=volumeTrendData[0],
                    last_interval_volume=volumeTrendData[3], intervals_open_price=priceTrendData[4]*dollarMultipler,
                    intervals_close_price=priceTrendData[5]*dollarMultipler, green_candles_count=priceTrendData[1],
                    red_candles_count=priceTrendData[2], interval_size=intervalSize, intervals_considered=intervalsToConsider,
                    price_change_threshold=priceChangeThreshold, volume_min_threshold=volumeMinThreshold,
                    volume_change_threshold=volumeChangeThreshold)

    if not alertFound:
        publishMsg = formatSlackHealthMessage("Boring Market!\nNothing to alert on based on current thresholds.")
        alertMsgBuilder.append(publishMsg)
        webhook_url = HEALTHCHECK_SLACK_WEBHOOK
    else:
        webhook_url = LEADS_SLACK_WEBHOOK

    if alertFound:#Currently stopping sending health messages, I'll set that up using cloudwatch alarms
        logging.info("Total alerts to send {0}".format(len(alertMsgBuilder)))

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
