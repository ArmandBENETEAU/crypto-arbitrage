import time
from time import strftime
import asyncio
import os 
import sys
from engines.exchanges.loader import EngineLoader

class CryptoEngineTriArbitrage(object):
    def __init__(self, exchange, mock=False):
        self.exchange = exchange
        self.mock = mock
        self.minProfitUSDT = 0.3
        self.hasOpenOrder = True # always assume there are open orders first
        self.openOrderCheckCount = 0
      
        self.engine = EngineLoader.getEngine(self.exchange['exchange'], self.exchange['keyFile'])

    async def start_engine(self):
        print(strftime('%Y%m%d%H%M%S') + ' starting Triangular Arbitrage Engine...')
        if self.mock:
            print('---------------------------- MOCK MODE ----------------------------')
        #Send the request asynchronously
        while True:
            try:
                if not self.mock and self.hasOpenOrder:
                    await self.check_openOrder()
                elif (await self.check_balance()):           
                    bookStatus = await self.check_orderBook()
                    if bookStatus['status']:
                        await self.place_order(bookStatus['orderInfo'])
            except Exception as e:
               # raise
               print(e)
            
            await asyncio.sleep(self.engine.sleepTime)
    
    async def check_openOrder(self):
        if self.openOrderCheckCount >= 5:
            await self.cancel_allOrders()
        else:
            print('checking open orders...')
            responses = await asyncio.gather(self.engine.get_open_order())

            if not responses[0]:
                print(responses)
                return False
            
            if responses[0]:
                self.engine.openOrders = responses[0]
                print(self.engine.openOrders)
                self.openOrderCheckCount += 1
            else:
                self.hasOpenOrder = False
                print('no open orders')
                print('starting to check order book...')
    
    async def cancel_allOrders(self):
        print('cancelling all open orders...')
        coros = []
        print(self.exchange['exchange'])
        for order in self.engine.openOrders:
            print(order)
            coros.append(self.engine.cancel_order(order['orderId']))

        responses = await asyncio.gather(*coros)
        
        self.engine.openOrders = []
        self.hasOpenOrder = False
        

    #Check and set current balance
    async def check_balance(self):
        responses = await asyncio.gather(self.engine.get_balance([
            self.exchange['tickerA'],
            self.exchange['tickerB'],
            self.exchange['tickerC']
            ]))

        self.engine.balance = responses[0]

        ''' Not needed? '''
        # if not self.mock:
        #     for res in responses:
        #         for ticker in res.parsed:
        #             if res.parsed[ticker] < 0.05:
        #                 print(ticker, res.parsed[ticker], '- Not Enough'
        #                 return False
        return True
    
    async def check_orderBook(self):
        responses = await asyncio.gather(
            self.engine.get_ticker_lastPrice(self.exchange['tickerA']),
            self.engine.get_ticker_lastPrice(self.exchange['tickerB']),
            self.engine.get_ticker_lastPrice(self.exchange['tickerC']))

        lastPrices = []
        for res in responses:
            price_value = list(res.values())
            lastPrices.append(price_value[0])

        responses = await asyncio.gather(
            self.engine.get_ticker_orderBook_innermost(self.exchange['tickerPairA']),
            self.engine.get_ticker_orderBook_innermost(self.exchange['tickerPairB']),
            self.engine.get_ticker_orderBook_innermost(self.exchange['tickerPairC']))
        
        if self.mock:
            print("\n--- Current order books ---")
            print('{0} - {1};'.format(self.exchange['tickerPairA'], responses[0]))
            print('{0} - {1};'.format(self.exchange['tickerPairB'], responses[1]))
            print('{0} - {1};'.format(self.exchange['tickerPairC'], responses[2]))
        
        # bid route BTC->ETH->LTC->BTC
        bidRoute_result = (1 / responses[0]['ask']['price']) \
                            / responses[1]['ask']['price']   \
                            * responses[2]['bid']['price']  
        # ask route ETH->BTC->LTC->ETH
        askRoute_result = (1 * responses[0]['bid']['price']) \
                            / responses[2]['ask']['price']   \
                            * responses[1]['bid']['price']
        
        # Max amount for bid route & ask routes can be different and so less profit
        if bidRoute_result > 1 or \
        (bidRoute_result > 1 and askRoute_result > 1 and (bidRoute_result - 1) * lastPrices[0] > (askRoute_result - 1) * lastPrices[1]):
            status = 1 # bid route
        elif askRoute_result > 1:
            status = 2 # ask route
        else:
            status = 0 # do nothing
        
        if status > 0:
            maxAmounts = self.getMaxAmount(lastPrices, responses, status)
            fee = 0
            for index, amount in enumerate(maxAmounts):
                fee += amount * lastPrices[index]
            fee *= self.engine.feeRatio
            
            bidRoute_profit = (bidRoute_result - 1) * lastPrices[0] * maxAmounts[0]
            askRoute_profit = (askRoute_result - 1) * lastPrices[1] * maxAmounts[1]
            # print('bidRoute_profit - {0} askRoute_profit - {1} fee - {2}'.format(
            #     bidRoute_profit, askRoute_profit, fee
            # )
            if status == 1 and bidRoute_profit - fee > self.minProfitUSDT:
                print("\nOpportunity found!")
                print(strftime('%Y%m%d%H%M%S') + ' Bid Route: Result - {0} Profit - {1} Fee - {2}'.format(bidRoute_result, bidRoute_profit, fee))
                orderInfo = [
                    {
                        "tickerPair": self.exchange['tickerPairA'],
                        "action": "bid",
                        "price": responses[0]['ask']['price'],
                        "amount": maxAmounts[0]
                    },
                    {
                        "tickerPair": self.exchange['tickerPairB'],
                        "action": "bid",
                        "price": responses[1]['ask']['price'],
                        "amount": maxAmounts[1]
                    },
                    {
                        "tickerPair": self.exchange['tickerPairC'],
                        "action": "ask",
                        "price": responses[2]['bid']['price'],
                        "amount": maxAmounts[2]
                    }                                        
                ]
                return {'status': 1, "orderInfo": orderInfo}
            elif status == 2 and askRoute_profit - fee > self.minProfitUSDT:
                print("\nOpportunity found!")
                print(strftime('%Y%m%d%H%M%S') + ' Ask Route: Result - {0} Profit - {1} Fee - {2}'.format(askRoute_result, askRoute_profit, fee))
                orderInfo = [
                    {
                        "tickerPair": self.exchange['tickerPairA'],
                        "action": "ask",
                        "price": responses[0]['bid']['price'],
                        "amount": maxAmounts[0]
                    },
                    {
                        "tickerPair": self.exchange['tickerPairB'],
                        "action": "ask",
                        "price": responses[1]['bid']['price'],
                        "amount": maxAmounts[1]
                    },
                    {
                        "tickerPair": self.exchange['tickerPairC'],
                        "action": "bid",
                        "price": responses[2]['ask']['price'],
                        "amount": maxAmounts[2]
                    }                                        
                ]               
                return {'status': 2, 'orderInfo': orderInfo}
        return {'status': 0}

    # Using USDT may not be accurate
    def getMaxAmount(self, lastPrices, orderBookRes, status):
        maxUSDT = []
        for index, tickerIndex in enumerate(['tickerA', 'tickerB', 'tickerC']):
            # 1: 'bid', -1: 'ask'
            if index == 0: bid_ask = -1
            elif index == 1: bid_ask = -1
            else: bid_ask = 1
            # switch for ask route
            if status == 2: bid_ask *= -1
            bid_ask = 'bid' if bid_ask == 1 else 'ask'
            
            maxBalance = min(orderBookRes[index][bid_ask]['amount'], self.engine.balance[self.exchange[tickerIndex]])
            # print('{0} orderBookAmount - {1} ownAmount - {2}'.format(
            #     self.exchange[tickerIndex], 
            #     orderBookRes[index].parsed[bid_ask]['amount'], 
            #     self.engine.balance[self.exchange[tickerIndex]]
            # )
            USDT = maxBalance * lastPrices[index] * (1 - self.engine.feeRatio)
            if not maxUSDT or USDT < maxUSDT: 
                maxUSDT = USDT       

        maxAmounts = []
        for index, tickerIndex in enumerate(['tickerA', 'tickerB', 'tickerC']):
            # May need to handle scientific notation
            maxAmounts.append(maxUSDT / lastPrices[index])

        return maxAmounts

    async def place_order(self, orderInfo):
        print(orderInfo)
        coros = []
        for order in orderInfo:
            coros.append(self.engine.place_order(
                order['tickerPair'],
                order['action'],
                order['amount'],
                order['price']))

        if not self.mock:
            responses = await asyncio.gather(*coros)

        self.hasOpenOrder = True
        self.openOrderCheckCount = 0

    async def run(self):
        await self.start_engine()

if __name__ == '__main__':

    async def main():

        # exchange = {
        # 'exchange': 'bittrex',
        # 'keyFile': '../keys/bittrex.key',
        # 'tickerPairA': 'BTC-ETH',
        # 'tickerPairB': 'ETH-LTC',
        # 'tickerPairC': 'BTC-LTC',
        # 'tickerA': 'BTC',
        # 'tickerB': 'ETH',
        # 'tickerC': 'LTC'
        # }  
        # try:
        exchange = {
            'exchange': 'coinbase_pro',
            'keyFile': 'keys/coinbasepro.key',
            'tickerPairA': 'ADA-ETH',
            'tickerPairB': 'ETH-BTC',
            'tickerPairC': 'ADA-BTC',
            'tickerA': 'ADA',
            'tickerB': 'ETH',
            'tickerC': 'BTC'
        }    
        engine = CryptoEngineTriArbitrage(exchange, True)
        await engine.run()

        # except Exception as err:
        #     print("Something bad happened:")
        #     print(str(err))

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
