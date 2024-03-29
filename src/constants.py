#SLACK RELATED CONSTANTS
BULLISH_COLOR = "#07EC23"
BEARISH_COLOR = "#FD2E02"
MIX_COLOR = "#F9F903"
DEFAULT_COLOR = "#FFFFFF"
HEALTHCHECK_SLACK_WEBHOOK = "https://hooks.slack.com/services/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"
LEADS_SLACK_WEBHOOK = "https://hooks.slack.com/services/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"
BITTREX_ALERT_TITLE = "Bittrex Alert!"

#TELEGRAM RELATED CONTSTANTS
CRYPTO_VOLATILITY_LEADS_WEBHOOK = "https://api.telegram.org/bot518887153:AAGfkjT0Oaf1WOpfRCcIhmt9iu6NVVHnK_g/sendMessage"
CRYPTO_VOLATILITY_LEADS_CHAT_ID = -180779793
CRYPTO_MOVERS_LEADS_WEBHOOK = "https://api.telegram.org/bot518887153:AAGfkjT0Oaf1WOpfRCcIhmt9iu6NVVHnK_g/sendMessage"
CRYPTO_MOVERS_LEADS_CHAT_ID = -183942997

#ALERT RELATED CONSTANTS
BULLISH_TREND = "UP"
BEARISH_TREND = "DOWN"
MIX_TREND = "MIX"
SIGNAL_TYPE_BUY = "BUY"
SIGNAL_TYPE_SELL = "SELL"
SIGNAL_TYPE_NA = "NA"

#BITTREX RELATED CONSTANTS
BUY_ORDERBOOK = 'buy'
SELL_ORDERBOOK = 'sell'
BOTH_ORDERBOOK = 'both'
TICKINTERVAL_ONEMIN = 'oneMin'
TICKINTERVAL_FIVEMIN = 'fiveMin'
TICKINTERVAL_HOUR = 'hour'
TICKINTERVAL_THIRTYMIN = 'thirtyMin'
TICKINTERVAL_DAY = 'Day'
ORDERTYPE_LIMIT = 'LIMIT'
ORDERTYPE_MARKET = 'MARKET'
TIMEINEFFECT_GOOD_TIL_CANCELLED = 'GOOD_TIL_CANCELLED'
TIMEINEFFECT_IMMEDIATE_OR_CANCEL = 'IMMEDIATE_OR_CANCEL'
TIMEINEFFECT_FILL_OR_KILL = 'FILL_OR_KILL'
CONDITIONTYPE_NONE = 'NONE'
CONDITIONTYPE_GREATER_THAN = 'GREATER_THAN'
CONDITIONTYPE_LESS_THAN = 'LESS_THAN'
CONDITIONTYPE_STOP_LOSS_FIXED = 'STOP_LOSS_FIXED'
CONDITIONTYPE_STOP_LOSS_PERCENTAGE = 'STOP_LOSS_PERCENTAGE'
BITTREX_GET_MARKETS_SUMMARIES_URL = "https://bittrex.com/api/v1.1/public/getmarketsummaries"
BITTREX_GET_MARKETS_URL = "https://bittrex.com/api/v1.1/public/getmarkets"
BITTREX_GET_TICKS_URL = "https://bittrex.com/Api/v2.0/pub/market/GetTicks?marketName={0}&tickInterval={1}&_={2}"
BITTREX_GET_BTC_PRICE_URL = "https://bittrex.com/api/v2.0/pub/currencies/GetBTCPrice"
BITTREX_GET_ETH_PRICE_URL = "https://bittrex.com/Api/v2.0/pub/market/GetLatestTick?marketName=BTC-ETH&tickInterval=oneMin&_={0}"

#ALERT DEFAULT CONFIGURATIONS CONSTANTS
DEFAULT_ALERT_PRICE_CHANGE_THRESHOLD = 2
DEFAULT_ALERT_VOLUME_CHANGE_THRESHOLD = 50
DEFAULT_ALERT_VOLUME_MIN_THRESHOLD = 50
INTERVALS_TO_CONSIDER = 3

#COINS TO WATCH CONFIGURATIONS CONSTANTS
#removed on 12/30/2017
#"BTC-ETC", "BTC-BTG", "BTC-WAVES", "BTC-STRAT", "BTC-ARDR", "BTC-MONA", "BTC-DOGE", "BTC-SNT", "BTC-DCR", "BTC-EMC2", "BTC-KMD", "BTC-PIVX",
# "BTC-PAY", "BTC-VTC", "BTC-GBYTE",
# "ETH-BTG", "ETH-ETC", "ETH-WAVES", "ETH-STRAT", "ETH-MCO", "ETH-SNT", "ETH-PAY",

CRYPTO_VOLATILITY_MARKETS_TO_WATCH_BASE_VOLUME_MIN = 750
CRYPTO_MOVERS_MARKETS_TO_WATCH_BASE_VOLUME_MIN = 250

MARKETS_TO_WATCH = ["BTC-LTC", "BTC-ETH", "BTC-BCC", "BTC-XRP", "BTC-ADA", "BTC-DASH", "BTC-XMR", "BTC-XLM",
"BTC-NEO", "BTC-NEOS", "BTC-QTUM", "BTC-LSK", "BTC-OMG", "BTC-ZEC", "BTC-NXT",
"BTC-XVG", "BTC-STEEM", "BTC-ARK", "BTC-SALT", "BTC-REP", "BTC-SC", "BTC-GNT", "BTC-DGB",
"ETH-LTC", "ETH-BCC", "ETH-XRP", "ETH-ADA", "ETH-DASH", "ETH-XMR", "ETH-XLM","ETH-NEO", "ETH-QTUM", "ETH-OMG",
"ETH-ZEC", "ETH-SALT", "ETH-REP", "ETH-SC", "ETH-GNT", "ETH-DGB", "BTC-ENG", "ETH-ENG"]

#MARKETS_TO_WATCH = ["BTC-SC"]
