from __future__ import print_function
import logging
import sys
from utils import *
from constants import *

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def calculatePercentageDiff(start_val, end_val):
    '''
        Given 2 values it find the percentage increase or decrease between values_1 and value_2
    '''
    valDiff = abs(start_val - end_val)
    valPercDiff = valDiff/start_val if start_val < end_val else (valDiff/end_val)*-1

    return valPercDiff*100

class candle(object):
    '''
        This class is used to store candle data
    '''

    def __init__(self, high, low, open, close, volume, interval, timestamp):
        self.high = high
        self.low = low
        self.open = open
        self.close = close
        self.volume = volume
        self.interval = interval
        self.timestamp = timestamp

    def __str__(self):
        return 'Candle Data : High {0}, Low {1}, Open {2}, Close {3}, Vol {4}, Interval {5}, Timestamp {6}'.format(self.high, self.low,
        self.open, self.close, self.volume, self.interval, self.timestamp)

class candlesInsights(object):
    '''
        This class is used to hold list of candles and perform various analysis on them
    '''

    def __init__(self, candles):
        self.candles = candles


    def getMedianVolume(self, candlesToConsider=None):
        '''
            This method identifies the median volume of the candles
        '''

        if not candlesToConsider:
            candlesToConsider = len(self.candles)

        candlesTmp = self.candles[-candlesToConsider:-1]

        #first get the list of the volume for all candles
        volumeDataRaw = [x.volume for x in candlesTmp]

        medianVolume = median(volumeDataRaw)

        return medianVolume



    def getVolumeTrend(self):
        '''
            This method identifies the volume pattern of the candles
            return tuple of the format (volumeDiff, volumeTrend, firstIntervalVolume, lastIntervalVolume)
        '''
        if not self.candles:
            raise Exception("No candles available to analyze volume trend")

        firstIntervalVolume = self.candles[0].volume
        lastIntervalVolume = self.candles[-1].volume

        volumeDiff = calculatePercentageDiff(firstIntervalVolume, lastIntervalVolume)

        volumeTrend = BULLISH_TREND if volumeDiff > 0 else BEARISH_TREND

        logging.debug("volumeDiff {0}] volumeTrend {1} firstIntervalVolume {2} lastIntervalVolume {3}".format(volumeDiff, volumeTrend,
        firstIntervalVolume, lastIntervalVolume))

        return (volumeDiff, volumeTrend, firstIntervalVolume, lastIntervalVolume)


    def getPriceTrend(self):
        '''
            This method identifies the price pattern of the candles
            Returns tuple of the format (priceDiff, greenCandlesCount, redCandlesCount, priceTrend, intervalsOpenPrice, intervalsClosePrice,
            lastIntervalTimestamp)
        '''
        if not self.candles:
            raise Exception("No candles available to analyze price trend")

        intervalStartPrice = self.candles[0].open
        intervalEndPrice = self.candles[-1].close
        lowestClosePrice = intervalStartPrice
        highestClosePrice = intervalStartPrice
        greenCandlesCount = 0
        redCandlesCount = 0
        for c in self.candles:
            if c.close > c.open:
                greenCandlesCount += 1
            else:
                redCandlesCount += 1

            if c.close < lowestClosePrice:
                lowestClosePrice = c.close

            if c.close > highestClosePrice:
                highestClosePrice = c.close

        #calculate overall price difference between all intervals
        priceDiff = calculatePercentageDiff(intervalStartPrice, intervalEndPrice)

        #percentage of green candles vs red candles
        #totalCandles = len(self.candles)
        #greenCandlesPercentage = (greenCandles/totalCandles)*100
        #redCandlesPercentage = (redCandles/totalCandles)*100

        priceTrend = None
        if intervalEndPrice > intervalStartPrice and greenCandlesCount >= redCandlesCount:
            priceTrend = BULLISH_TREND
        elif intervalEndPrice < intervalStartPrice and redCandlesCount >= greenCandlesCount:
            priceTrend = BEARISH_TREND
        else:
            priceTrend = MIX_TREND

        logging.debug("priceDiff {0} greenCandlesCount {1} redCandlesCount {2} priceTrend {3} intervalsOpenPrice {4} intervalsClosePrice {5} \
        lastIntervalTimestamp {6}".format(priceDiff,
        greenCandlesCount, redCandlesCount, priceTrend, intervalStartPrice, intervalEndPrice, self.candles[-1].timestamp))

        return (priceDiff, greenCandlesCount, redCandlesCount, priceTrend, intervalStartPrice, intervalEndPrice, self.candles[-1].timestamp)
