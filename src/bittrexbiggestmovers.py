from __future__ import print_function
import json
import logging
import urllib2
import urllib
import time
import os
import requests
import boto3
from utils import *
from candles import candle, candlesInsights, calculatePercentageDiff
from marketsummary import MarketSummary
import time
import sys
from dao import *
from constants import *
from bittrexcore import *
from datetime import datetime
from pytz import timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class TopMover(object):
    def __init__(self):
        self.TopMoversPrice = 0
        self.TopMoversPriceWinnerStart = None
        self.TopMoversPriceWinnerEnd = None

        self.TopMoversVolume = 0
        self.TopMoversVolumeWinnerStart = None
        self.TopMoversVolumeWinnerEnd = None

def findBiggestMover(marketNames, go_back_intervals, btc_price, eth_price):
    latestInterval = calculateIntervalNumber(datetime.now(pytz.timezone('America/Los_Angeles')), 5)
    latestDate = datetime.now(pytz.timezone('America/Los_Angeles'))

    print("Latest Interval " + str(latestInterval))
    print("Latest Date " + str(latestDate))

    #latestDateInterval = latestDate.strftime("%Y-%m-%d") + "#" + str(latestInterval)
    endDateInterval = getPreviousDateInterval(inputdate=latestDate, current_interval=latestInterval, go_back_intervals=2)
    startDateInterval = getPreviousDateInterval(inputdate=latestDate, current_interval=latestInterval, go_back_intervals=go_back_intervals+2)

    topMoversResult = TopMover()

    for market in marketNames:
        logging.debug("Processing market {0}".format(market))

        if not market.startswith('USDT'):

            #so we first try to get the data for current interval but if it is not present, we shall try for one previous interval as well
            endMS = getMarketSummary(market, endDateInterval)

            if endMS and endMS.baseVolume >= 100:
                startMS = getMarketSummary(market, startDateInterval)

                #let check percentage diff in price
                try:
                    logging.debug('market {2} latest price is {0} and volume is {1}'.format(endMS.last, endMS.baseVolume, market))
                    logging.debug('market {2} one hour ago price is {0} and volume is {1}'.format(startMS.last, startMS.baseVolume, market))

                    priceDiff = calculatePercentageDiff(startMS.last, endMS.last)

                    logging.debug('market {0} price diff is {1}'.format(market, priceDiff))

                    if priceDiff > 0 and priceDiff > topMoversResult.TopMoversPrice:
                        topMoversResult.TopMoversPrice = priceDiff
                        topMoversResult.TopMoversPriceWinnerStart = startMS
                        topMoversResult.TopMoversPriceWinnerEnd = endMS

                except:
                    logging.error("Couldn't calculate price diff between startMS and endMS for market {0}".format(market))

                #let check percentage diff in volume
                try:
                    volumeDiff = calculatePercentageDiff(startMS.baseVolume, endMS.baseVolume)

                    if volumeDiff > 0 and volumeDiff > topMoversResult.TopMoversVolume:
                        topMoversResult.TopMoversVolume = volumeDiff
                        topMoversResult.TopMoversVolumeWinnerStart = startMS
                        topMoversResult.TopMoversVolumeWinnerEnd = endMS

                except:
                    logging.error("Couldn't calculate Volume diff between startMS and endMS for market {0}".format(market))

    #RESULTS
    if topMoversResult.TopMoversPriceWinnerStart and topMoversResult.TopMoversVolumeWinnerStart:
        ###############################
        #Price winners are
        startPrice = convertToDollar(topMoversResult.TopMoversPriceWinnerStart.last, btc_price, eth_price, topMoversResult.TopMoversPriceWinnerEnd.name)
        endPrice = convertToDollar(topMoversResult.TopMoversPriceWinnerEnd.last, btc_price, eth_price, topMoversResult.TopMoversPriceWinnerEnd.name)

        print("Price Rise Winner is market {0} and price gain is {1:.2f}. Start Time {2} End Time {3} Start Price {4:.5f} Last Price {5:.5f} %".format(
        topMoversResult.TopMoversPriceWinnerEnd.name, float(topMoversResult.TopMoversPrice),
        topMoversResult.TopMoversPriceWinnerStart.timestamp, topMoversResult.TopMoversPriceWinnerEnd.timestamp,
        startPrice, endPrice))

        ###############################
        #volume winners are
        startVolume = topMoversResult.TopMoversVolumeWinnerStart.baseVolume
        endVolume = topMoversResult.TopMoversVolumeWinnerEnd.baseVolume

        print("Volume Rise Winner is market {0} and Volume gain is {1:.2f}. Start Time {2} End Time {3} Start Volume {4:.5f} Last Volume {5:.5f} %".format(
        topMoversResult.TopMoversVolumeWinnerEnd.name, float(topMoversResult.TopMoversVolume),
        topMoversResult.TopMoversVolumeWinnerStart.timestamp, topMoversResult.TopMoversVolumeWinnerEnd.timestamp,
        startVolume, endVolume))

        hoursConsidered = go_back_intervals/12

        alertMessage = formatTelegramCryptoMoversLeadPlainTextMessage(hours=hoursConsidered,
        price_market_name=topMoversResult.TopMoversPriceWinnerEnd.name,
        price_gained=float(topMoversResult.TopMoversPrice),
        price_start_time=topMoversResult.TopMoversPriceWinnerStart.timestamp,
        price_end_time=topMoversResult.TopMoversPriceWinnerEnd.timestamp,
        price_start=startPrice,
        price_end=endPrice,
        volume_market_name=topMoversResult.TopMoversVolumeWinnerEnd.name,
        volume_gained=float(topMoversResult.TopMoversVolume),
        volume_start_time=topMoversResult.TopMoversVolumeWinnerStart.timestamp,
        volume_end_time=topMoversResult.TopMoversVolumeWinnerEnd.timestamp,
        volume_start=startVolume,
        volume_end=endVolume)

        #print('Alert Message : ' + json.dumps(alertMessage))
        #print('alert url ' + CRYPTO_MOVERS_LEADS_WEBHOOK)

        response = requests.post(CRYPTO_MOVERS_LEADS_WEBHOOK, data=json.dumps(alertMessage), headers={'Content-Type': 'application/json'})

        if response.status_code != 200:
            raise ValueError(
                'Request to telegram crypto movers leads returned an error %s, the response is:\n%s' % (response.status_code, response.text)
                )

        logging.info('Biggest Movers Alert Sent!')

    else:
        print('No Price Gainers or  Volume Gainers in go_back_intervals {0}'.format(go_back_intervals))

    return topMoversResult


