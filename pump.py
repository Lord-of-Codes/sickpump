#!/usr/bin/env python

"""
Disclaimer: This does not guarantee profit and you can still lose money if your
sell order does not fill. (A sell order set too high may not be filled)

This program is for educational purposes only and is provided AS IS. Check the LICENSE file of 
this repository.
"""

import json
import signal
import sys
import time
from cryptopia_api import Api

# Get these from (link here)
def get_secret(secret_file):
    """Grabs API key and secret from file and returns them"""

    with open(secret_file) as secrets:
        secrets_json = json.load(secrets)
        secrets.close()

    return str(secrets_json['key']), str(secrets_json['secret'])

def sigint_handler():
    """Handler for ctrl+c"""
    print '\n[!] CTRL+C pressed. Exiting...'
    sys.exit(0)

EXIT_CYCLE = False
while not EXIT_CYCLE:

    # setup api
    KEY, SECRET = get_secret("secrets.json")
    API = Api(KEY, SECRET)

    # do before entering coin to save the API call during the pump
    BALANCE_BTC, ERROR = API.get_balance('BTC')
    if ERROR is not None:
        print ERROR
        break
    AVAILABLE_BTC = BALANCE_BTC['Available']

    # Set to True to enable limit trading...
    ALLOW_ORDERS = False


    signal.signal(signal.SIGINT, sigint_handler)
    print '\nWelcome to sickpump '
    print '\nBuy and Sell orders will be instantly placed on Cryptopia at a specified % above the ASK price.\n'

    TRAINING = raw_input("Live Mode (1) = Real orders will be placed.\nTraining Mode (2) = No real orders will be placed.\n\nEnter 1 for Live Mode or 2 for Training Mode - (1 or 2) ?: ")
    if TRAINING == "2":
        ALLOW_ORDERS = False
        print '\nTraining Mode Active! No real orders will be placed.'
        print '\nPress CTRL+C to exit at anytime.\n'
    else:
        ALLOW_ORDERS = True
        print '\nLive Mode Active! Real orders will be placed.'
        print '\nPress CTRL+C to exit at anytime.\n'
    print 'You have {} BTC available.'.format(AVAILABLE_BTC)
    PUMP_BALANCE = float(raw_input("How much BTC would you like to use?: "))
    while PUMP_BALANCE > AVAILABLE_BTC:
        print 'You can\'t invest more than {}'.format(AVAILABLE_BTC)
        PUMP_BALANCE = float(raw_input("How much BTC would you like to use?: "))

    PUMP_BUY = float(raw_input("\nBuy Above Current Ask by what %: "))
    PUMP_SELL = float(raw_input("Sell Above Current Ask by what %: "))

    COIN_SUMMARY, ERROR = API.get_market("BTC_USDT")
    BTC_PRICE = COIN_SUMMARY['LastPrice']

    if ERROR is not None:
        print ERROR
        break

    TIMECHECK = raw_input("Press enter to import market data. Do this between 60 to 30 seconds before coin announcement")
    MARKETS, ERROR = API.get_markets('BTC')
    if ERROR is not None:
        print ERROR
        break

    print '\n*Orders will send immediately after entering coin ticker symbol.'
    PUMP_COIN_RAW = raw_input("Coin Ticker Symbol: ")
    PUMP_COIN = PUMP_COIN_RAW.upper()

    LOW = 0
    HIGH = len(MARKETS)-1
    COININDEX = None
    while LOW <= HIGH:
        MID = (LOW+HIGH)/2
        if MARKETS[MID]['Label']==(PUMP_COIN+"/BTC"):
            COININDEX = MID
            break
        if MARKETS[MID]['Label']<(PUMP_COIN+"/BTC"):
            LOW = MID+1
        if MARKETS[MID]['Label']>(PUMP_COIN+"/BTC"):
            HIGH = MID-1

    ASK_PRICE = MARKETS[COININDEX]['AskPrice']
    LAST_PRICE = MARKETS[COININDEX]['LastPrice']
    CLOSE_PRICE = MARKETS[COININDEX]['Close']

    if LAST_PRICE > CLOSE_PRICE + 0.20 * CLOSE_PRICE:
        print '\nYou joined too late or this was pre-pumped!\nClose Price : {:.8f} . Last Price : {:.8f}'.format(CLOSE_PRICE, LAST_PRICE)
        LATE = raw_input("Still want to continue? (y/n): ")
        if LATE.lower() == "y" or LATE == "yes":
            print '\nYou joined this pump despite warning, good luck!'
        else:
            print '\nOk! Trade has been exited. No order placed.'
            break
    else:
        print '\nEntry point acceptable!'

    ASK_BUY = ASK_PRICE + (PUMP_BUY/100 * ASK_PRICE)
    ASK_SELL = ASK_PRICE + (PUMP_SELL/100 * ASK_PRICE)

    print '\nUsing {:.8f} BTC to buy {} .'.format(PUMP_BALANCE, PUMP_COIN)
    print 'Current ASK price for {} is {:.8f} BTC.'.format(PUMP_COIN, ASK_PRICE)
    print '\nASK  {}% (your specified buy point) for {} is {:.8f} BTC.'.format(PUMP_BUY, PUMP_COIN, ASK_BUY)
    print 'ASK  {}% (your specified sell point) for {} is {:.8f} BTC.'.format(PUMP_SELL, PUMP_COIN, ASK_SELL)


    # calculates the number of PUMP_COIN(s) to buy, taking into
    # consideration Cryptopia's 0.20% fee.
    NUM_COINS = (PUMP_BALANCE - (PUMP_BALANCE*0.00201)) / ASK_BUY

    BUY_PRICE = ASK_BUY * NUM_COINS
    SELL_PRICE = ASK_SELL * NUM_COINS
    PROFIT = SELL_PRICE - BUY_PRICE
    PROFITP = (PROFIT*100)/BUY_PRICE


    if ALLOW_ORDERS:
        print '\n[+] Placing buy order for {:.8f} {} coins at {:.8f} BTC for a total of {:.8f} BTC'.format(NUM_COINS, PUMP_COIN, ASK_BUY, BUY_PRICE)
        TRADE, ERROR = API.submit_trade(PUMP_COIN + '/BTC', 'Buy', ASK_BUY, NUM_COINS)
        count1 = 1
        while ERROR is not None and count1 <= 10:
            TRADE, ERROR = API.submit_trade(PUMP_COIN + '/BTC', 'Buy', ASK_BUY, NUM_COINS)
            count1 = count1 + 1
        if ERROR is not None:
            print ERROR
            break
        print'\nBuy order successfully placed'
        print TRADE
        print 'Succeeded in {} try'.format(count1)
        if ERROR is None:
            print '\n[+] Placing sell order at {:.8f} ({}%)...'.format(ASK_SELL, PUMP_SELL)
            TRADE, ERROR = API.submit_trade(PUMP_COIN + '/BTC', 'Sell', ASK_SELL, NUM_COINS)
            count2 = 1
            while ERROR is not None and count2 <= 50:
                TRADE, ERROR = API.submit_trade(PUMP_COIN + '/BTC', 'Sell', ASK_SELL, NUM_COINS)
                count2 = count2 + 1
            if ERROR is not None:
                    print ERROR
                    break
            print'\nSell order successfully placed'
            print TRADE
            print 'Succeeded in {} try'.format(count2)
    else:
        print "\n\n[!] Training Mode Active. No real orders are being placed."
        print '\n[+] Placing buy order for {:.8f} {} coins at {:.8f} BTC for a total of {:.8f} BTC'.format(NUM_COINS, PUMP_COIN, ASK_BUY, BUY_PRICE)
        print '[+] Placing sell order at {:.8f} ({}%)...'.format(ASK_SELL, PUMP_SELL)
        print "\n[!] Training Mode Active. No real orders are being placed."
    

    USDPROFIT = BTC_PRICE*PROFIT

    print '\n[*] PROFIT if sell order fills: {:.2f}%  ({:.8F} BTC)  ($ {:.2f})'.format(PROFITP, PROFIT, USDPROFIT)

    print '\nCheck Cryptopia to assure order has been filled!\n'
    print 'Adjust your order manually in Cryptopia if you observe the pump is weak and did not reach your sell limit.'

    if __name__ == "__main__":
        ANSWER = raw_input("\nWould you like to restart the Trade Bot? (y/n) ").format(PUMP_COIN)
        if ANSWER.lower().strip() in "n no".split():
            EXIT_CYCLE = True
