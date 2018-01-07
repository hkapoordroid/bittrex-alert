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
from marketsummary import MarketSummary
import time
import sys
from dao import *
from constants import *
import string


logger = logging.getLogger()

def getMarketSummaries():
    '''
        this method gets all market summaries data and returns it as list of marketsummary objects
    '''

    resp = call_api(BITTREX_GET_MARKETS_SUMMARIES_URL)

    if not resp:
        raise Exception("Could not retrieve market summaries from bittrex")

    marketSummariesData = resp['result']

    marketSummariesList = set()
    for ms in marketSummariesData:
        msObj = MarketSummary(name=ms['MarketName'], high=ms['High'], low=ms['Low'], volume=ms['Volume'], last=ms['Last'],
        base_volume=ms['BaseVolume'], timestamp=ms['TimeStamp'], bid=ms['Bid'], ask=ms['Ask'], open_buy_orders=ms['OpenBuyOrders'],
        open_sell_orders=ms['OpenSellOrders'], prev_day=ms['PrevDay'], created=ms['Created'])
        marketSummariesList.add(msObj)

    return marketSummariesList

def getMarketNames():
    '''
        this method gets all market names from bittrex and returns list of strings
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

    btcPrice = string.replace(resultData['bpi']['USD']['rate'], ',', '')

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