def main(event, context):
    '''
        This method calculates biggest movers in terms of volume and price gains for every hour, every 3 hours, every 6 hours, every 12 hours and
        every 23 hours.
    '''

    btcPrice = float(getBTCPrice())
    ethPrice = getETHPrice(btcPrice)

    marketNames = getMarketNames(min_base_volume=CRYPTO_MOVERS_MARKETS_TO_WATCH_BASE_VOLUME_MIN)
    #marketNames = ['BTC-LTC', 'BTC-ETH', 'BTC-SC', 'BTC-XVG', 'BTC-NXS', 'BTC-XLM', 'BTC-XRP', 'ETH-LTC', 'ETH-XRP']

    logging.info("Considering {0} Markets".format(str(len(marketNames))))

    logging.info("Calculating for 1 hour window")
    topMoversResult_1Hour = findBiggestMover(marketNames=marketNames, go_back_intervals=12, btc_price=btcPrice, eth_price=ethPrice)
    logging.info("Calculating for 3 hour window")
    topMoversResult_3Hour = findBiggestMover(marketNames=marketNames, go_back_intervals=36, btc_price=btcPrice, eth_price=ethPrice)
    logging.info("Calculating for 6 hour window")
    topMoversResult_6Hour = findBiggestMover(marketNames=marketNames, go_back_intervals=72, btc_price=btcPrice, eth_price=ethPrice)
    logging.info("Calculating for 12 hour window")
    topMoversResult_12Hour = findBiggestMover(marketNames=marketNames, go_back_intervals=144, btc_price=btcPrice, eth_price=ethPrice)

if __name__ == "__main__":
    main(None, None)
