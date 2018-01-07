from __future__ import print_function
import json
import logging
import urllib2
import time
import os
import requests
import boto3
from utils import *
from candles import candle, candlesInsights, calculatePercentageDiff
import time
import sys
from dao import *
from constants import *
from bittrexcore import *


logger = logging.getLogger()
logger.setLevel(logging.INFO)

client = boto3.client('sns')

def main(event, context):
    '''
        main function which executes the alerts
    '''
    allMarketNames = getMarketNames(min_base_volume=CRYPTO_VOLATILITY_MARKETS_TO_WATCH_BASE_VOLUME_MIN)



    #Get the algorithm configuration params from env if exists else use defaults
    priceChangeThreshold = int(os.environ.get('ALERT_PRICE_CHANGE_THRESHOLD')) if os.environ.get('ALERT_PRICE_CHANGE_THRESHOLD') else DEFAULT_ALERT_PRICE_CHANGE_THRESHOLD
    volumeChangeThreshold = int(os.environ.get('ALERT_VOLUME_CHANGE_THRESHOLD')) if os.environ.get('ALERT_VOLUME_CHANGE_THRESHOLD') else DEFAULT_ALERT_VOLUME_CHANGE_THRESHOLD
    volumeMinThreshold = int(os.environ.get('ALERT_VOLUME_MIN_THRESHOLD')) if os.environ.get('ALERT_VOLUME_MIN_THRESHOLD') else DEFAULT_ALERT_VOLUME_MIN_THRESHOLD
    intervalSize = os.environ.get('ALERT_INTERVAL') if os.environ.get('ALERT_INTERVAL') else TICKINTERVAL_FIVEMIN
    intervalsToConsider = os.environ.get('INTERVALS_TO_CONSIDER') if os.environ.get('INTERVALS_TO_CONSIDER') else INTERVALS_TO_CONSIDER
    snsTopicARN = os.environ.get('SNS_TOPIC_ARN')

    logging.info("ALERT_PRICE_CHANGE_THRESHOLD : {0}\n \
    ALERT_VOLUME_CHANGE_THRESHOLD : {1}\n \
    ALERT_VOLUME_MIN_THRESHOLD : {2}\n \
    ALERT_INTERVALS : {3}\n".format(priceChangeThreshold,
    volumeChangeThreshold, volumeMinThreshold, intervalSize))

    #markets = MARKETS_TO_WATCH if MARKETS_TO_WATCH else allMarketNames
    markets = allMarketNames

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

            if abs(float(priceTrendData[0])) > float(priceChangeThreshold): #and abs(float(volumeTrendData[3])) > float(volumeMinThreshold):

                #check for volume movements
                marketMedianVolumeData = getMedianVolume(market)

                print(marketMedianVolumeData)
                #if there is a change in median volume in past 15 mins compared to median volume in past 24 hours, we have a situation to observe
                medianVolumeChange = calculatePercentageDiff(marketMedianVolumeData.OneDayMedianVolume, marketMedianVolumeData.FifteenMinMedianVolume)

                volumeTrend = 'NA'
                if marketMedianVolumeData.FifteenMinMedianVolume > marketMedianVolumeData.OneDayMedianVolume:
                    volumeTrend = 'UP'
                else:
                    volumeTrend = 'DOWN'

                alertText = "Time: {0}\n\nPriceTrend: {1}\nPriceDiff: {2:.2f}%\n\nVolumeTrend: {3}\n\
MedianVolumeDiff: {4:.2f}%\n\nIntervalsOpenPrice: ${5:.4f}\n\
IntervalsClosePrice: ${6:.4f}\nGreenCandles: {7}\nRedCandles: {8}\nIntervalSize: {9}\n\
IntervalsConsidered: {10}".format(priceTrendData[6], priceTrendData[3], priceTrendData[0],
    volumeTrend, medianVolumeChange, priceTrendData[4]*dollarMultipler,
    priceTrendData[5]*dollarMultipler, priceTrendData[1], priceTrendData[2],
    intervalSize, intervalsToConsider)

                msgColor = MIX_COLOR
                signalType = SIGNAL_TYPE_NA
                if priceTrendData[3] == BULLISH_TREND:#and volumeTrendData[1] == BULLISH_TREND:
                    msgColor = BULLISH_COLOR
                    signalType = SIGNAL_TYPE_BUY
                elif priceTrendData[3] == BEARISH_TREND:# and volumeTrendData[1] == BEARISH_TREND:
                    msgColor = BEARISH_COLOR
                    signalType = SIGNAL_TYPE_SELL

                #persist the signal which we are about to send for later analysis
                if signalType in [SIGNAL_TYPE_BUY, SIGNAL_TYPE_SELL]:
                    #publishMsg = formatSlackAlertMessage(BITTREX_ALERT_TITLE, market, market, alertText, msgColor)
                    publishMsg = formatTelegramVolatilityLeadPlainTextMessage(market, alertText)
                    logging.debug(publishMsg)
                    alertMsgBuilder.append(publishMsg)
                    alertFound = True
                    logging.info("Alert Found!")

                    #Dsiabling stopring of signals data 12/31/2017
                    '''
                    insertSignal(market_name=market, timestamp=priceTrendData[6], signal_type=signalType, price_trend=priceTrendData[3],
                    price_diff=priceTrendData[0], volume_trend=volumeTrendData[1], volume_diff=volumeTrendData[0],
                    last_interval_volume=volumeTrendData[3], intervals_open_price=priceTrendData[4]*dollarMultipler,
                    intervals_close_price=priceTrendData[5]*dollarMultipler, green_candles_count=priceTrendData[1],
                    red_candles_count=priceTrendData[2], interval_size=intervalSize, intervals_considered=intervalsToConsider,
                    price_change_threshold=priceChangeThreshold, volume_min_threshold=volumeMinThreshold,
                    volume_change_threshold=volumeChangeThreshold)
                    '''

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

            '''
            #slack web hook
            response = requests.post(webhook_url, data=json.dumps(msg), headers={'Content-Type': 'application/json'})
            '''

            response = requests.post(CRYPTO_VOLATILITY_LEADS_WEBHOOK, data=json.dumps(msg), headers={'Content-Type': 'application/json'})

            if response.status_code != 200:
                raise ValueError(
                    'Request to slack returned an error %s, the response is:\n%s' % (response.status_code, response.text)
                    )


            logging.info("Alert Sent!")


if __name__ == '__main__':
    main(None, None)
