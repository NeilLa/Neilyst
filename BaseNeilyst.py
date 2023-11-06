import configparser
import ccxt

class BaseNeilyst():
    def __init__(self, exchange_name):
        config = configparser.ConfigParser()
        config.read('config.ini')

        proxy = config.get('DEFAULT', 'proxy', fallback=None)
        timeout = config.getint('DEFAULT', 'timeout', fallback=10000)

        self.exchange_name = exchange_name
        self.exchange = getattr(ccxt, self.exchange_name)()
        self.exchange.httpsProxy = proxy
        self.exchange.timeout = timeout

        self.ohlcv_data = None
        self.indicators = None

        self.fee_rate = config.getfloat('DEFAULT', 'fee', fallback=0.00015)
        self.slippage_rate = config.getfloat("DEFAULT", 'slippage', fallback=0.00005)