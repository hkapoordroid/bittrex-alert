from __future__ import print_function
from constants import *
import logging
import time
import sys
from bittrexcore import *
from dao import *

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def main(event, context):
    '''
        main function which identifies volume movement of the crypto's
    '''
    intervalSize = TICKINTERVAL_FIVEMIN
    intervalsToConsider = 288 #5 min intervals for past 24 hours

    logger.info("Starting to calculate media volume for markets")

    for market in MARKETS_TO_WATCH:
        logging.info("Processing market {0}".format(market))
        time.sleep(1)#in order to avoid getting throtled

        candlesList = None
        try:
            candlesList = getCandles(market, intervalSize, intervalsToConsider)
        except:
            logging.error("Couldn't find data for market {0} : {1}".format(market, sys.exc_info()[0]))

        if candlesList:
            candlesInsightsObj = candlesInsights(candlesList)

            fifteenMinMedianVolume = candlesInsightsObj.getMedianVolume(candlesToConsider=3)
            oneHourMedianVolume = candlesInsightsObj.getMedianVolume(candlesToConsider=12)
            threeHourMedianVolume = candlesInsightsObj.getMedianVolume(candlesToConsider=36)
            oneDayMedianVolume = candlesInsightsObj.getMedianVolume(candlesToConsider=288)

            logging.info("Fifteen Min Median Volume for market {0} is {1}".format(market, fifteenMinMedianVolume))
            logging.info("One Hour Median Volume for market {0} is {1}".format(market, oneHourMedianVolume))
            logging.info("Three Hours Median Volume for market {0} is {1}".format(market, threeHourMedianVolume))
            logging.info("One Day Median Volume for market {0} is {1}".format(market, oneDayMedianVolume))

            insertMedianVolume(market_name=market, fifteen_min_median_volume=fifteenMinMedianVolume,
            one_hour_median_volume=oneHourMedianVolume, three_hour_median_volume=threeHourMedianVolume,
            one_day_median_volume=oneDayMedianVolume)


if __name__ == "__main__":
    main(None, None)
