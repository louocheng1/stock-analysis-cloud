import yfinance as yf
import pandas as pd
import twstock
from datetime import datetime, timedelta
import os
import requests
import warnings
import json
import traceback
import sys
# 忽略警告
warnings.filterwarnings('ignore')
# 常數設定
MIN_AVG_VOLUME_LOTS = 200
MIN_AVG_VOLUME_SHARES = MIN_AVG_VOLUME_LOTS * 1000
# 傳產黑名單
TRADITIONAL_INDUSTRIES = {
    '水泥工業', '食品工業', '塑膠工業', '紡織纖維', '玻璃陶瓷',
    '造紙工業', '鋼鐵工業', '橡膠工業', '汽車工業', '建材營造業',
    '航運業', '觀光餐旅', '貿易百貨業', '油電燃氣業', '其他業',
    '化學工業', '電機機械', '電器電纜', '居家生活', '運動休閒',
    '農業科技業'
}
class CloudStockScanner:
    def __init__(self):
        # 雲端環境變數
        self.supabase_url = (os.environ.get("SUPABASE_URL") or "").strip()
        self.supabase_key = (os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY") or "").strip()
        self.tg_token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
        self.tg_chat_id = (os.environ.get("TELEGRAM_CHAT_ID") or "").strip()
        # 輸出診斷資訊
        print(f"\n[Diagnostic] System Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[Diagnostic] Python Version: {sys.version}")
        print(f"[Diagnostic] Pandas Version: {pd.__version__}")
        print(f"[Diagnostic] YFinance Version: {yf.__version__}")
        
        config_status = {
            "SUPABASE_URL": "✅ 已配置" if self.supabase_url else "❌ 未配置",
            "SUPABASE_KEY": "✅ 已配置" if self.supabase_key else "❌ 未配置",
            "TG_TOKEN": "✅ 已配置" if self.tg_token else "❌ 未配置",
            "TG_CHAT_ID": "✅ 已配置" if self.tg_chat_id else "❌ 未配置"
        }
        for k, v in config_status.items():
            print(f"{k:25}: {v}")
    def check_peg_ratio(self, symbol_full):
        try:
            ticker = yf.Ticker(symbol_full)
            info = ticker.info
            pe = info.get('trailingPE')
            growth = info.get('earningsGrowth')
            
            if pe is None or growth is None or growth <= 0:
                return False, None
            
            peg = pe / (growth * 100)
            return (peg < 0.75), round(peg, 2)
        except Exception as e:
            return False, None
    def get_taiwan_stock_codes(self):
        try:
            codes = twstock.codes
            tse_otc_codes = []
            for code, info in codes.items():
                if info.market in ['上市', '上櫃'] and len(code) == 4 and code.isdigit():
                    if info.group in TRADITIONAL_INDUSTRIES:
                        continue
                    suffix = ".TW" if info.market == '上市' else ".TWO"
                    tse_otc_codes.append((f"{code}{suffix}", info.name, info.group))
            print(f"[Info] Found {len(tse_otc_codes)} candidate stocks after filtering.")
            return tse_otc_codes
        except Exception as e:
            print(f"[Critical] Failed to load stock codes: {e}")
            raise e
    def process_stock_data(self, df, symbol, name, group_name=""):
        try:
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            if df is None or df.empty: return None
            if not all(col in df.columns for col in required_cols): return None
            
            df = df[required_cols].copy()
            df.dropna(subset=['Close', 'Volume'], inplace=True)
            cutoff_date = (datetime.now() - timedelta(days=180)).date()
            if len(df[df.index.date >= cutoff_date]) < 20: return None
            
            recent_data = df[df.index.date >= cutoff_date]
            avg_volume = recent_data['Volume'].mean()
            if pd.isna(avg_volume) or avg_volume < MIN_AVG_VOLUME_SHARES: return None
            df['Prev_Close'] = df['Close'].shift(1)
            df['Price_Change'] = (df['Close'] - df['Prev_Close']) / df['Prev_Close']
            df['High_30_Prev'] = df['High'].shift(1).rolling(window=30).max()
            df['MA5'] = df['Close'].rolling(window=5).mean()
            df['Vol_MA5'] = df['Volume'].rolling(window=5).mean()
            df['Vol_MA20'] = df['Volume'].rolling(window=20).mean()
            df.dropna(subset=['MA5', 'High_30_Prev', 'Price_Change', 'Vol_MA5', 'Vol_MA20'], inplace=True)
            
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
                            is_low_peg, peg_val = self.check_peg_ratio(symbol)
                            if is_low_peg:
                                results.append({
                                    'symbol': symbol.split('.')[0],
                                    'name': name,
                                    'industry': group_name,
                                    'breakout_date': dt.strftime('%Y-%m-%d'),
                                    'breakout_price': round(float(row['Close']), 2),
                                    'pullback_date': p_dt.strftime('%Y-%m-%d'),
                                    'pullback_price': round(float(p_row['Close']), 2),
                                    'ma5': round(float(p_row['MA5']), 2),
                                    'peg': peg_val,
                                    'vol_ma5_lots': round(float(p_row['Vol_MA5']) / 1000, 1),
                                    'vol_ma20_lots': round(float(p_row['Vol_MA20']) / 1000, 1),
                                    'avg_vol_6m_lots': round(float(avg_volume) / 1000, 1)
                                })
                                break
            return results
        except Exception as e:
            return None
    def send_telegram_notification(self, results):
        if not self.tg_token or not self.tg_chat_id:
            print("[Info] Telegram credentials missing, skipping notification.")
            return
            
        date_str = datetime.now().strftime('%Y-%m-%d')
        msg = f"📊 <b>雲端台股掃描總結 ({date_str})</b>\n\n"
        if not results:
            msg += "本日未發現符合教學策略之標的。"
        else:
            msg += f"🔥 <b>共發現 {len(results)} 檔潛力標的：</b>\n"
            for idx, res in enumerate(results[:10]):
                msg += f"\n{idx+1}. <b>{res['name']} ({res['symbol']})</b>\n"
                msg += f"   🚀 突破日: {res['breakout_date']}\n"
                msg += f"   📉 拉回日: {res['pullback_date']}\n"
                msg += f"   📊 估值 PEG: {res.get('peg', '--')}\n"
            if len(results) > 10:
                msg += f"\n... 以及其他 {len(results)-10} 檔。"
        
        url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
        try:
            resp = requests.post(url, json={"chat_id": self.tg_chat_id, "text": msg, "parse_mode": "HTML"}, timeout=15)
            print(f"[Info] Telegram Status: {resp.status_code}")
        except Exception as e:
            print(f"[Error] Failed to send TG: {e}")
    def upload_to_supabase(self, results):
        if not self.supabase_url or not self.supabase_key:
            return
            
        try:
            date_str = datetime.now().strftime('%Y-%m-%d')
            headers = {
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}",
                "Content-Type": "application/json"
            }
            
            # 刪除舊紀錄
            del_url = f"{self.supabase_url}/rest/v1/stock_scan_results?scan_date=eq.{date_str}"
            requests.delete(del_url, headers=headers, timeout=15)
            
            # 插入新紀錄
            post_url = f"{self.supabase_url}/rest/v1/stock_scan_results"
            payload = {
                "scan_date": date_str,
                "results": results,
                "signal_count": len(results)
            }
            
            resp = requests.post(post_url, headers=headers, data=json.dumps(payload), timeout=15)
            if resp.status_code in [200, 201, 204]:
                print(f"✅ Supabase Upload Success! ({len(results)} items)")
            else:
                print(f"❌ Supabase Upload Failed: {resp.status_code} - {resp.text}")
                
        except Exception as e:
            print(f"[Error] Supabase Error: {e}")
    def run(self):
        try:
            print(f"\n[Start] Launching scanner batch mode...")
            stocks = self.get_taiwan_stock_codes()
            all_matches = []
            batch_size = 50
            
            num_batches = (len(stocks) + batch_size - 1) // batch_size
            
            for i in range(0, len(stocks), batch_size):
                batch_idx = i // batch_size + 1
                batch = stocks[i:i+batch_size]
                symbols = [s[0] for s in batch]
                
                print(f"[Batch {batch_idx}/{num_batches}] Downloading {len(symbols)} symbols...")
                
                try:
                    df_all = yf.download(symbols, period="1y", interval="1d", progress=False, group_by='ticker')
                    
                    if df_all is None or df_all.empty:
                        continue
                        
                    for s_code, s_name, s_group in batch:
                        try:
                            if isinstance(df_all.columns, pd.MultiIndex):
                                if s_code in df_all.columns.levels[0]:
                                    df_stock = df_all[s_code]
                                else:
                                    continue
                            else:
                                df_stock = df_all
                                
                            res = self.process_stock_data(df_stock, s_code, s_name, s_group)
                            if res: 
                                all_matches.extend(res)
                        except:
                            continue
                            
                except Exception as batch_e:
                    print(f"  [Error] Batch {batch_idx} failed: {batch_e}")
                    continue
            
            all_matches.sort(key=lambda x: x['pullback_date'], reverse=True)
            self.upload_to_supabase(all_matches)
            self.send_telegram_notification(all_matches)
            print(f"\n[Finish] Completed successfully. Total Matches: {len(all_matches)}")
            
        except Exception as e:
            print("\n[CRITICAL ERROR] Scanner crashed!")
            traceback.print_exc()
            sys.exit(1)
if __name__ == "__main__":
    scanner = CloudStockScanner()
    scanner.run()
