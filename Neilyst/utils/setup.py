import ccxt

def init_ccxt_exchange(exchange_name, proxy):
    ccxt_exchange = getattr(ccxt, exchange_name)()

    if proxy:
        ccxt_exchange.httpsProxy = proxy
        
    return ccxt_exchange
