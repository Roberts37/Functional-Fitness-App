#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import ccxt
import random
import numpy as np
from datetime import datetime
from time import sleep
import warnings
warnings.filterwarnings('ignore')
from pprint import pprint
import pandas_ta as ta
import time
import crab_api as api # change to correct api for aws
from apscheduler.schedulers.background import BackgroundScheduler


# In[2]:


class Raven:
    
    in_position = False
    long = False
    short = False
    first = False
    in_trend = False
    can_long = False
    symbols = ['KAVAUSD','ETHUSD','AVAXUSD','LINKUSD','MATICUSD','BNBUSD','KSMUSD','GMXUSD','DOTUSD']
    symbol = 'ETHUSD'
    last_trade = 'MATICUSD'
    runs = 10

    
    def __init__(self, time, long_time, bars, leverage):
        self.exchange = ccxt.phemex({
            'apiKey':api.key,#api.key
            'secret':api.secret})#api.secret
        #self.symbol = symbol
        self.time = time
        self.long_time_frame = long_time
        self.bars = bars
        self.leverage = leverage
        self.long_stop_loss = 0.98
        self.short_stop_loss = 1.02
        self.top_long_position = 0
        self.top_short_position = 0
        self.top_long_position_exit = 0
        self.top_short_position_exit = 0

        if Raven.first == False:
            Raven.set_leverage(self)
            Raven.first = True
        else:
            pass
        
        
    def long_data_timeframe(self):
        assets = ['KAVAUSD','ETHUSD','AVAXUSD','LINKUSD','MATICUSD','BNBUSD','KSMUSD','GMXUSD','DOTUSD']
        Raven.symbols = []
        random.shuffle(assets)
        
        for ass in assets:
            Raven.symbol = ass
            print('the current symbol passing through the long_data_timeframe function is: ' + ass)
            long_df = pd.DataFrame(self.exchange.fetch_ohlcv(Raven.symbol,since=None, timeframe=self.long_time_frame, limit=self.bars))
            long_df.columns=['time','open','high','low','close','volume']
            long_df['time'] = pd.to_datetime(long_df['time'], unit='ms')

            while True:
                if len(long_df.index) < 500:
                    sleep(10)
                    long_df = pd.DataFrame(self.exchange.fetch_ohlcv(Raven.symbol, since=None, timeframe=self.long_time_frame, limit = self.bars))
                    long_df.columns = ['time','open','high','low','close','volume']
                    long_df['time'] = pd.to_datetime(long_df['time'], unit='ms')

                elif len(long_df.index) == 500:
                    break

            # long_df.ta.adx(length=20,inplace=True)
            # long_df['adx'] = long_df['ADX_20']
            long_df['adx'] = long_df.ta.adx(length=20,inplace=True)['ADX_20']
            # long_df['hilo'] = long_df.ta.hilo(high_length=250, low_length=250,append=True)['HILO_250_250']
            for current in range(1,len(long_df)):
                lookback = current - 20
                if long_df.loc[current,'adx'] < 20 or long_df.loc[current, 'adx'] < long_df.loc[lookback:current,'adx'].max() -5:
                    long_df.loc[current,'in_trend'] = False
                else:
                    long_df.loc[current,'in_trend'] = True

                # if long_df.loc[current,'close'] > long_df.loc[current,'hilo']:
                #     long_df.loc[current,'can_long'] = True
                # else:
                #     long_df.loc[current,'can_long'] = False
                    
            if long_df.iloc[-1]['in_trend'] == True:
                # Raven.in_trend = True
                # Raven.can_long = long_df.iloc[-1]['can_long']
                Raven.symbols.append(ass)
                # break 
            sleep(5)
                
        if len(Raven.symbols) == 0:
            Raven.in_trend = False
        elif len(Raven.symbols) > 0:
            Raven.in_trend = True
            print('Symbols List: ')
            print(Raven.symbols)
        
        print('Raven in_trend: ' + str(Raven.in_trend))
        # print(long_df.iloc[-3:])
                
        return long_df
    
    
    
    def long_short(self):
        
        ls_df = pd.DataFrame(self.exchange.fetch_ohlcv(Raven.symbol,since=None, timeframe=self.long_time_frame, limit=self.bars))
        ls_df.columns=['time','open','high','low','close','volume']
        ls_df['time'] = pd.to_datetime(ls_df['time'], unit='ms')

#         while True:
#             if len(ls_df.index) < 500:
#                 sleep(10)
#                 ls_df = pd.DataFrame(self.exchange.fetch_ohlcv(Raven.symbol, since=None, timeframe=self.long_time_frame, limit = self.bars))
#                 ls_df.columns = ['time','open','high','low','close','volume']
#                 ls_df['time'] = pd.to_datetime(ls_df['time'], unit='ms')

