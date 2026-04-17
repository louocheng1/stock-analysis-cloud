import requests
import json

url = "https://gmcgfvgkkwefhtjmvawj.supabase.co/rest/v1/stock_scan_results?select=*&order=scan_date.desc&limit=1"
headers = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdtY2dmdmdra3dlZmh0am12YXdqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYzMjI5NzUsImV4cCI6MjA5MTg5ODk3NX0.cu0qrV9cz2lPSt1Lp6j59JroqLUSVYt-zg9tzpxDshM",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdtY2dmdmdra3dlZmh0am12YXdqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYzMjI5NzUsImV4cCI6MjA5MTg5ODk3NX0.cu0qrV9cz2lPSt1Lp6j59JroqLUSVYt-zg9tzpxDshM"
}

try:
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text}")
except Exception as e:
    print(f"Error: {e}")
