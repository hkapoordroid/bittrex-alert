from __future__ import print_function
import logging
import boto3
import json
from constants import *
import sys
import datetime
import time
from decimal import *

logger = logging.getLogger()

dynamodb = boto3.resource('dynamodb')
bittrexAlertsSignalsTable = dynamodb.Table('bittrex-alerts-signals')
bittrexMedianVolumesTable = dynamodb.Table('bittrex-median-volumes')

class medianVolume(object):

    def __init__(self, FifteenMinMedianVolume, OneHourMedianVolume, ThreeHourMedianVolume, OneDayMedianVolume, LastUpdatedTimeStamp):
        self.FifteenMinMedianVolume = FifteenMinMedianVolume
        self.OneHourMedianVolume = OneHourMedianVolume
        self.ThreeHourMedianVolume = ThreeHourMedianVolume
        self.OneDayMedianVolume = OneDayMedianVolume
        self.LastUpdatedTimeStamp = LastUpdatedTimeStamp

    def __str__(self):
        return "FifteenMinMedianVolume {0}\nOneHourMedianVolume {1}\nThreeHourMedianVolume {2}\n\
        OneDayMedianVolume {3}\nLastUpdatedTimeStamp {4}".format(
        str(self.FifteenMinMedianVolume), str(self.OneHourMedianVolume), str(self.ThreeHourMedianVolume), 
        str(self.OneDayMedianVolume), self.LastUpdatedTimeStamp)

def getMedianVolume(market_name):
    try:
        response = bittrexMedianVolumesTable.get_item(
            Key={
                'MarketName' : market_name,
            }
        )

        item = response['Item']

        FifteenMinMedianVolume = Decimal(item['FifteenMinMedianVolume'])
        OneHourMedianVolume = Decimal(item['OneHourMedianVolume'])
        ThreeHourMedianVolume = Decimal(item['ThreeHourMedianVolume'])
        OneDayMedianVolume = Decimal(item['OneDayMedianVolume'])
        LastUpdatedTimeStamp = item['LastUpdatedTimeStamp']

        medianVolumeObj = medianVolume(FifteenMinMedianVolume, OneHourMedianVolume, ThreeHourMedianVolume, OneDayMedianVolume, LastUpdatedTimeStamp)

        return medianVolumeObj

    except:
        logging.error("Error while trying to get median volume for market {0}\nError message: {1}".format(market_name, sys.exc_info()))


def insertMedianVolume(market_name, fifteen_min_median_volume, one_hour_median_volume, three_hour_median_volume, one_day_median_volume):
    try:
        ts = time.time()

        itemToInsert = {
            "MarketName" : market_name,
            "FifteenMinMedianVolume" : "%.15g" % fifteen_min_median_volume,
            "OneHourMedianVolume" : "%.15g" % one_hour_median_volume,
            "ThreeHourMedianVolume" : "%.15g" % three_hour_median_volume,
            "OneDayMedianVolume" : "%.15g" % one_day_median_volume,
            "LastUpdatedTimeStamp" : datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        }

        bittrexMedianVolumesTable.put_item(Item=itemToInsert)

        logging.info("Volume Data persisted for market {0}\n".format(market_name))
    except:
        logging.error("Error while trying to persist median volume for market {0}\nError message: {1}".format(market_name, sys.exc_info()))


def insertSignal(market_name, timestamp, signal_type, price_trend, price_diff, volume_trend, volume_diff, last_interval_volume, intervals_open_price,
intervals_close_price, green_candles_count, red_candles_count, interval_size, intervals_considered, price_change_threshold, volume_min_threshold,
volume_change_threshold):
    try:
        itemToInsert = {
            "marketName" : market_name,
            "timestamp" : timestamp,
            "signalType" : signal_type,
            "priceTrend" : price_trend,
            "priceDiff" : "%.15g" % price_diff,
            "volumeTrend" : volume_trend,
            "volumeDiff" : "%.15g" % volume_diff,
            "lastIntervalVolume" : "%.15g" % last_interval_volume,
            "intervalsOpenPrice" : "%.15g" % intervals_open_price,
            "intervalsClosePrice" : "%.15g" % intervals_close_price,
            "greenCandlesCount" : green_candles_count,
            "redCandlesCount" : red_candles_count,
            "intervalSize" : interval_size,
            "intervalsConsidered" : intervals_considered,
            "priceChangeThreshold" : price_change_threshold,
            "volumeMinThreshold" : volume_min_threshold,
            "volumeChangeThreshold" : volume_change_threshold,
        }

        bittrexAlertsSignalsTable.put_item(Item=itemToInsert)

        logging.info("{0} Signal Persisted for market {1}".format(signal_type, market_name))

    except:
        logging.error("Error while trying to persist the signal \nError message: {0}".format(sys.exc_info()))

if __name__ == "__main__":
    print(getMedianVolume('BTC-SC'))
    '''
    insertSignal(market_name="BTC-SC", timestamp="2017-12-25T01:05:00", signal_type="BUY", price_trend="UP",
    price_diff=3.25, volume_trend="UP", volume_diff=59.90,
    last_interval_volume=4660629.62, intervals_open_price=0.0342,
    intervals_close_price=0.0339, green_candles_count=4,
    red_candles_count=2, interval_size="fiveMin", intervals_considered=6,
    price_change_threshold=3, volume_min_threshold=50,
    volume_change_threshold=50)
    '''
