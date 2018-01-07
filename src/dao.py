from __future__ import print_function
import logging
import boto3
import json
from constants import *
import sys
import datetime
import time
from decimal import *
from marketsummary import MarketSummary

logger = logging.getLogger()

dynamodb = boto3.resource('dynamodb')
bittrexAlertsSignalsTable = dynamodb.Table('bittrex-alerts-signals')
bittrexMedianVolumesTable = dynamodb.Table('bittrex-median-volumes')
bittrexMarketSummariesTable = dynamodb.Table('bittrex-market-summaries')

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


def getMarketSummary(market_name, date_interval):
    try:
        response = bittrexMarketSummariesTable.get_item(
            Key={
                'MarketName' : market_name,
                'DateAndInterval' : date_interval,
            }
        )

        if response and response['Item']:
            item = response['Item']

            name = item['MarketName']
            dateInterval = item['DateAndInterval']
            high = Decimal(item['High'])
            low = Decimal(item['Low'])
            volume = Decimal(item['Volume'])
            last = Decimal(item['Last'])
            baseVolume = Decimal(item['BaseVolume'])
            timestamp = item['timestamp']
            bid = Decimal(item['Bid'])
            ask = Decimal(item['Ask'])
            openBuyOrders = Decimal(item['OpenBuyOrders'])
            openSellOrders = Decimal(item['OpenSellOrders'])
            prevDay = Decimal(item['PrevDay'])
            marketCreatedDate = item['CreatedDate']

            return MarketSummary(name=name, high=high, low=low, volume=volume, last=last, base_volume=baseVolume,
            timestamp=timestamp, bid=bid, ask=ask, open_buy_orders=openBuyOrders, open_sell_orders=openSellOrders, prev_day=prevDay,
            created=marketCreatedDate)

        else:
            logging.error("Error while trying to get market summary for market {0} and date interval {1}\nError message: {2}".format(market_name,
            date_interval, sys.exc_info()))

            return None

    except:
        logging.error("Error while trying to get market summary for market {0} and date interval {1}\nError message: {2}".format(market_name,
        date_interval, sys.exc_info()))

    return None

def insertMarketSummary(market_summary,date_interval):
    try:
        #items are inserted with ttl of 25 hours

        itemToInsert = {
            "MarketName" : market_summary.name,
            "DateAndInterval" : date_interval,
            "High" : "%.15g" % float(market_summary.high),
            "Low" : "%.15g" % float(market_summary.low),
            "Volume" : "%.15g" % float(market_summary.volume),
            "Last" : "%.15g" % float(market_summary.last),
            "BaseVolume" : "%.15g" % float(market_summary.baseVolume),
            "timestamp" : market_summary.timestamp,
            "TTLTimestamp" : int(time.time()) + 90000,
            "Bid" : "%.15g" % float(market_summary.bid),
            "Ask" : "%.15g" % float(market_summary.ask),
            "OpenBuyOrders" : "%.15g" % float(market_summary.openBuyOrders),
            "OpenSellOrders" : "%.15g" % float(market_summary.openSellOrders),
            "PrevDay" : "%.15g" % float(market_summary.prevDay),
            "CreatedDate" : market_summary.created,
        }

        bittrexMarketSummariesTable.put_item(Item=itemToInsert)

        logging.info("Market Summary data persisted for market {0} and dateinterval {1}".format(market_summary.name, date_interval))
    except:
        logging.error("Error while trying to persist market summary for market {0}\n Error message: {1}".format(market_summary.name, sys.exc_info()))


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
