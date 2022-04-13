import backtrader as bt

class EMAcrossover(bt.Strategy): 
    # Exponential Moving average parameters
    params = (('pfast',9),('pslow',13),)

    def log(self, txt, dt=None):
        #dt = dt or self.datas[0].datetime[0]
        dt = dt or self.datas[0].datetime.datetime()
        #print(dt)
        #dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt} {txt}') # Comment this line when running optimization
        #print(f'{bt.num2date(dt)} {txt}') # Comment this line when running optimization

    def __init__(self):
        self.dataclose = self.datas[0].close

        # Order variable will contain ongoing order details/status
        self.order = None

        # Instantiate moving averages
        #self.fast_ma = bt.indicators.MovingAverageSimple(self.datas[0], period=self.params.pfast)
        #self.slow_ma = bt.indicators.MovingAverageSimple(self.datas[0], period=self.params.pslow)
        self.fast_ma = bt.indicators.ExponentialMovingAverage(self.datas[0], period=self.params.pfast)
        self.slow_ma = bt.indicators.ExponentialMovingAverage(self.datas[0], period=self.params.pslow)
        ''' Using the built-in crossover indicator
        self.crossover = bt.indicators.CrossOver(self.fast_sma, self.slow_sma)'''


    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # An active Buy/Sell order has been submitted/accepted - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, {order.executed.price:.2f}')
            elif order.issell():
                self.log(f'SELL EXECUTED, {order.executed.price:.2f}')
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Reset orders
        self.order = None

    def next(self):
        ''' Logic for using the built-in crossover indicator

        if self.crossover > 0: # Fast ma crosses above slow ma
            pass # Signal for buy order
        elif self.crossover < 0: # Fast ma crosses below slow ma
            pass # Signal for sell order
        '''

        # Check for open orders
        if self.order:
            return

        # Check if we are in the market
        if not self.position:
            # We are not in the market, look for a signal to OPEN trades
                
            #If the 20 SMA is above the 50 SMA  
            if self.fast_ma[0] > self.slow_ma[0] and self.fast_ma[-1] < self.slow_ma[-1]:
                self.log(f'BUY CREATE {self.dataclose[0]:2f}')
                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()
            #Otherwise if the 20 SMA is below the 50 SMA   
            elif self.fast_ma[0] < self.slow_ma[0] and self.fast_ma[-1] > self.slow_ma[-1]:
                self.log(f'SELL CREATE {self.dataclose[0]:2f}')
                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()
        else:
            # We are already in the market, look for a signal to CLOSE trades
            if len(self) >= (self.bar_executed + 5):
                self.log(f'CLOSE CREATE {self.dataclose[0]:2f}')
                self.order = self.close()

class VWAP(bt.Indicator):

    ''' This indicator needs a timer to reset the period to 1 at every session start
        also it needs a flag in next section of strategy to increment the self._vwap_period 
        run cerebro with runonce=False as we need dynamic indicator'''

    plotinfo = dict(subplot=False)

    alias = ('VWAP', 'VolumeWeightedAveragePrice','vwap',)
    lines = ('VWAP','typprice','cumprice', 'cumtypprice',)
    plotlines = dict(VWAP=dict(alpha=1.0, linestyle='-', linewidth=2.0, color = 'magenta'))

    def __init__(self):
        self._vwap_period = 1
        
    def vwap_period(self, period):
        self._vwap_period = period
        
    def next(self):
        if self.data.datetime.date(0) != self.data.datetime.date(-1):
            self._vwap_period = 1
            
        self.l.typprice[0] = ((self.data.close + self.data.high + self.data.low)/3) * self.data.volume
        self.l.cumtypprice[0] = sum(self.l.typprice.get(size=self._vwap_period), self._vwap_period)
        self.cumvol = sum(self.data.volume.get(size=self._vwap_period), self._vwap_period)
        self.lines.VWAP[0] = self.l.cumtypprice[0] / self.cumvol

        #super(vwap, self).__init__()
        
