import os, socket, requests, urllib3, config
from datetime import datetime
from termcolor import colored
from binance.client import Client
from binance.exceptions import BinanceAPIException
from apscheduler.schedulers.blocking import BlockingScheduler
import pytz
from webhook_launcher import telegram_bot_sendtext

# Get environment variables
api_key     = ''
api_secret  = ''
client      = Client(api_key, api_secret)

# Value from config.py
live_trade = config.live_trade
base = config.base
core  = config.core
quote  = config.quote
margin_percentage = config.margin_percentage
enable_scheduler = config.enable_scheduler

# Trading Setup
pair,round_off = [], []
for i in range(len(base)):
    if len(quote) > 1 : my_quote_asset = quote[i]
    else: my_quote_asset = quote[0]
    pair.append(base[i] + quote[i])

for coin in quote:
    if coin == "USDT": decimal = 2
    elif coin == "BTC": decimal = 6
    elif coin == "ETH": decimal = 5
    elif coin == "BNB": decimal = 3
    elif coin == "BUSD": decimal = 2
    else: decimal == 4
    round_off.append(decimal)

def buy_low_sell_high():
    for i in range(len(pair)):

        # Auto Adjust FIXED or DYNAMIC variable
        if len(quote) > 1 : my_quote_asset = quote[i]
        else: my_quote_asset = quote[0]
        if len(core) > 1 : my_core_number = core[i]
        else: my_core_number = core[0]
        if len(round_off) > 1 : my_round_off = round_off[i]
        else: my_round_off = round_off[0]

        # Retrieve Current Asset INFO
        asset_info      = client.get_symbol_ticker(symbol=pair[i])
        asset_price     = float(asset_info.get("price"))
        asset_balance   = float(client.get_asset_balance(asset=base[i]).get("free"))

        # Computing for Trade Quantity
        current_holding = round(asset_balance * asset_price, my_round_off)
        change_percent  = round(((current_holding - my_core_number) / my_core_number * 100), 4)
        trade_amount    = round(abs(current_holding - my_core_number), my_round_off)
        
        # Output Console and Placing Order
        if (current_holding > my_core_number) and (abs(change_percent) > margin_percentage):
            if live_trade: client.order_market_sell(symbol=pair[i], quoteOrderQty=trade_amount)
            print(colored(asset_info, "green"))
            print(colored("Created at           : " + str(datetime.today().strftime("%d-%m-%Y @ %H:%M:%S")), "green"))
            print(colored("Prefix Core          : " + str(my_core_number) + " " + my_quote_asset, "green"))
            print(colored("Current Core         : " + str(current_holding) + " " + my_quote_asset, "green"))
            print(colored("Percentage Changed   : " + str(change_percent) + " %", "green"))
            print(colored("Action               : SELL " + str(trade_amount) + " " + my_quote_asset + "\n", "green"))
            telegram_bot_sendtext(str(asset_info) + "\n" +
                                 "Created at           : " + str(datetime.today().strftime("%d-%m-%Y @ %H:%M:%S")) + "\n" +
                                 "Prefix Core          : " + str(my_core_number) + " " + my_quote_asset + "\n" +
                                 "Current Core         : " + str(current_holding) + " " + my_quote_asset + "\n" +
                                 "Percentage Changed   : " + str(change_percent) + " %" + "\n" +
                                 "Action               : SELL " + str(trade_amount) + " " + my_quote_asset + "\n"
                                 )

        elif (current_holding < my_core_number) and (abs(change_percent) > margin_percentage):
            if live_trade: client.order_market_buy(symbol=pair[i], quoteOrderQty=trade_amount)
            print(colored(asset_info, "red"))
            print(colored("Created at           : " + str(datetime.today().strftime("%d-%m-%Y @ %H:%M:%S")), "red"))
            print(colored("Prefix Core          : " + str(my_core_number) + " " + my_quote_asset, "red"))
            print(colored("Current Core         : " + str(current_holding) + " " + my_quote_asset, "red"))
            print(colored("Percentage Changed   : " + str(change_percent) + " %", "red"))
            print(colored("Action               : BUY " + str(trade_amount) + " " + my_quote_asset + "\n", "red"))
            telegram_bot_sendtext(str(asset_info) + "\n" +
                                 "Created at           : " + str(datetime.today().strftime("%d-%m-%Y @ %H:%M:%S")) + "\n" +
                                 "Prefix Core          : " + str(my_core_number) + " " + my_quote_asset + "\n" +
                                 "Current Core         : " + str(current_holding) + " " + my_quote_asset + "\n" +
                                 "Percentage Changed   : " + str(change_percent) + " %" + "\n" +
                                 "Action               : BUY " + str(trade_amount) + " " + my_quote_asset + "\n"
                                 )

        else:
            print(asset_info)
            print("Created at           : " + str(datetime.today().strftime("%d-%m-%Y @ %H:%M:%S")))
            print("Prefix Core          : " + str(my_core_number) + " " + my_quote_asset)
            print("Current Core         : " + str(current_holding) + " " + my_quote_asset)
            print("Percentage Changed   : " + str(change_percent) + " %")
            print("Action               : Do Nothing\n")

            telegram_bot_sendtext(str(asset_info) + "\n" +
                                 "Created at           : " + str(datetime.today().strftime("%d-%m-%Y @ %H:%M:%S")) + "\n" +
                                 "Prefix Core          : " + str(my_core_number) + " " + my_quote_asset + "\n" +
                                 "Current Core         : " + str(current_holding) + " " + my_quote_asset + "\n" +
                                 "Percentage Changed   : " + str(change_percent) + " %"+ "\n" +
                                 "Action               : Do Nothing\n"
                                 )            

try:
    if live_trade and enable_scheduler:
        print(colored("The program is running.\n", "green"))
        buy_low_sell_high()
        scheduler = BlockingScheduler(timezone=pytz.timezone('Asia/Ho_Chi_Minh'))
        # scheduler.add_job(buy_low_sell_high, 'cron', hour='0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23')
        scheduler.add_job(buy_low_sell_high, 'interval', hours=1)
        scheduler.start()        
    else: buy_low_sell_high()

except (KeyError,
        socket.timeout,
        BinanceAPIException,
        ConnectionResetError,
        urllib3.exceptions.ProtocolError,
        urllib3.exceptions.ReadTimeoutError,
        requests.exceptions.ConnectionError,
        requests.exceptions.ConnectTimeout,
        requests.exceptions.ReadTimeout) as e:

    with open("Error_Message.txt", "a") as error_message:
        error_message.write("[!] Created at : " + datetime.today().strftime("%d-%m-%Y @ %H:%M:%S") + "\n")
        error_message.write(str(e) + "\n\n")

except KeyboardInterrupt: print("\n\nAborted.\n")
