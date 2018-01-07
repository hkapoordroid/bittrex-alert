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




def main(event, context):
    '''
        This method scans the bittrex to get all markets summaries and persist in the DDB
    '''
    logging.info("Start to get market summaries")

    marketSummaries = getMarketSummaries()

    logging.info("Got back market summaries for {0} markets".format(str(len(marketSummaries))))
    logging.info("Starting to persist market summaries data")
    for ms in marketSummaries:
        time.sleep(0.2)#to prevent throttling
        timestamp = utc_to_pst(convert_bittrex_timestamp_to_datetime(ms.timestamp))
        ms.timestamp = timestamp
        interval = calculateIntervalNumber(timestamp, 5)#we consider 5 minute interval for now, TODO: this should be configurable
        dateandinterval = timestamp.strftime("%Y-%m-%d") + "#" + str(interval)
        insertMarketSummary(ms, dateandinterval)

    logging.info("Completed persisting market summaries data")


if __name__ == "__main__":
    main(None, None)