class VWAPretest(bt.Strategy): 
    # VWAP parameters
    # params = dict( 
        # vwap_period = 1,
    # )
    #params = (('vwap_period',1),)

    def log(self, txt, dt=None):
        #dt = dt or self.datas[0].datetime[0]
        dt = dt or self.datas[0].datetime.datetime()
        print(f'{dt} {txt}') # Comment this line when running optimization

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.datavwap = self.datas[0].vwap
        self.dataema_thirteen = self.datas[0].ema_thirteen
        
        # Candlestick tolerance - 0.1%
        self.tolerance = 0.001
        # Number of candles above/below vwap
        self.vwap_candle_threshold = 8
        # Stop Loss Percentage - 0.3%
        self.stoploss = 0.003
        self.account_value = 10000.0
        # Maximum Lose-able value per trade - 0.5% based on account value (e.g. 10k)
        self.max_loseable_value = 0.005 * self.account_value
        
        
        self.stoploss_value = None
        self.position_size = None
        
        #self.vwap = VWAP(self.data) # get VWAP 
        
        # Order variable will contain ongoing order details/status
        self.order = None

        # Instantiate moving averages
        #self.fast_ma = bt.indicators.MovingAverageSimple(self.datas[0], period=self.params.pfast)
        #self.slow_ma = bt.indicators.MovingAverageSimple(self.datas[0], period=self.params.pslow)
        #self.fast_ma = bt.indicators.ExponentialMovingAverage(self.datas[0], period=self.params.pfast)
        #self.slow_ma = bt.indicators.ExponentialMovingAverage(self.datas[0], period=self.params.pslow)
        ''' Using the built-in crossover indicator
        self.crossover = bt.indicators.CrossOver(self.fast_sma, self.slow_sma)'''


    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # An active Buy/Sell order has been submitted/accepted - Nothing to do
            #self.log(f'ORDER ACCEPTED/SUBMITTED', dt=order.created.dt)
            #self.order = order
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
            elif order.issell():
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Reset orders
        self.order = None
        
    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' % (trade.pnl, trade.pnlcomm))
    def next(self):
        ''' Logic for using the built-in crossover indicator

        if self.crossover > 0: # Fast ma crosses above slow ma
            pass # Signal for buy order
        elif self.crossover < 0: # Fast ma crosses below slow ma
            pass # Signal for sell order
        '''
        #self.vwap.vwap_period (self.params.vwap_period)
         ##  print values for diagnostics
        # txt = list()
        # txt.append('{}'.format(len(self.data0)))
        # txt.append('{}'.format(self.data.datetime.datetime(0)))
        # txt.append('{}'.format(self.data.close[0]))
        # txt.append('{}'.format(self.dataclose[0]))
        # txt.append('{}'.format(self.data.vwap[0]))
        # txt.append('{}'.format(self.datavwap[0]))
        # #txt.append('{}'.format(self.params.vwap_period))
        # print(', '.join(txt))
        
        candlewick_midpoint = (self.dataopen[0] + self.dataclose[0])/2
        self.data.candle_open_close_midpoint[0] = candlewick_midpoint

        # Update Local Max and Min value
        if self.datahigh[0] > self.data.current_vwap_local_max[0]:
            self.data.current_vwap_local_max[0] = self.datahigh[0]
            
        if self.datalow[0] > self.data.current_vwap_local_min[0]:
            self.data.current_vwap_local_min[0] = self.datalow[0]
        
        if len(self.data.close) >= self.vwap_candle_threshold:
            # Determine the last x candles, whether they are above or below vwap
            no_last_x_candle_pos_above = sum(candle_midpoint >= candle_vwap for candle_midpoint, candle_vwap in zip(self.data.candle_open_close_midpoint.get(size=self.vwap_candle_threshold) , self.datavwap.get(size=self.vwap_candle_threshold)))
            no_last_x_candle_pos_below  = sum(candle_midpoint <= candle_vwap for candle_midpoint, candle_vwap in zip(self.data.candle_open_close_midpoint.get(size=self.vwap_candle_threshold) , self.datavwap.get(size=self.vwap_candle_threshold)))
            
            #print(self.data.datetime.datetime(0), no_last_x_candle_pos_above, no_last_x_candle_pos_below)
            #print(len(self.data.candle_open_close_midpoint.get(size=5)), self.data.candle_open_close_midpoint.get(size=5))
            
            # Determine the last two candles' price action
            price_action_direction  = self.dataclose[0] - self.dataclose[-1]
            
            # When candle is above vwap and price action is still decreasing, it's in the direction to retest vwap
            if no_last_x_candle_pos_above >= int(round(self.vwap_candle_threshold*0.6)) and  price_action_direction < 0:
                # Check if the candle's close / low is near vwap
                if (0 <= (abs(self.dataclose[0] - self.datavwap[0]) / self.datavwap[0]) <= self.tolerance) or (0 <= (abs(self.datalow[0] - self.datavwap[0]) / self.datavwap[0]) <= self.tolerance):
                    self.data.vwap_retest_signal_rule_one[0] = 1
            
            # When candle is below vwap and price action is still increasing, it's in the direction to retest vwap
            elif no_last_x_candle_pos_below >= int(round(self.vwap_candle_threshold*0.6)) and  price_action_direction > 0:
                # Check if candle's close / high is near vwap
                if (0 <= (abs(self.dataclose[0] - self.datavwap[0]) / self.datavwap[0]) <= self.tolerance) or (0 <= (abs(self.datahigh[0] - self.datavwap[0]) / self.datavwap[0]) <= self.tolerance):
                    self.data.vwap_retest_signal_rule_one[0] = -1
                
            # Only if vwap retest rule 1 is fulfilled, check for confirmation
            if self.data.vwap_retest_signal_rule_one[-1] != 0:
                # For Long setup, check if latest candle's close is above the previous candle's close and it closes above vwap
                if (self.data.vwap_retest_signal_rule_one[-1] == 1) and (self.dataclose[0] > self.dataclose[-1]) and (self.dataclose[0] > self.datavwap[0]):
                    self.data.vwap_confirmation_candle_signal_rule_two[0] = 1

                # For Short setup, check if confilatestrmation candle's close is below the previous candle's close and it closes below vwap
                elif (self.data.vwap_retest_signal_rule_one[-1] == -1) and (self.dataclose[0] < self.dataclose[-1]) and (self.dataclose[0] < self.datavwap[0]):
                    self.data.vwap_confirmation_candle_signal_rule_two[0] = -1
            
        
        # txt = list()
        # txt.append('{}'.format(len(self.data0)))
        # txt.append('{}'.format(self.data.datetime.datetime(-1)))
        # txt.append('{}'.format(self.data.candle_open_close_midpoint[-1]))
        # txt.append('{}'.format(self.data.datetime.datetime(0)))
        # txt.append('{}'.format(self.data.candle_open_close_midpoint[0]))
        # txt.append('{}'.format(self.data.datetime.datetime(1)))
        # txt.append('{}'.format(self.data.candle_open_close_midpoint[1]))
        # txt.append('{}'.format(self.data.datetime.datetime(2)))
        # txt.append('{}'.format(self.data.candle_open_close_midpoint[2]))
        # txt.append('{}'.format(len(self.data.candle_open_close_midpoint)))
        # # txt.append('{}'.format(self.data.datetime.datetime(0)))        
        # # txt.append('{}'.format(len(self.data.close)))
        # #txt.append('{}'.format(self.params.vwap_period))
        # print(', '.join(txt)) 
        
        
        # Check for open orders
        if self.order:
            return

        # Check if we are in the market
        if not self.position:
            # We are not in the market, look for a signal to OPEN trades
            
            # If VWAP retest for LONG Position with confirmation candle
            if self.data.vwap_confirmation_candle_signal_rule_two[0] == 1:                
                # Price
                purchase_price = self.dataclose[0]
                # Calculate STOP LOSS
                self.stoploss_value = self.datavwap[0]*(1 - self.stoploss)
                # Calculate Position Sizing
                #self.position_size = round(self.max_loseable_value / abs(purchase_price - self.stoploss_value),2) # For Crypto
                self.position_size = int(round(self.max_loseable_value / abs(purchase_price - self.stoploss_value)))
                # If position_size is higher than account's value
                if self.position_size * purchase_price > self.broker.get_cash():
                    #self.position_size = round(self.broker.get_cash()/purchase_price,2)
                    self.position_size = int(self.broker.get_cash()/purchase_price)
               
                print('----------------------------------------------------------------------------')
                self.log(f'BUY CREATED at price: {purchase_price:2f}, stop loss: {self.stoploss_value:2f}, position size: {self.position_size}')

                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy(size=self.position_size, price=purchase_price)
            
            # Otherwise if VWAP retest for SHORT Position with confirmation candle    
            elif self.data.vwap_confirmation_candle_signal_rule_two[0] == -1:
                #self.log(f'SELL CREATED {self.dataclose[0]:2f}')
                
                # Price
                purchase_price = self.dataclose[0]
                # Calculate STOP LOSS
                self.stoploss_value = self.datavwap[0]*(1 + self.stoploss)
                # Calculate Position Sizing
                #self.position_size = round(self.max_loseable_value / abs(purchase_price - self.stoploss_value),2) # For Crypto
                self.position_size = int(round(self.max_loseable_value / abs(purchase_price - self.stoploss_value)))
                # If position_size is higher than account's value
                if self.position_size * purchase_price > self.broker.get_cash():
                    #self.position_size = round(self.broker.get_cash()/purchase_price,2)
                    self.position_size = int(self.broker.get_cash()/purchase_price)
                
                print('----------------------------------------------------------------------------')
                self.log(f'SELL CREATED at price: {purchase_price:2f}, stop loss: {self.stoploss_value:2f}, position size: {self.position_size}')
                
                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell(size=self.position_size, price=purchase_price)
            
        else:
            # Monitor for Soft Stop Loss (2 Candles below/above stop loss) for LONG position
            #print(self.position)
            # LONG position and Close is below Stop Loss
            if (self.position.size > 0) and (self.dataclose[0] <= self.stoploss_value):
                self.data.soft_stop_loss[0] = self.data.soft_stop_loss[-1] + 1
            # For SHORT position and Close is above Stop Loss
            elif (self.position.size < 0) and (self.dataclose[0] >= self.stoploss_value):
                self.data.soft_stop_loss[0] = self.data.soft_stop_loss[-1] + 1
            else:
                self.data.soft_stop_loss[0] = 0
            
            # Soft Stop Loss hit 2 times, close position
            if self.data.soft_stop_loss[0] >= 2:
                self.log(f'SOFT STOP LOSS HIT, CLOSE CREATE {self.dataclose[0]:2f}')
                self.order = self.close()
                        
            # Take Profit when crosses EMA13 when in the green (check < or > entry price)
            #print(self.position)
            # LONG position, Close is crosses below EMA13 and entry price is lower than EMA13
            if (self.position.size > 0) and ((self.dataclose[0] < self.dataema_thirteen[0]) and (self.dataclose[-1] > self.dataema_thirteen[-1])) and (self.position.price <= self.dataema_thirteen[0]):
                self.log(f'CROSSES BELOW EMA13, CLOSE CREATE {self.dataclose[0]:2f}')
                self.order = self.close()
            # SHORT position, Close is crosses above EMA13 and entry price is higher than EMA13
            elif (self.position.size < 0) and ((self.dataclose[0] > self.dataema_thirteen[0]) and (self.dataclose[-1] < self.dataema_thirteen[-1])) and (self.position.price >= self.dataema_thirteen[0]):
                self.log(f'CROSSES ABOVE EMA13, CLOSE CREATE {self.dataclose[0]:2f}')
                self.order = self.close()
            
            # # We are already in the market, look for a signal to CLOSE trades
            # if len(self) >= (self.bar_executed + 5):
                
                # # Implement Soft Stop Loss
                
                # # Detect Previous Swing High/ Swing Low
                
                # # Take Partial Profit at 1%, 1.5% and 2%
                
                # self.log(f'CLOSE CREATE {self.dataclose[0]:2f}')
                # self.order = self.close()