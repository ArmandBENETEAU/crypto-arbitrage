'''
Pricing Tier        Taker Fee       Maker Fee
Up to $10k          0.50%           0.50%
$10k - $50k         0.35%           0.35%
$50k - $100k        0.25%           0.15%
$100k - $1m         0.20%           0.10%
$1m - $20m          0.18%           0.08%
$20m - $100m        0.15%           0.05%
$100m - $300m       0.10%           0.02%
$300m - $500m       0.08%           0.00%
$500m - $750m       0.06%           0.00%
$750m - $1b         0.05%           0.00%
$1b+                0.04%           0.00%
'''

import asyncio
from datetime import datetime, timedelta
import calendar
from decimal import Decimal
from base import ExchangeException
from mod_imports import *
import time

class ExchangeEngine(ExchangeEngineBase):
    def __init__(self, filename):
        self.API_URL = 'https://api.exchange.coinbase.com'
        self.apiVersion = 'v1.0'
        self.feeRatio = Decimal(0.0050)
        self.sleepTime = 5

        self.load_key(filename)

        # Try to get the api_key, the passphrase and the secret key
        self.api_key = self.key.get("api_key", "")
        self.passphrase = self.key.get("passphrase", "")
        self.secret_key = self.key.get("api_secret", "")

        if self.api_key == "" or self.passphrase == "" or self.secret_key == "":
            raise ValueError("One of the key is missing for the Coinbase Pro exchange")

        # Create the authentication headers that are not moving
        self.fix_headers = {
            'Content-Type': 'Application/JSON',
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-PASSPHRASE': self.passphrase
        }

        # Creation of the client session to use
        self.client_session = None

    async def _send_request(self, command: str, httpMethod: str, params={}):
        # Create the client session if not existing
        if self.client_session is None:
            self.client_session = aiohttp.ClientSession(headers=self.fix_headers)

        # Create the command
        full_cmd = f"/{command}"
        # Put the HTTP method in uppercase
        upper_method = httpMethod.upper()

        # Get the timestamp
        timestamp = str(time.time())

        # Create the body to send in message
        if len(params) != 0:
            msg_body = json.dumps(params)
        else:
            msg_body = ''

        # Create the message
        message = ''.join([timestamp, upper_method,
                           full_cmd, msg_body])

        # Convert to bytes
        message_bytes = message.encode('ascii')
        hmac_key = base64.b64decode(self.secret_key)
        signature = hmac.new(hmac_key, message_bytes, hashlib.sha256)
        signature_b64 = base64.b64encode(signature.digest()).decode('utf-8')

        additional_headers = {
            'CB-ACCESS-SIGN': signature_b64,
            'CB-ACCESS-TIMESTAMP': timestamp
        }

        # Send the request
        response = await self.client_session.request(upper_method, f"{self.API_URL}{full_cmd}", data=params, headers=additional_headers)

        # Get the answer as dictionary
        async with response:
            content = await response.json()

        return content


    async def place_order(self, ticker, action, amount, price):
        pass
  
    async def get_balance(self, tickers: list=[]) -> dict:
        '''
        Return the balance of all the tickers given by the caller. A ticker is the unique
        way to call a crypto-currency, like BTC, ETH, XRP, etc.

        The result is a dictionnary, looking like the following:

        {
            'ETH': 0.005,
            'OMG': 0,
            'XRP': 1.5
        }
        '''
        # Create the resulting dict
        result = {}

        # Send the request allowing to get all accounts
        accounts_list = await self._send_request("accounts", "GET")

        # Check along the accounts to retrieve the ticker
        for account in accounts_list:
            if account["currency"] in tickers:
                # If it is part of the tickers wanted add it in the dict
                result[account["currency"]] = float(account["balance"])
                # Check if we have all our tickers
                if len(result) == len(tickers):
                    break

        # Raise an exception if we did not found all the tickers
        if len(result) != len(tickers):
            raise ExchangeException("One of the ticker balance has not been found!")
        else:
            return result
    
    async def get_ticker_history(self, ticker):
        pass

    async def end_engine(self):
        if self.client_session is not None:
            await self.client_session.close()

if __name__ == "__main__":
    engine = ExchangeEngine('keys/coinbasepro.key')

    async def main():
        # answer = await engine._send_request("accounts", "GET")
        answer = await engine.get_balance(tickers=["XLM", "EOS", "BTC"])
        answer_str = json.dumps(answer, indent=4)
        print(answer_str)
        await engine.end_engine()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())


