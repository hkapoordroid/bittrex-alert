from __future__ import print_function
import logging
import boto3
import json
from constants import *
import sys

logger = logging.getLogger()

dynamodb = boto3.resource('dynamodb')
bittrexAlertsSignalsTable = dynamodb.Table('bittrex-alerts-signals')


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
    insertSignal(market_name="BTC-SC", timestamp="2017-12-25T01:05:00", signal_type="BUY", price_trend="UP",
    price_diff=3.25, volume_trend="UP", volume_diff=59.90,
    last_interval_volume=4660629.62, intervals_open_price=0.0342,
    intervals_close_price=0.0339, green_candles_count=4,
    red_candles_count=2, interval_size="fiveMin", intervals_considered=6,
    price_change_threshold=3, volume_min_threshold=50,
    volume_change_threshold=50)
