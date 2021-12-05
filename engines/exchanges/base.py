from abc import ABC, abstractmethod
import asyncio
import json

class ExchangeException(BaseException):
    pass

class ExchangeEngineBase(ABC):
    @abstractmethod
    def __init__(self, filename):
        pass
    
    def load_key(self, filename):
        with open(filename) as f:    
            self.key = json.load(f)
            
    @abstractmethod
    async def _send_request(self):
        pass
    
    @abstractmethod
    async def place_order(self, ticker, action, amount, price):
        pass
  
    @abstractmethod
    async def get_balance(self):
        pass
    
    
    @abstractmethod
    async def get_ticker_history(self, ticker):
        pass
       
    '''
    Format: e.g. {'exchange': 'gatecoin', 'ticker': 'BTCHKD', 'data': [{price: (int)30.5}]}
    '''
    #@abstractmethod
    def parseTickerData(self, tickerData):
        pass