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


logger = logging.getLogger()


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
    logging.info("Get candles data for market {0} using url {1}".format(market_name, url))

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
