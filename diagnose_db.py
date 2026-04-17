import requests
import json

url = "https://gmcgfvgkkwefhtjmvawj.supabase.co/rest/v1/stock_scan_results?select=*&order=created_at.desc&limit=3"
headers = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdtY2dmdmdra3dlZmh0am12YXdqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYzMjI5NzUsImV4cCI6MjA5MTg5ODk3NX0.cu0qrV9cz2lPSt1Lp6j59JroqLUSVYt-zg9tzpxDshM",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdtY2dmdmdra3dlZmh0am12YXdqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYzMjI5NzUsImV4cCI6MjA5MTg5ODk3NX0.cu0qrV9cz2lPSt1Lp6j59JroqLUSVYt-zg9tzpxDshM"
}

try:
    response = requests.get(url, headers=headers)
    data = response.json()
    print(f"Count of records found: {len(data)}")
    for record in data:
        print(f"ID: {record.get('id')}, Date: {record.get('scan_date')}, Created: {record.get('created_at')}, Signals: {record.get('signal_count')}")
except Exception as e:
    print(f"Error: {e}")
