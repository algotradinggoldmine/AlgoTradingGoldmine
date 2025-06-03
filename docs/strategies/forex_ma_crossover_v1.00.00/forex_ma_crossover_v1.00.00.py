###[name]=ForexMACrossover
###[version]=1.00.00
###[label]=20250520-001

# V1.00.00
# Init (初始化)

# ta_lib.MA_Type (ta_lib.移动平均线类型)
# Simple Moving Average (简单移动平均线)
SMA = 0
# Exponential Moving Average (指数移动平均线)
EMA = 1
# Weighted Moving Average (加权移动平均线)
WMA = 2
# Double Exponential Moving Average (双指数移动平均线)
DEMA = 3
# Triple Exponential Moving Average (三指数移动平均线)
TEMA = 4
# Triangular Moving Average (三角移动平均线)
TRIMA = 5
# Kaufman Adaptive Moving Average (Kaufman 自适应移动平均线)
KAMA = 6
# MESA Adaptive Moving Average (MESA 自适应移动平均线)
MAMA = 7
# Triple Generalized Double Exponential Moving Average (三重广义双指数移动平均线)
T3 = 8


class ForexMACrossover:
    """
    A basic framework for a Forex Moving Average Crossover trading strategy.
    一个用于外汇移动平均线交叉交易策略的基本框架。
    """
    def __init__(self):
        # Default processing pipelines for different stages of the strategy
        # 策略不同阶段的默认处理流程
        self.default_process = {
            'run_processes': {
                'process_orders': {'func': self.process_orders},
                'open_orders': {'func': self.open_orders},
            },
            'open_processes': {},
            'order_processes': {}

        }
        self.options = {
            'run_processes': [
                {'name': 'process_orders'},
                {'name': 'open_orders'},
            ],
            'open_processes': [
                {'name': 'open_new_order', 'func': self.open_new_order, 'order_list': True},
            ],
            'order_processes': [
                {'name': 'close_order', 'func': self.close_order, 'order_list': False},
            ]
        }

    def forex_intraday_ma_crossover_with_confirmation(self, timeframe, short_window, medium_window, confirmation_window, op):
        """
        适用于外汇周内交易的价格确认的移动平均线交叉策略。
        Forex intraday Moving Average crossover strategy with price confirmation.

        Args:
            timeframe: time frame (时间框架)
            short_window (int): 短期 EMA 周期。
                                Short-term EMA period.
            medium_window (int): 中期 EMA 周期。
                                 Medium-term EMA period.
            confirmation_window (int): 价格确认周期。
                                       Price confirmation period.

        Returns:
            signal: 当op=='open'时，返回buy或sell，当op=='close'时，返回close_long或close_short，如果返回空则无信号
                    When op=='open', returns 'buy' or 'sell'; when op=='close', returns 'close_long' or 'close_short'. Returns empty string if no signal.
        """
        max_bars = medium_window + 24 # Maximum bars needed for calculations (计算所需的最大K线数量)
        sd_h1 = GetSymbolData(Symbol(), timeframe=timeframe, size=max_bars) # Get symbol data (获取交易品种数据)
        signal = '' # Initialize signal (初始化信号)
        # Calculate EMAs for crossover detection with shifts (计算用于交叉检测的EMA并考虑偏移量)
        short_ema_1 = iMA(sd_h1.close, timeperiod=short_window, matype=EMA, shift=confirmation_window + 1)
        medium_ema_1 = iMA(sd_h1.close, timeperiod=medium_window, matype=EMA, shift=confirmation_window + 1)
        short_ema_2 = iMA(sd_h1.close, timeperiod=short_window, matype=EMA, shift=confirmation_window + 2)
        medium_ema_2 = iMA(sd_h1.close, timeperiod=medium_window, matype=EMA, shift=confirmation_window + 2)

        if op == 'close':
            # 卖出平多逻辑 (Logic for closing long positions)
            if short_ema_1 < medium_ema_1 and short_ema_2 >= medium_ema_2:
                signal = 'close_long'
            # 买入平空逻辑 (Logic for closing short positions)
            elif short_ema_1 > medium_ema_1 and short_ema_2 <= medium_ema_2:
                signal = 'close_short'
        else:
            # 买入逻辑 (Buy logic)
            if short_ema_1 > medium_ema_1 and short_ema_2 <= medium_ema_2:
                # 检查价格确认 (Check price confirmation)
                confirmed = True
                for j in range(0, confirmation_window):
                    short_ema = iMA(sd_h1.close, timeperiod=short_window, matype=EMA, shift=confirmation_window-j)
                    if sd_h1.close[confirmation_window-j] < short_ema: # If close price is below short EMA, not confirmed (如果收盘价低于短期EMA，则未确认)
                        confirmed = False
                        break
                if confirmed:
                    signal = 'buy'

            # 卖出逻辑 (Sell logic)
            elif short_ema_1 < medium_ema_1 and short_ema_2 >= medium_ema_2:
                # 检查价格确认 (Check price confirmation)
                confirmed = True
                for j in range(0, confirmation_window):
                    short_ema = iMA(sd_h1.close, timeperiod=short_window, matype=EMA, shift=confirmation_window-j)
                    if sd_h1.close[confirmation_window-j] > short_ema: # If close price is above short EMA, not confirmed (如果收盘价高于短期EMA，则未确认)
                        confirmed = False
                        break
                if confirmed:
                    signal = 'sell'

        return signal


    def close_order(self, order, operation):
        '''平仓 / Close Position'''
        close = False
        # 获利大于 600 直接平仓 (Close position directly if profit is greater than or equal to 600)
        if order.profit >= 600:
            close = True
        else:
            # 盈利未达预期，则使用平仓信号判断是否平仓 (If profit is not as expected, use the closing signal to determine whether to close)
            signal = self.forex_intraday_ma_crossover_with_confirmation(timeframe=TimeFrame.H1, short_window=4,
                                                                        medium_window=24, confirmation_window=0,
                                                                        op='close')
            # 平掉多单 (Close long positions)
            if order.is_long() and signal == 'close_long':
                close = True
            # 平掉空单 (Close short positions)
            elif order.is_short() and signal == 'close_short':
                close = True
        #是否执行平仓 (Whether to execute the closing operation)
        if close:
            CloseOrder(order.uid, volume=order.volume, tags='')
            return True # Order was closed (订单已平仓)
        return False # Order was not closed (订单未平仓)

    def open_new_order(self, new_order_list, params):
        '''开仓 / Open Position'''
        # 最大开仓量为1单 (Maximum open positions is 1)
        max_orders = 1
        # Get currently opened orders (获取当前已开订单)
        opened_order_list = GetOpenedOrderUIDs(scope=DataScope.EA_VERSION)

        # 判断是否超过最大开仓量 (Check if the maximum number of open positions has been exceeded)
        if len(opened_order_list) >= max_orders:
            # Do not open new orders if max limit reached (如果达到最大限制，则不打开新订单)
            return False
        # 获得开仓信号 (Get the opening signal)
        signal = self.forex_intraday_ma_crossover_with_confirmation(timeframe=TimeFrame.M5, short_window=6, medium_window=24,
                                                                    confirmation_window=2, op='open')
        # 如果获得买入或卖出信号，则执行开仓命令 (If a buy or sell signal is received, execute the open order command)
        if signal in ('buy', 'sell'):
            new_order_dict = {}
            new_order_dict['errid'] = 0
            new_order_dict['position'] = PositionType.LONG if signal == 'buy' else PositionType.SHORT
            new_order_dict['price'] = Ask() if signal == 'buy' else Bid()
            new_order_dict['size'] = 1
            new_order_dict['tags'] = ''
            new_order_list.append(new_order_dict)
            return True
        return False

    def open_orders(self, params):
        """
        Handles the opening of new orders based on the 'open_processes' configuration.
        根据 'open_processes' 配置处理新订单的开立。

        Args:
            params (dict): A dictionary of parameters that can be passed to the function
                           (currently not used in this basic framework).
                           可以传递给函数的参数字典（当前在此基本框架中未使用）。

        Returns:
            tuple: A tuple containing an error code (0 for success, -1 or -2 for failure) and
                   a list of dictionaries, each containing the order details and its error code.
                   一个元组，包含错误代码（0 表示成功，-1 或 -2 表示失败）和
                   一个字典列表，每个字典包含订单详细信息及其错误代码。
        """
        process_name = 'open_processes'
        operation_list = self.options[process_name]
        new_order_list = []

        for operation in operation_list:
            func = operation.get('func', self.default_process[process_name].get(operation['name'], {'func': None})['func'])
            if func is None:
                print(f"Func {operation['name']} is None!")
                return -2, None

            using_order_list = operation.get('order_list', False)
            if using_order_list:
                if not func(new_order_list, operation):
                    return -1, None
            else:
                for new_order in new_order_list:
                    if new_order['errid'] != 0:
                        continue
                    if not func(new_order, operation):
                        new_order['errid'] = -1

        ret = []
        for new_order in new_order_list:
            errid = new_order['errid']
            rv = dict(order=new_order, errid=errid)
            ret.append(rv)

            if errid != 0:
                continue

            position = new_order['position'] # Position type (头寸类型)
            order_type = new_order.get('order_type', OrderType.MARKET) # Order type (订单类型)
            size = new_order['size'] # Order size (订单大小)
            price = new_order['price'] # Order price (订单价格)
            slippage = new_order.get('slippage', 10) # Slippage (滑点)
            stop_loss = new_order.get('stop_loss', None) # Stop loss price (止损价格)
            take_profit = new_order.get('take_profit', None) # Take profit price (止盈价格)
            tags = new_order.get('tags', None) # Tags for the order (订单标签)

            if position == PositionType.LONG:
                errid, result = Buy(size, type=order_type, price=price, slippage=slippage, stop_loss=stop_loss, take_profit=take_profit,
                                    tags=tags) # Place a buy order (下买单)
                print(f"Buy: {errid}, {result}")
            elif position == PositionType.SHORT:
                errid, result = Sell(size, type=order_type, price=price, slippage=slippage, stop_loss=stop_loss, take_profit=take_profit,
                                     tags=tags) # Place a sell order (下卖单)
                print(f"Sell: {errid}, {result}")
            else:
                rv['errid'] = -3 # Invalid position type (无效的头寸类型)
                continue

            rv['errid'] = errid # Update error ID (更新错误ID)
            rv['result'] = result # Store order result (存储订单结果)

        return 0, ret

    def process_order(self, order):
        """
        Processes a single open order based on the 'order_processes' configuration.
        This allows for managing existing orders (e.g., adjusting stop loss, take profit).

        根据 'order_processes' 配置处理单个未平仓订单。
        这允许管理现有订单（例如，调整止损、止盈）。

        Args:
            order (dict): A dictionary containing the details of the open order.
                          包含未平仓订单详细信息的字典。

        Returns:
            bool: True if any of the configured order processing functions handled the order,
                  False otherwise (meaning no specific action was taken for this order).
                  如果任何配置的订单处理函数处理了该订单，则返回 True，
                  否则返回 False（表示该订单未采取任何特定操作）。
        """
        process_name = 'order_processes' # Name of the process (流程名称)
        operation_list = self.options[process_name] # List of operations for order processing (订单处理操作列表)

        for operation in operation_list:
            func = operation.get('func', self.default_process[process_name].get(operation['name'], {'func': None})['func'])
            if func is None:
                print(f"Func {operation['name']} is None!") # Log if function is not found (如果未找到函数则记录)
                return False
            if func(order, operation): # Execute function for the order (为订单执行函数)
                return True # Order was handled (订单已处理)
        return False # Order was not handled (订单未处理)

    def process_orders(self, params):
        """
        Retrieves all currently open orders from the trading platform and processes each one
        using the 'process_order' method.

        从交易平台检索所有当前未平仓订单，并使用 'process_order' 方法处理每个订单。

        Args:
            params (dict): A dictionary of parameters that can be passed to the function
                           (currently not used in this basic framework).
                           可以传递给函数的参数字典（当前在此基本框架中未使用）。
        """
        order_dict = GetOpenedOrderUIDs() # Get all open order UIDs (获取所有未平仓订单UID)
        for order_uid in order_dict:
            order = GetOrder(order_uid) # Get details for each order (获取每个订单的详细信息)
            if order is not None:
                self.process_order(order) # Process the individual order (处理单个订单)
            else:
                print(f"ERROR: {order_uid} is None") # Log if order details are not found (如果未找到订单详细信息则记录)

    def init_data(self, *args, **kwargs):
        """
        Placeholder for initializing any necessary data (e.g., loading historical data,
        setting up indicator parameters) before the strategy starts running.

        用于在策略开始运行之前初始化任何必要数据（例如，加载历史数据、
        设置指标参数）的占位符。

        Args:
            *args: Variable length argument list for potential future parameters.
                   用于未来潜在参数的可变长度参数列表。
            **kwargs: Arbitrary keyword arguments for potential future parameters.
                      用于未来潜在参数的任意关键字参数。

        Returns:
            bool: True if the data initialization is successful, False otherwise.
                  如果数据初始化成功，则返回 True，否则返回 False。
        """
        return True # Data initialization is always successful in this mock (在此模拟中数据初始化始终成功)

    def run(self):
        """
        The main execution loop of the Forex MACrossover strategy. This method orchestrates
        the different processing stages defined in the 'options'.

        Forex MACrossover 策略的主执行循环。此方法协调
        'options' 中定义的各种处理阶段。

        Returns:
            int: An error code indicating the success or failure of the strategy run.
                 0: Success (成功)
                -1: Error during initialization (初始化错误)
                -2: Error: a specified function in 'options' is None (错误：'options' 中指定的函数为 None)
        """
        if not self.init_data(): # Initialize data (初始化数据)
            print(f"init_data error, exit ...!") # Log error (记录错误)
            return -1

        process_name = 'run_processes' # Name of the main process (主流程名称)
        operation_list = self.options.get(process_name, [dict(name='process_orders'), dict(name='open_orders'), ]) # Get list of operations (获取操作列表)

        for operation in operation_list:
            func = operation.get('func', self.default_process[process_name].get(operation['name'], {'func': None})['func'])
            if func is None:
                print(f"Func {operation['name']} is None!") # Log if function is not found (如果未找到函数则记录)
                return -2
            func(operation) # Execute the function (执行函数)

        return 0 # Strategy ran successfully (策略成功运行)

# --------------
# main
# --------------
# This block is executed when the script is run directly. (当脚本直接运行时，此块代码被执行。)
strategy = ForexMACrossover() # Create an instance of the strategy (创建策略实例)
strategy.run() # Run the strategy (运行策略)
