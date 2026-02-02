from bs4 import BeautifulSoup
import json
import os

def analyze_html():
    file_path = "debug_page.html"
    if not os.path.exists(file_path):
        print("debug_page.html not found.")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')

    print(f"--- Analyzing {file_path} ---")
    
    # 1. Look for scripts with specific IDs or types
    scripts = soup.find_all('script')
    print(f"\nFound {len(scripts)} scripts.")
    for i, s in enumerate(scripts):
        s_id = s.get('id', 'No ID')
        s_type = s.get('type', 'No Type')
        content_snippet = s.string[:50] if s.string else "No content"
        print(f"Script {i}: ID={s_id}, Type={s_type}, ContentStart={content_snippet}")
        
    # 2. Look for JSON data islands
    print("\n--- JSON Data Islands ---")
    for s in scripts:
        if s.get('type') == 'application/json' or (s.string and '{"' in s.string[:20]):
            print(f"Found potential JSON script (ID={s.get('id')})")
            try:
                data = json.loads(s.string)
                print("  Valid JSON parse!")
                keys = list(data.keys()) if isinstance(data, dict) else "List"
                print(f"  Keys: {keys}")
                # Check for nested pins
                str_data = str(data)
                if "736x" in str_data or "orig" in str_data:
                    print("  -> Contains image keys (736x, orig)!")
            except:
                pass

    # 3. Look for img tags
    imgs = soup.find_all('img')
    print(f"\nFound {len(imgs)} img tags.")
    for img in imgs[:10]:
        print(f"Img: src={img.get('src')}, srcset={img.get('srcset')}")

if __name__ == "__main__":
    analyze_html()
