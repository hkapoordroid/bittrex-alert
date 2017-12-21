from __future__ import print_function
from bittrex.bittrex import *
import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
my_bittrex = Bittrex(None, None, api_version=API_V2_0)

client = boto3.client('sns')

def calculatePercentageDiff(value_1, value_2):
    valDiff = abs(value_1 - value_2)
    valPercDiff = valDiff/value_1 if value_1 < value_2 else (valDiff/value_2)*-1

    return valPercDiff*100

def alertDiffInPrice(marketName='BTC-LTC', interval=TICKINTERVAL_THIRTYMIN):
    #get the ticket for the given markets
    logging.info('getting candles from bittrex for market {0}'.format(marketName))
    result = my_bittrex.get_candles(marketName, interval)
    #print(json.dumps(result, indent=4, separators=(',', ': ')))

    if not result:
        raise Exception("Could not retrieve data from bittrex api for market {0}".format(marketName))

    if result:
        candles = result['result']

        if not candles:
            raise Exception("Could not retrieve candles for market {0}\nresponse dump : {1}".format(marketName, result))

        if candles:
            candlesLen = len(candles)

            #print(candlesLen)

            if candlesLen > 1:
                startCandle = candles[candlesLen-2]
                endCandle = candles[candlesLen-1]

                logging.info("Start Candle : {0}\n End Candle : {1}".format(startCandle, endCandle))

                startVolume = startCandle['V']
                startTime = startCandle['T']

                endVolume = endCandle['V']
                endTime = endCandle['T']
                endOpenPrice = endCandle['O']
                endClosePrice = endCandle['C']

                volPercDiff = calculatePercentageDiff(startVolume, endVolume)
                pricePercDiff = calculatePercentageDiff(endOpenPrice, endClosePrice)
                priceTrend = ''
                endCandleHigh = endCandle['H']
                endCandleLow = endCandle['L']

                if startCandle['C'] > startCandle['O'] and endCandle['C'] > endCandle['O']:
                    priceTrend = 'UP'
                elif startCandle['C'] < startCandle['O'] and endCandle['C'] < endCandle['O']:
                    priceTrend = 'Down'
                else:
                    priceTrend = 'Mix'

                #TODO: logic to decide what is considered alert goes here. Example: If the volume has increase by certain percentage

                #Prepare the message
                snsMsg = "Market Name : {0}\n \
Price Trend : {1}\n \
Price % Change : {2}\n \
Volume % Change : {3}\n \
TimeStamp : {4}".format(marketName, priceTrend,
                          str(pricePercDiff), str(volPercDiff), str(endCandle['T']))

                return snsMsg

def getMarketNames():
    resp = my_bittrex.get_markets()

    print(resp['result'])
    '''
    if resp:
        marketNames = [x['MarketName'] for x in resp['result']]

        return marketNames
    '''
    return None


def main(event, context):
    #change here to include or remove a market
    #marketsToWatch = ["USDT-BTC", "BTC-LTC" "BTC-ADA", "USDT-XRP", "BTC-SC", "BTC-XLM", "BTC-OMG", "BTC-XVG"]
    marketsToWatch = ["USDT-BTC"]

    snsMsg = ''

    for market in marketsToWatch:
        logger.info('Checking for market name : ' + market)
        val = alertDiffInPrice(market, TICKINTERVAL_HOUR)
        #logger.info('Results : ' + str(val))
        if val:
            snsMsg = snsMsg + '\n' + val
        logger.info('Completed Checking for market name : ' + market)

    logger.info('Successfully published following msg to SNS : {0}'.format(snsMsg))

    '''
    client.publish(TopicArn='arn:aws:sns:us-east-1:787766881935:bittrex-alerts',
    Message=snsMsg,
    Subject='Crypto Alert!!!!',
    MessageStructure='string')
    '''

    return snsMsg


if __name__ == '__main__':
    #main(None, None)
    print(getMarketNames())
