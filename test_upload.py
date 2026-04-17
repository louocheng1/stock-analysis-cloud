import requests
import json
from datetime import datetime

# Use the keys from index.html
SUPABASE_URL = 'https://gmcgfvgkkwefhtjmvawj.supabase.co'
SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdtY2dmdmdra3dlZmh0am12YXdqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYzMjI5NzUsImV4cCI6MjA5MTg5ODk3NX0.cu0qrV9cz2lPSt1Lp6j59JroqLUSVYt-zg9tzpxDshM'

def test_upload_via_requests():
    print(f"Testing upload to {SUPABASE_URL} via REST API...")
    
    date_str = datetime.now().strftime('%Y-%m-%d')
    results = [
        {
            "symbol": "2330",
            "name": "台積電",
            "industry": "半導體",
            "breakout_date": "2026-04-10",
            "breakout_price": 800.0,
            "pullback_date": "2026-04-15",
            "pullback_price": 810.0,
            "ma5": 805.0,
            "peg": 0.6,
            "vol_ma5_lots": 1000,
            "vol_ma20_lots": 800,
            "avg_vol_6m_lots": 900
        }
    ]
    
    data = {
        "scan_date": date_str,
        "results": results,
        "signal_count": len(results)
    }
    
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }
    
    url = f"{SUPABASE_URL}/rest/v1/stock_scan_results"
    
    try:
        # Note: REST API doesn't support easy delete or upsert without service role usually,
        # but let's try a POST with Prefer: resolution=merge-duplicates if supported or just POST.
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        if response.status_code in [200, 201]:
            print("Success! Data uploaded.")
        else:
            print("Failed to upload data. Probably RLS policy prevents Anon writes.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_upload_via_requests()
