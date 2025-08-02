import pandas as pd
import pandas_ta as ta
import numpy as np

CONFIG = {
    'csv_filepath': 'D:\Blockchain\Grace\BTC1H.csv', 
    'initial_balance': 5,              
    'fee_percent': 0.1,                
    "ma_fast_period": 4,
    "ma_slow_period": 9,
    "atr_period": 9,
    "use_trailing_stop": True,
    "trailing_stop_atr_multiplier": 2,
}

def calculate_indicators(df):
    """Menghitung semua indikator teknikal."""
    df.ta.ema(length=CONFIG['ma_fast_period'], append=True, col_names=('MA_fast',))
    df.ta.ema(length=CONFIG['ma_slow_period'], append=True, col_names=('MA_slow',))
    df.ta.atr(length=CONFIG['atr_period'], append=True, col_names=('ATR',))
    df.dropna(inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

def trend_following_strategy(latest_data, prev_data, current_position):
    """Strategi saat pasar trending."""
    action = "hold"
    # Sinyal Beli
    if (prev_data['MA_fast'] < prev_data['MA_slow'] and
        latest_data['MA_fast'] > latest_data['MA_slow'] and
        not current_position):
        action = 'buy'
    return action

def manage_trailing_stop(latest_price, position_data):
    """Memeriksa apakah trailing stop loss terpicu."""
    if not CONFIG['use_trailing_stop'] or not position_data['in_position']:
        return False, position_data

    position_data['highest_price_since_entry'] = max(position_data['highest_price_since_entry'], latest_price)
    new_ts_price = position_data['highest_price_since_entry'] - (position_data['latest_atr'] * CONFIG['trailing_stop_atr_multiplier'])
    
    if new_ts_price > position_data['trailing_stop_price']:
        position_data['trailing_stop_price'] = new_ts_price

    if latest_price <= position_data['trailing_stop_price']:
        return True, position_data 
    
    return False, position_data

def run_backtest(df):
    """Fungsi utama untuk menjalankan simulasi backtest."""
    print("Memulai Backtest...")
    trades = []
    position_data = {
        "in_position": False,
        "entry_price": 0,
        "entry_time": None,
        "trailing_stop_price": 0,
        "highest_price_since_entry": 0,
        "latest_atr": 0,
    }

    for i in range(1, len(df)):
        latest_data = df.iloc[i]
        prev_data = df.iloc[i-1]
        position_data['latest_atr'] = latest_data['ATR']

        if position_data['in_position']:
            hit_ts, position_data = manage_trailing_stop(latest_data['close'], position_data)
            if hit_ts:
                exit_price = position_data['trailing_stop_price'] 
                
                # Hitung PnL
                pnl = (exit_price - position_data['entry_price']) / position_data['entry_price']
                trades.append({
                    'entry_time': position_data['entry_time'],
                    'exit_time': latest_data['timestamp'],
                    'entry_price': position_data['entry_price'],
                    'exit_price': exit_price,
                    'pnl_percent': pnl,
                    'exit_reason': 'Trailing Stop'
                })
                
                # Reset posisi
                position_data['in_position'] = False
                continue # Lanjut ke candle berikutnya

        action = "hold"
        action = trend_following_strategy(latest_data, prev_data, position_data['in_position'])

        if action == "buy" and not position_data['in_position']:
            position_data['in_position'] = True
            position_data['entry_price'] = latest_data['close']
            position_data['entry_time'] = latest_data['timestamp']
            position_data['highest_price_since_entry'] = latest_data['close']
            position_data['trailing_stop_price'] = latest_data['close'] - (latest_data['ATR'] * CONFIG['trailing_stop_atr_multiplier'])
        
        elif action == 'sell' and position_data['in_position']:
            exit_price = latest_data['close']
            pnl = (exit_price - position_data['entry_price']) / position_data['entry_price']
            
            trades.append({
                'entry_time': position_data['entry_time'],
                'exit_time': latest_data['timestamp'],
                'entry_price': position_data['entry_price'],
                'exit_price': exit_price,
                'pnl_percent': pnl,
                'exit_reason': 'Signal'
            })
            
            position_data['in_position'] = False

    print("Backtest Selesai.")
    return trades

def calculate_metrics(trades):
    """Menghitung metrik performa dari hasil trade."""
    if not trades:
        print("Tidak ada trade yang dieksekusi.")
        return None

    df_trades = pd.DataFrame(trades)
    
    # Kurangi biaya transaksi dari setiap PnL
    df_trades['pnl_percent'] -= (CONFIG['fee_percent'] / 100) * 2 

    # Hitung Saldo & Drawdown
    initial_balance = CONFIG['initial_balance']
    balance_over_time = [initial_balance]
    current_balance = initial_balance
    peak_balance = initial_balance
    max_drawdown = 0

    for pnl in df_trades['pnl_percent']:
        current_balance *= (1 + pnl)
        balance_over_time.append(current_balance)
        if current_balance > peak_balance:
            peak_balance = current_balance
        
        drawdown = (peak_balance - current_balance) / peak_balance
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    # Kalkulasi Metrik Utama
    total_trades = len(df_trades)
    winning_trades = df_trades[df_trades['pnl_percent'] > 0]
    losing_trades = df_trades[df_trades['pnl_percent'] <= 0]
    
    win_rate = (len(winning_trades) / total_trades) * 100 if total_trades > 0 else 0
    
    total_gross_profit = winning_trades['pnl_percent'].sum()
    total_gross_loss = abs(losing_trades['pnl_percent'].sum())
    
    profit_factor = total_gross_profit / total_gross_loss if total_gross_loss > 0 else float('inf')
    
    max_loss = df_trades['pnl_percent'].min() * 100 if not df_trades.empty else 0
    
    avg_win = winning_trades['pnl_percent'].mean() if not winning_trades.empty else 0
    avg_loss = abs(losing_trades['pnl_percent'].mean()) if not losing_trades.empty else 0
    
    risk_reward_ratio = avg_win / avg_loss if avg_loss > 0 else float('inf')
    
    expectancy = ((win_rate/100) * avg_win) - (((100 - win_rate)/100) * avg_loss)

    metrics = {
        "Total Trades": total_trades,
        "Win Rate (%)": f"{win_rate:.2f}",
        "Profit Factor": f"{profit_factor:.2f}",
        "Maximum Drawdown (%)": f"{max_drawdown * 100:.2f}",
        "Maximum Loss per Trade (%)": f"{max_loss:.2f}",
        "Average Win (%)": f"{avg_win * 100:.2f}",
        "Average Loss (%)": f"{avg_loss * 100:.2f}",
        "Risk:Reward Ratio": f"{risk_reward_ratio:.2f}",
        "Expectancy (%)": f"{expectancy * 100:.2f}",
        "Final Balance ($)": f"{current_balance:,.2f}"
    }

    metrics2 ={
        "Total Trades": total_trades,
        "Final Balance ($)": f"{current_balance:,.2f}"

    }
    return metrics

if True:
    try:
        df_raw = pd.read_csv(CONFIG['csv_filepath'])
        df_raw['timestamp'] = pd.to_datetime(df_raw['timestamp']) 
        df_raw.columns = [col.lower() for col in df_raw.columns] 
        
    except FileNotFoundError:
        print(f"Error: File tidak ditemukan di '{CONFIG['csv_filepath']}'")
        exit()
    except Exception as e:
        print(f"Error saat membaca CSV: {e}")
        print("Pastikan nama kolom adalah: timestamp, open, high, low, close, volume")
        exit()
    

    df_processed = calculate_indicators(df_raw)
    
    list_of_trades = run_backtest(df_processed)
    
    performance_metrics = calculate_metrics(list_of_trades)
    
    if performance_metrics:
        print("\n" + "="*30)
        print("HASIL PERFORMA STRATEGI")
        print("="*30)
        for key, value in performance_metrics.items():
            print(f"{key:<28}: {value}")
        print("="*30)

