from binance import Client
from binance import BinanceSocketManager
import pandas as pd
import asyncio
import sys
import time

apiKey = 'fmJFIHzmHYcuU7DUfWmTq5Bxpuj50gkD3C3YChYAMIpJlLAos3w5rG7aRFIw8VHd'
apiSecret = 'kzfH3z36eP1iDAl5WymrEYsDIvwgCbsuXFVZo4WoIjqUvdL9Sas0Ya36VPhoSEd3'
binance = Client(apiKey, apiSecret, testnet=True)

bsm = BinanceSocketManager(binance)


def get_top_symbol():
    x = pd.DataFrame(binance.get_ticker())
    relev = x[x.symbol.str.contains('USDT')]
    nonLevarage = relev[~((relev.symbol.str.contains('UP'))
                          | (relev.symbol.str.contains('DOWN')))]
    topSymbol = nonLevarage[nonLevarage.priceChangePercent ==
                            nonLevarage.priceChangePercent.max()]
    topSymbol = topSymbol.symbol.values[0]
    return topSymbol
    # return 'BNBBUSD'


def get_minute_data(symbol, interval, lookback):
    frame = pd.DataFrame(binance.get_historical_klines(
        symbol, interval, lookback + ' min ago UTC'))
    frame = frame.iloc[:, :6]
    frame.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    frame = frame.set_index('Time')
    frame.index = pd.to_datetime(frame.index, unit='ms')
    frame = frame.astype(float)
    return frame


async def create_frame(msg):
    df = pd.DataFrame([msg])
    df = df.loc[:, ['s', 'E', 'p']]
    df.columns = ['symbol', 'Time', 'Price']
    df.Price = df.Price.astype(float)
    df.Time = pd.to_datetime(df.Time, unit='ms')
    return df


xy = get_minute_data(get_top_symbol(), '1m', '120')


def countdown(t, step=1, msg='sleeping'):  # in seconds
    pad_str = ' ' * len('%d' % step)
    for i in range(t, 0, -step):
        print('%s for the next %d seconds %s\r' % (msg, i, pad_str)),
        sys.stdout.flush()
        time.sleep(step)
    print('Done %s for %d seconds!  %s' % (msg, t, pad_str))


async def strategy(buy_amount, sl=0.985, Target=1.02, open_position=False):
    history = []
    try:
        asset = get_top_symbol()
        print('top symbol now : ' + asset)
    except:
        countdown(61)
        asset = get_top_symbol()
    socket = bsm.trade_socket(asset)
    df = get_minute_data(asset, '1m', '120')
    qty = round(buy_amount/df.Close.iloc[-1])
    if qty > 0:
        macd = ((df.Close.pct_change()+1).cumprod()).iloc[-1]
        print(f'macd value : {macd}')
        if macd > 1:
            order = binance.create_order(
                symbol=asset, side='BUY', type='MARKET', quantity=qty)
            print(order)
            buyprice = float(order['fills'][0]['price'])
            open_position = True
            while open_position:
                print('\n')
                await socket.__aenter__()
                msg = await socket.recv()
                print(msg)
                df = await create_frame(msg)

                print(f'current Close is ' + str(df['Price'].values[-1]))
                print(f'current Target is ' + str(buyprice*Target))
                print(f'current Stop is ' + str(buyprice*sl))
                if df.Price.values <= buyprice * sl or df.Price.values >= buyprice * Target:
                    order = binance.create_order(
                        symbol=asset, side='SELL', type='MARKET', quantity=qty)
                    history.append({'buyPrice': buyprice, 'sellPrice': float(
                        order['fills'][0]['price']), 'targetPrice': str(buyprice*Target), 'stopPrice': str(buyprice*sl)})
                    print(order)
                    print('\n================\n')
                    print(history)
                    break
        else:
            print('not yet to cross macd')
    else:
        print('your balance not enough to buy with your setting now')
        countdown(61)


async def main():
    while True:
        await strategy(500)

loop = asyncio.get_event_loop()
loop.create_task(main())
loop.run_forever()