#             elif len(ls_df.index) == 500:
#                 break
        ls_df['hilo'] = ls_df.ta.hilo(high_length=250, low_length=250,append=True)['HILO_250_250']
        
        for current in range(1,len(ls_df.index)):
            if ls_df.loc[current,'close'] > ls_df.loc[current,'hilo']:
                ls_df.loc[current,'can_long'] = True
            else:
                ls_df.loc[current,'can_long'] = False
                
        if ls_df.iloc[-1]['can_long'] == True:
            Raven.can_long = True
        else:
            Raven.can_long = False
            
        print('Can long: ' + Raven.symbol + ' ' + str(Raven.can_long))
        sleep(5)
            
        return ls_df
        
        
    def data(self):
        df = pd.DataFrame(self.exchange.fetch_ohlcv(Raven.symbol, since=None, timeframe=self.time, limit = self.bars))
        df.columns = ['time','open','high','low','close','volume']
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        while True:
            if len(df.index) < 500:
                sleep(10)
                df = pd.DataFrame(self.exchange.fetch_ohlcv(Raven.symbol, since=None, timeframe=self.time, limit = self.bars))
                df.columns = ['time','open','high','low','close','volume']
                df['time'] = pd.to_datetime(df['time'], unit='ms')
        
            elif len(df.index) == 500:
                break
        #------------------ To Change Algo Change between here --------------------------------
        # df.ta.macd(fast=25,slow=40,signal=25, append=True)
        df.ta.hilo(high_length = 90, low_length = 90, append=True)
        df.ta.hilo(high_length = 150, low_length = 150, append=True)
        df.drop(columns = 'HILOl_150_150',inplace=True)
        df.drop(columns = 'HILOs_150_150',inplace=True)
        df.drop(columns = 'HILOl_90_90',inplace=True)
        df.drop(columns = 'HILOs_90_90',inplace=True)
        # df.drop(columns = 'MACD_25_40_25', inplace=True)
        # df.drop(columns = 'MACDs_25_40_25',inplace=True)
        df['long'] = False
        df['short'] = False
        
        for current in range(1,len(df.index)):
            lookback = current - 10
            previous = current - 1
            
            if df.loc[current,'close'] > df.loc[current,'HILO_90_90'] and df.loc[previous,'close'] < df.loc[previous, 'HILO_90_90'] and df.loc[current,'close'] > df.loc[current,'HILO_150_150']:
                df.loc[current,'long'] = True
            elif df.loc[previous,'long'] and df.loc[current,'close'] > df.loc[current,'HILO_90_90'] and df.loc[current,'close'] > df.loc[current,'HILO_150_150']:
                df.loc[current,'long'] = True
            else:
                df.loc[current,'long'] = False
                
            if df.loc[current,'close'] < df.loc[current,'HILO_90_90'] and df.loc[previous,'close'] > df.loc[previous, 'HILO_90_90'] and df.loc[current,'close'] < df.loc[current,'HILO_150_150']:
                df.loc[current,'short'] = True
            elif df.loc[previous,'short'] and df.loc[current,'close'] < df.loc[current,'HILO_90_90'] and df.loc[current,'close'] < df.loc[current,'HILO_150_150']:
                df.loc[current,'short'] = True
            else:
                df.loc[current,'short'] = False
        # self.exchange.set_leverage(self.leverage, Raven.symbol)
        return df
    
        #------------------ To Change Algo Change between here --------------------------------
    
    
    def get_balance(self):
        params={"type":"swap","code":"USD"}
        response = self.exchange.fetch_balance(params=params)
        free = response['free']
        balance = free['USD']
    #pprint(f'this is your usd balance {balance}')
    
        markets = self.exchange.fetchMarkets()
        index = 0
        for x in markets:
            if x['id'] == Raven.symbol:
                market = markets[index]
                contract_size = market['contractSize']
            else:
                index+=1
    #pprint(f'this is the contract size {contract_size}')
    
        ob = self.exchange.fetch_order_book(Raven.symbol)
        bid = ob['bids'][0][0]
        ask = ob['asks'][0][0]
        mid_price = (ask + bid) / 2
    #print(f'this is the middle price {mid_price}')

        contract_amount = mid_price * contract_size
    #print(f'1 contract should equal about this much {contract_amount}')
    
        purchase = (balance // contract_amount -1) * self.leverage
    #print(f'if you are wanting to put your whole balance in which i know you do, you will be buying {purchase} many contracts based on your account size')
    
    #purchase = int(purchase)
        return purchase
    
    
    def close_size(self):
        psl = self.exchange.fetch_positions()
        index = 0
        for x in psl:
            if psl[index]['info']['symbol'] == Raven.symbol:
                poi = psl[index]# this will need to updated based on which asset
                poi = poi['info']
                ze = poi['size']
                clo_size = int(ze)
            else:
                index +=1
        return clo_size
    
    
    
    def entry_price(self):
        entry = self.exchange.fetch_positions()
        index = 0
        for x in entry:
            if entry[index]['info']['symbol'] == Raven.symbol:
                poi = entry[index]
                entry_price = poi['entryPrice']    
            else:
                index+=1
                  
        return entry_price
    

    def current_price(self):
        ob = self.exchange.fetch_order_book(Raven.symbol)
        bid = ob['bids'][0][0]
        ask = ob['asks'][0][0]
        current_price = (ask + bid) / 2
        
        return current_price
    
    
    
    
    def set_leverage(self):
        assets = ['KAVAUSD','ETHUSD','AVAXUSD','LINKUSD','MATICUSD','BNBUSD','KSMUSD','GMXUSD','DOTUSD']
        for ass in assets:
            self.exchange.set_leverage(self.leverage, ass)
            
            
            
    def long_position_close(self):
        self.exchange.create_limit_sell_order(Raven.symbol,Raven.close_size(self), self.exchange.fetch_order_book(Raven.symbol)['asks'][0][0]) #self.exchange.create_limit_sell_order(Raven.symbol,Raven.close_size(self), self.exchange.fetch_order_book(Raven.symbol)['asks'][0][0])
        sleep(120)
        if len(self.exchange.fetch_open_orders(Raven.symbol)) != 0:
            self.exchange.cancel_all_orders(Raven.symbol)
            self.exchange.create_order(Raven.symbol,'market','sell',Raven.close_size(self)) #self.exchange.create_order(Raven.symbol,'market','sell',Raven.close_size(self))
        Raven.in_position = False
        Raven.long = False
        print('Long position closed'+Raven.symbol +str(datetime.now()))
        self.top_long_position = 0
        self.top_long_position_exit = 0
        Raven.last_trade = Raven.symbol
        sleep(10)
        
        
    def short_position_close(self):
        self.exchange.create_limit_buy_order(Raven.symbol,Raven.close_size(self),self.exchange.fetch_order_book(Raven.symbol)['bids'][0][0]) #self.exchange.create_limit_buy_order(Raven.symbol,Raven.close_size(self),self.exchange.fetch_order_book(Raven.symbol)['bids'][0][0])
        sleep(120)
        if len(self.exchange.fetch_open_orders(Raven.symbol)) != 0:
            self.exchange.cancel_all_orders(Raven.symbol)
            self.exchange.create_order(Raven.symbol,'market','buy',Raven.close_size(self)) #self.exchange.create_order(Raven.symbol,'market','buy',Raven.close_size(self))
        Raven.in_position = False 
        Raven.short = False
        print('Short position closed'+Raven.symbol+str(datetime.now()))
        self.top_short_position = 0
        self.top_short_position_exit = 0
        Raven.last_trade = Raven.symbol
        sleep(10)
            
            

    def algo(self):
        
        print(datetime.now())
        
        
        
        if Raven.in_position == True:
            df = Raven.data(self)
            current = len(df.index) - 1
            previous = current - 1
            look_back = range(current-10,current+1)
            
            
            entry = Raven.entry_price(self)
            price = Raven.current_price(self)
            
            #calculates where we currently are in terms of pnl
            long_position = (price / entry *100) -100
            short_position = (entry / price *100) - 100
            
            
            if Raven.runs > 4:
                Raven.runs = 1
            

                
            print(df.iloc[-3:])
        
            
            if Raven.long == True:

                if long_position > self.top_long_position:
                    self.top_long_position = long_position                   
                    
                if self.top_long_position > 5:
                    self.top_long_position_exit = 0.9   
                elif self.top_long_position > 3:
                    self.top_long_position_exit = 0.75
                elif self.top_long_position > 1:
                    self.top_long_position_exit = 0.6
                    
                if self.top_long_position > 1:
                    if long_position <= self.top_long_position * self.top_long_position_exit:
                        Raven.long_position_close(self)
                        print('closed on the top_long_position_exit rule')
                        self.top_long_position = 0
                        self.top_long_position_exit = 0

                if self.top_long_position > 7:
                    Raven.long_position_close(self)
                    print('closed on the greater than 7 rule')
                    self.top_long_position = 0
                    self.top_long_position_exit = 0

                if Raven.in_position == True:

                    if not df['long'][current] or price < entry * self.long_stop_loss or price < df['close'][look_back].max() * self.long_stop_loss:
                        Raven.long_position_close(self)
                        print('closed due to not long rule')
                    else:
                        print(f'top_long_position: {self.top_long_position}')
                        print(f'top_long_position_exit: {self.top_long_position_exit}')
                        print(f'top long position exit target: {self.top_long_position * self.top_long_position_exit}')
                        print(f'Our entry price was: {entry}')
                        print(f'The current price of {Raven.symbol} is: {price}')
                        print(f'Still in the position with a current pnl: {round(long_position,2)}%' + str(datetime.now()))
                    
            elif Raven.short == True:   

                if short_position > self.top_short_position:
                    self.top_short_position = short_position
                    
                if self.top_short_position > 5:
                    self.top_short_position_exit = 0.9  
                elif self.top_short_position > 3:
                    self.top_short_position_exit = 0.75
                elif self.top_short_position > 1:
                    self.top_short_position_exit = 0.6

                    
                if self.top_short_position > 1:
                    if short_position <= self.top_short_position * self.top_short_position_exit:
                        Raven.short_position_close(self)
                        print('closed on the top_long_position_exit rule')
                        self.top_short_position_exit = 0
                        self.top_short_position = 0

                if self.top_short_position > 7:
                    Raven.short_position_close(self)
                    print('closed on the greater than 7 rule')
                    self.top_short_position_exit = 0
                    self.top_short_position = 0 

                if Raven.in_position == True:
                               
                
                    if not df['short'][current] or price > entry * self.short_stop_loss or price > df['close'][look_back].min() * self.short_stop_loss:
                        Raven.short_position_close(self)
                        print('closed due to not short rule')
                        
                    else:
                        print(f'top_short_position: {self.top_short_position}')
                        print(f'top_short_position_exit: {self.top_short_position_exit}')
                        print(f'top short position exit target: {self.top_short_position * self.top_short_position_exit}')
                        print(f'Our entry price was: {entry}')
                        print(f'The current price of {Raven.symbol} is: {price}')
                        print(f'Still in the position with a current pnl: {round(short_position,2)}%' + str(datetime.now()))

                
                    
        if Raven.in_position == False:
            # if Raven.runs > 4: # change this based on time frames
            #     Raven.long_data_timeframe(self)
            #     Raven.runs = 1
            random.shuffle(Raven.symbols)
                
            sleep(20)
            
            
            
                
            for current_symbol in Raven.symbols:
                if current_symbol == Raven.last_trade:
                    print(f'our last trade was on {Raven.last_trade} skipping to next asset')
                    pass
                else:
                    Raven.symbol = current_symbol
                    print("current symbol in algo function: " + str(Raven.symbol))
                    #Raven.long_short(self)
                    df = Raven.data(self)
                    current = len(df.index) - 1
                    previous = current - 1

                    if df['long'][current] and not df['long'][previous]:
                        self.exchange.create_limit_buy_order(Raven.symbol, Raven.get_balance(self), self.exchange.fetch_order_book(Raven.symbol)['bids'][0][0]) #self.exchange.create_limit_buy_order(Raven.symbol, Raven.get_balance(self), self.exchange.fetch_order_book(Raven.symbol)['bids'][0][0])
                        sleep(60)
                        if len(self.exchange.fetch_open_orders(Raven.symbol)) != 0:
                            self.exchange.cancel_all_orders(Raven.symbol)
                            self.exchange.create_order(Raven.symbol,'market','buy',Raven.get_balance(self)) #self.exchange.create_order(Raven.symbol,'market','buy',Raven.get_balance(self))
                        Raven.in_position = True
                        Raven.long = True
                        print('Long position entered' + Raven.symbol +str(datetime.now()))
                        break
                        sleep(10)

                    elif df['short'][current] and not df['short'][previous]:
                        self.exchange.create_limit_sell_order(Raven.symbol,Raven.get_balance(self),self.exchange.fetch_order_book(Raven.symbol)['asks'][0][0])#self.exchange.create_limit_sell_order(Raven.symbol,Raven.get_balance(self),self.exchange.fetch_order_book(Raven.symbol)['asks'][0][0])
                        sleep(60)
                        if len(self.exchange.fetch_open_orders(Raven.symbol)) != 0:
                            self.exchange.cancel_all_orders(Raven.symbol)
                            self.exchange.create_order(Raven.symbol,'market','sell',Raven.get_balance(self)) #self.exchange.create_order(Raven.symbol,'market','buy',Raven.get_balance(self))
                        Raven.in_position = True
                        Raven.short = True
                        print('Short position entered'+Raven.symbol + str(datetime.now()))
                        break
                        sleep(10)
                    else:
                        print('No positions were entered at this time: ' + str(datetime.now()))
                        sleep(8)
                            
        Raven.runs += 1


# In[3]:


Refine = Raven('1h','1h', 500, 1)
sched = BackgroundScheduler()


# In[4]:


# sched.add_job(Refine.long_data_timeframe,'interval',minutes=15)
sched.add_job(Refine.algo,'interval', hours=1)
# sched.add_job(Refine.long_data_timeframe,'interval',minutes=15)
 
    # Starts the Scheduled jobs
sched.start()
 
    # Runs an infinite loop
while True:
    sleep(1)


# In[ ]:




