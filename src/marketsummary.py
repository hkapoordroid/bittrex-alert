from __future__ import print_function
import logging
import sys
from utils import *
from constants import *

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class MarketSummary(object):
    def __init__(self, name, high, low, volume, last, base_volume, timestamp, bid, ask, open_buy_orders, open_sell_orders, prev_day, created):
        self.name = name
        self.high = high
        self.low = low
        self.volume = volume
        self.last = last
        self.baseVolume = base_volume
        self.timestamp = timestamp
        self.bid = bid
        self.ask = ask
        self.openBuyOrders = open_buy_orders
        self.openSellOrders = open_sell_orders
        self.prevDay = prev_day
        self.created = created

    def __str__(self):
        return  'Market Summary : name {0} high {1} low {2} volume {3} last {4} base volume {5} timestamp {6} bid {7} ask {8} open buy orders {9} \
open sell orders {10} prev day {11} created {12}'.format(self.name, self.high, self.low, self.volume, self.last, self.baseVolume, self.timestamp,
self.bid, self.ask, self.openBuyOrders, self.openSellOrders, self.prevDay, self.created)
