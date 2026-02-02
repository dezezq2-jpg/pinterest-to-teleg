from parser import get_pinterest_images
import config

def test():
    print(f"Testing scraper on: {config.PINTEREST_SEARCH_URL}")
    items = get_pinterest_images(config.PINTEREST_SEARCH_URL)
    
    print(f"\nFound {len(items)} items total.")
    
    if items:
        print("\n--- First 5 Items ---")
        for i, item in enumerate(items[:5]):
            print(f"[{i+1}] ID: {item.get('id', 'N/A')}")
            print(f"    URL: {item.get('url', 'N/A')}")
            desc = item.get('description', '')
            print(f"    Desc: {desc[:50]}..." if desc else "    Desc: (None)")
            print("-" * 30)
    else:
        print("\nNo items found. Check parser logic.")

if __name__ == "__main__":
    test()
