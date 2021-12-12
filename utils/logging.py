"""
File containing the logging object
.. moduleauthor:: Armand BENETEAU <armand.beneteau@iot.bzh>
*Date: 12/12/2021*
"""
import logging
import logging.handlers

# --------------------------------------------
# Logging configuration ----------------------
# --------------------------------------------
logging.basicConfig(format='%(asctime)s => [%(levelname)s] %(message)s', level=logging.INFO)
crypto_arb_log = logging.getLogger('crypto-arbitrage')