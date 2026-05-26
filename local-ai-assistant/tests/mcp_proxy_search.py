
import sys
import os
from pathlib import Path

# Додаємо шлях до MCP, щоб імпортувати інструменти
sys.path.append(r"E:\projects\MCP")
import requests
import urllib.parse

def search_reddit(query, limit=5):
    try:
        url = f"https://www.reddit.com/search.json?q={urllib.parse.quote(query)}&limit={limit}&sort=relevance"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        results = []
        for post in data.get('data', {}).get('children', []):
            post_data = post.get('data', {})
            results.append(f"REDDIT: {post_data.get('title')} (r/{post_data.get('subreddit')})\nURL: https://reddit.com{post_data.get('permalink')}")
        return results
    except: return ["Reddit search failed"]

def search_github(query, limit=5):
    try:
        url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(query)}&sort=stars&per_page={limit}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        results = []
        for repo in data.get('items', []):
            results.append(f"GITHUB: {repo.get('full_name')} - {repo.get('description')}\nURL: {repo.get('html_url')}")
        return results
    except: return ["GitHub search failed"]

query = "Ollama models 6B-10B 2026 Qwen 3.5 9B Granite 4.1 8B Falcon 3 10B benchmarks Reddit GitHub"
print(f"--- RUNNING ENHANCED SEARCH FOR: {query} ---")

print("\n--- REDDIT FINDINGS ---")
for r in search_reddit(query): print(f"{r}\n")

print("\n--- GITHUB FINDINGS ---")
for g in search_github(query): print(f"{g}\n")
