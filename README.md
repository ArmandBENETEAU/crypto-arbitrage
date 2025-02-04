# Crypto Arbitrage
## Introduction
This is an automatic trading bot using Triangular or Exchange Arbitrages. It reguarly checks and detects arbitrage opportunities, and place orders when a profit can be made. This works on any cryptocurrency pairs with minor configuration.  
Started with $1000 in October 2017, there were some times that this made about $40/day for a few weeks with Triangular Arbitrage on Bittrex, but as the market is getting very unstable, the profit is hard to outrun the high price fluctuation.

## Exchanges
Bittrex, Bitfinex, Bitstamp, Kraken, Gatecoin (Not maintained anymore due to its extremely low volume)

## Setup
1. Install Python 2 at here https://www.python.org/downloads/ if necessary. **This bot will not work with Python 3.**
2. `pip install grequests`
3. Rename or copy `.key_sample` files under `keys` to `.key` file, and add the APIs. E.g. Create a file `bittrex.key`. **Make sure not to push any API keys or this `.key` file.**
4. Modify `arbitrage_config.json` for any other ticker pairs or exchanges

## Usage
Triangular: `python main.py -m triangular`  
Exchange:   `python main.py -m exchange`  
Mock mode is enabled by default, which does not place any order and just check and show any arbitrage opportunities. To turn off mock mode and run in production, add the argument `-p`.

## Difficulties
1. The trading fee is the largest obstacle. Most of the exchanges have a 0.25% fee. The profit will be larger if the fee can be lower.
2. Sometimes not all the placed orders are executed, so there will be some manual work to rebalance. The bot should be able to deal with this situation, such as placing a market order, instead of just cancelling the open orders.

## Further Improvement: TODO
1. Refactoring to python3
2. Use proper async code with python3 (aiohttp)
3. Use Decimal class instead of float for calculations
4. Implement "Coinbase Pro" exchange since it is the one I'm using
5. Handle open orders strategically?
6. Implement exchange rebalancing?
