
from duckduckgo_search import DDGS
import json

def run_search(query):
    print(f"Searching DuckDuckGo for: {query}")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=10))
            for i, r in enumerate(results, 1):
                print(f"\n{i}. {r['title']}")
                print(f"   URL: {r['href']}")
                print(f"   {r['body'][:200]}...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_search("best Ollama models 6B 7B 8B 9B 10B ranking 2026 benchmarks")
    print("\n" + "="*50 + "\n")
    run_search("Qwen 3.5 9B vs Granite 4.1 8B vs Llama 3.1 8B vs Falcon 3 10B performance reddit")
