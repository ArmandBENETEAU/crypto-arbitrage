import argparse
import asyncio
import json

from utils.logging import crypto_arb_log

configFile = 'arbitrage_config.json'

with open(configFile) as cfg_file: 
    config = json.load(cfg_file)

parser = argparse.ArgumentParser(description='Crypto Arbitrage')
parser.add_argument('-m', '--mode', help='Arbitrage mode: triangular or exchange', required=True)
parser.add_argument('-p', '--production', help='Production mode', action='store_true')
args = parser.parse_args()

engine = None
isMockMode = True if not args.production else False

if args.mode == 'triangular':
    from engines.triangular_arbitrage import CryptoEngineTriArbitrage
    engine = CryptoEngineTriArbitrage(config['triangular'], isMockMode)
elif args.mode == 'exchange':
    # from engines.exchange_arbitrage import CryptoEngineExArbitrage
    # engine = CryptoEngineExArbitrage(config['exchange'], isMockMode)
    pass
else:
    crypto_arb_log.error(f"Mode {args.mode} is not recognized")

async def main():
    await engine.run()

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
