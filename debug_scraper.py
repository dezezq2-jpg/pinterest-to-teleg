import requests
import config

def save_debug_html():
    url = config.PINTEREST_SEARCH_URL
    
    user_agents = [
        ("Mobile", "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36"),
        ("Desktop", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"),
        ("Googlebot", "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"),
    ]

    for name, ua in user_agents:
        print(f"\n--- Testing UA: {name} ---")
        headers = {
            'User-Agent': ua,
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/'
        }
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            content = response.text
            
            # Check for images
            if ".jpg" in content or "pinimg.com" in content:
                print(f"SUCCESS! Found images with {name} UA.")
                with open("debug_page.html", "w", encoding="utf-8") as f:
                    f.write(content)
                print("Saved to debug_page.html")
                return
            else:
                print(f"FAILED. No images found in response with {name} UA.")
                
        except Exception as e:
            print(f"Error with {name}: {e}")

    print("\nAll attempts failed to find images directly in HTML.")


if __name__ == "__main__":
    save_debug_html()
