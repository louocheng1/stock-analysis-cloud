import yfinance as yf
import pandas as pd
import twstock
from datetime import datetime, timedelta
import warnings

# 忽略警告
warnings.filterwarnings('ignore')

# 常數設定
MIN_AVG_VOLUME_LOTS = 200
MIN_AVG_VOLUME_SHARES = MIN_AVG_VOLUME_LOTS * 1000

TRADITIONAL_INDUSTRIES = {
    '水泥工業', '食品工業', '塑膠工業', '紡織纖維', '玻璃陶瓷',
    '造紙工業', '鋼鐵工業', '橡膠工業', '汽車工業', '建材營造業',
    '航運業', '觀光餐旅', '貿易百貨業', '油電燃氣業', '其他業',
    '化學工業', '電機機械', '電器電纜', '居家生活', '運動休閒',
    '農業科技業'
}

def check_peg_ratio(symbol_full):
    try:
        ticker = yf.Ticker(symbol_full)
        info = ticker.info
        pe = info.get('trailingPE')
        growth = info.get('earningsGrowth')
        if pe is None or growth is None or growth <= 0:
            return False, None
        peg = pe / (growth * 100)
        return (peg < 0.75), round(peg, 2)
    except:
        return False, None

def get_taiwan_stock_codes():
    codes = twstock.codes
    tse_otc_codes = []
    for code, info in codes.items():
        if info.market in ['上市', '上櫃'] and len(code) == 4 and code.isdigit():
            if info.group in TRADITIONAL_INDUSTRIES:
                continue
            suffix = ".TW" if info.market == '上市' else ".TWO"
            tse_otc_codes.append((f"{code}{suffix}", info.name, info.group))
    return tse_otc_codes

def process_stock_data(df, symbol, name, group_name=""):
    try:
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required_cols): return None
        df = df[required_cols].copy()
        df.dropna(subset=['Close', 'Volume'], inplace=True)
        cutoff_date = (datetime.now() - timedelta(days=180)).date()
        if len(df[df.index.date >= cutoff_date]) < 20: return None
        avg_volume = df[df.index.date >= cutoff_date]['Volume'].mean()
        if avg_volume < MIN_AVG_VOLUME_SHARES: return None
        df['Prev_Close'] = df['Close'].shift(1)
        df['Price_Change'] = (df['Close'] - df['Prev_Close']) / df['Prev_Close']
        df['High_30_Prev'] = df['High'].shift(1).rolling(window=30).max()
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df.dropna(subset=['MA5', 'High_30_Prev', 'Price_Change'], inplace=True)
        search_cutoff = (datetime.now() - timedelta(days=90)).date()
        recent_df = df[df.index.date >= search_cutoff]
        results = []
        for i in range(len(recent_df)):
            row = recent_df.iloc[i]
            dt = recent_df.index[i]
            if row['High'] >= row['High_30_Prev'] and row['Price_Change'] >= 0.098:
                idx = df.index.get_loc(dt)
                post_df = df.iloc[idx + 1 : idx + 11]
                for j in range(len(post_df)):
                    p_row = post_df.iloc[j]
                    p_dt = post_df.index[j]
                    if p_row['Low'] <= (p_row['MA5'] * 1.005) and p_row['Close'] >= p_row['MA5']:
                        is_low_peg, peg_val = check_peg_ratio(symbol)
                        if is_low_peg:
                            results.append({
                                'symbol': symbol.split('.')[0],
                                'name': name,
                                'industry': group_name,
                                'peg': peg_val
                            })
                            break
        return results
    except:
        return None

def test_scan():
    print("Testing scanning logic on a few stocks...")
    # Test TSMC (2330.TW) and Foxconn (2317.TW)
    stocks = [("2330.TW", "台積電", "半導體"), ("2317.TW", "鴻海", "其他電子")]
    for s in stocks:
        print(f"Checking {s[0]} ({s[1]})...")
        df = yf.download(s[0], period="1y", interval="1d", progress=False)
        if df.empty:
            print("  Empty data from yfinance.")
            continue
        res = process_stock_data(df, s[0], s[1], s[2])
        if res:
            print(f"  Found potential signal: {res}")
        else:
            print("  No signal found for these specific criteria today.")

if __name__ == "__main__":
    test_scan()
