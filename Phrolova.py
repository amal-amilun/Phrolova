import ccxt
import pandas as pd
import pandas_ta as ta
import time
from dotenv import load_dotenv
import os
load_dotenv()

CONFIG = {
    "exchange": "binance",
    "api_key": os.getenv("LIVE_API_KEY"),
    "api_secret":os.getenv("LIVE_SECRET_KEY"),
    "symbol": "BTC/USDT",
    "timeframe": "1h",

    # Pengaturan Indikator
    "ma_fast_period": 4,
    "ma_slow_period": 9,
    "atr_period": 9,

    # Pengaturan Manajemen Risiko
    "use_trailing_stop": True,
    "trailing_stop_atr_multiplier": 2,
}

# Fungsi-Fungsi Utama Bot
def connect_to_exchange():
    """Menghubungkan ke bursa menggunakan CCXT"""
    print(f"Menghubungkan ke {CONFIG['exchange']}")
    try:
        exchange = getattr(ccxt, CONFIG['exchange'])({
            'apiKey': CONFIG['api_key'],
            'secret': CONFIG['api_secret'],
            'enableRateLimit': True,
        })
        exchange.set_sandbox_mode(False)
        print("Berhasil terhubung ke bursa.")
        return exchange
    except Exception as e:
        print(f"Gagal terhubung ke bursa: {e}")
        return None
    
def calculate_indicators(df):
    """Menghitung semua indikator"""
    df.ta.ema(length=CONFIG['ma_fast_period'], append=True, col_names=('MA_fast',))
    df.ta.ema(length=CONFIG['ma_slow_period'], append=True, col_names=('MA_slow',))
    df.ta.atr(length=CONFIG['atr_period'], append=True, col_names=('ATR',))

    df.dropna(inplace=True)
    return df

def trend_following_strategy(df, current_position):
    """Trending Strategy"""
    latest_data = df.iloc[-1]
    prev_data = df.iloc[-2]
    action = "hold"

    # Beli -> kalo MA_fast motong MA_slow
    if(prev_data['MA_fast'] < prev_data['MA_slow'] and
        latest_data['MA_fast'] > latest_data['MA_slow'] and
       not current_position):
        action = 'buy'
        print("Sinyal Trend Following: Buy")

    return action

def manage_trailing_stop(latest_price, position_data):
    """Fungsi untuk panggil trailing stop setiap candle"""
    if not CONFIG['use_trailing_stop'] or not position_data['in_position']:
        return False
    
    current_trailing_stop_price = latest_price - (position_data['latest_atr'] * CONFIG['trailing_stop_atr_multiplier'])

    # Update trailing stop
    if current_trailing_stop_price > position_data['trailing_stop_price']:
        position_data['trailing_stop_price'] = current_trailing_stop_price
        print(f"Trailing stop diupdate ke: {current_trailing_stop_price:.2f}")
        
    # Kalau hit trailing stop
    if latest_price <= position_data['trailing_stop_price']:
        print(f"Trailing Stop Hit jual di harga {latest_price:.2f}")
        return True
    
    return False

def main_loop():
    exchange = connect_to_exchange()
    if not exchange:
        return
    
    # Status trading sekarang
    position_data = {
        "in_position": False,
        "entry_price": 0,
        "trailing_stop_price": 0,
        "latest_atr": 0,
    }

    while True:
        try:
            print("\n"+"="*30)
            print(f"Candle baru untuk {CONFIG['symbol']} pada time frame {CONFIG['timeframe']}")

            balances = exchange.fetch_balance()['free']
            print(f"Saldo tersedia: BTC={balances.get('BTC', 0)}, USDT={balances.get('USDT', 0):.2f}")
            
            # Ambil data OHLCV
            ohlcv = exchange.fetch_ohlcv(CONFIG['symbol'], CONFIG['timeframe'], limit=200)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

            # Hitung semua indikator
            df = calculate_indicators(df)
            latest_data = df.iloc[-1]
            position_data['latest_atr'] = latest_data['ATR']

            # Cek Trailing Stop
            if position_data['in_position']:
                if manage_trailing_stop(latest_data['close'], position_data):
                    btc_balance = balances.get('BTC', 0)
                    if btc_balance > 0:
                        print(f"Menjual seluruh {btc_balance} BTC..")
                        position_data['in_position'] = False
                        exchange.create_market_sell_order(CONFIG['symbol'], btc_balance)
                        time.sleep(exchange.rateLimit / 1000)
                    continue
            
            action = "hold"
            action = trend_following_strategy(df, position_data['in_position'])

            # Eksekusi
            if action == "buy":
                usdt_balance = balances.get("USDT", 0)
                if usdt_balance > 10:
                    print(f"Membeli BTC dengan seluruh {usdt_balance} USDT..")
                    params = {'quoteOrderQty': usdt_balance}
                    exchange.create_market_buy_order(CONFIG['symbol'], None, params)
                    position_data['in_position'] = True
                    position_data['entry_price'] = latest_data['close']
                    position_data['trailing_stop_price'] = latest_data['close'] - (latest_data['close'] * CONFIG['trailing_stop_atr_multiplier'])
            
            else:
                print("Aksi: Hold")

            print("Siklus selesai. Menunggu candle berikutnya..")
            time.sleep(3600)

        except ccxt.NetworkError as e:
            print(f"Error Jaringan: {e}. Mencoba lagi dalam 60 detik..")
            time.sleep(60)
        except Exception as e:
            print(f"Error tak terduga: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main_loop()
