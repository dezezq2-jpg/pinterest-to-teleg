import requests
from bs4 import BeautifulSoup
import json
import logging
import random
import re

logger = logging.getLogger(__name__)

def get_pinterest_images(url):
    """
    Scrapes high-quality images from a Pinterest search URL.
    Uses Mobile User-Agent to ensure better data availability.
    Filters out promoted pins (ads).
    Returns a list of dicts: {'id': pin_id, 'url': image_url, 'is_promoted': bool}
    """
    # Mobile User-Agent is key to getting SSR content
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        valid_media = []
        
        # --- STRATEGY 1: JSON Parsing (Preferred for High Res) ---
        try:
            # Look for __PWS_DATA__ or __PWS_INITIAL_PROPS__
            data_scripts = soup.find_all('script', id=re.compile(r'__PWS_(DATA|INITIAL_PROPS)__'))
            
            for script in data_scripts:
                try:
                    data = json.loads(script.string)
                    valid_media.extend(extract_from_json(data))
                except Exception as e:
                    logger.warning(f"Failed to parse JSON from {script.get('id')}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in JSON strategy: {e}")

        # --- STRATEGY 2: HTML Image Tags (Fallback) ---
        if not valid_media:
            logger.info("JSON strategy yielded no results. Trying HTML fallback...")
            valid_media.extend(extract_from_html(soup))

        # Remove duplicates based on ID or URL
        unique_media = {}
        for item in valid_media:
            # Use URL as key if ID is missing or generic
            key = item.get('id') or item.get('url')
            if key and key not in unique_media:
                 unique_media[key] = item

        results = list(unique_media.values())
        logger.info(f"Found {len(results)} valid items total.")
        return results

    except Exception as e:
        logger.error(f"Error fetching Pinterest data: {e}")
        return []

def extract_from_json(data):
    """Recursively finds pins in JSON data."""
    found_pins = []
    
    def find_recursively(obj):
        if isinstance(obj, dict):
            if 'id' in obj and 'images' in obj:
                if isinstance(obj['images'], dict) and len(obj['images']) > 0:
                    found_pins.append(obj)
            for v in obj.values():
                find_recursively(v)
        elif isinstance(obj, list):
            for item in obj:
                find_recursively(item)
    
    find_recursively(data)
    
    valid_items = []
    for pin in found_pins:
        try:
            if pin.get('is_promoted', False):
                continue
                
            images = pin.get('images', {})
            img_url = None
            # Prefer highest resolution
            for size in ['orig', '1200x', '736x', '474x']:
                if size in images:
                    img_url = images[size]['url']
                    break
            
            if img_url:
                valid_items.append({
                    'id': pin['id'],
                    'url': img_url,
                    'description': pin.get('description', ''),
                    'is_promoted': False
                })
        except:
            continue
            
    return valid_items

def extract_from_html(soup):
    """Extracts images directly from <img> tags."""
    valid_items = []
    imgs = soup.find_all('img')
    
    for img in imgs:
        src = img.get('src')
        if not src or 'pinimg.com' not in src:
            continue
            
        # Filter out tiny icons or non-content
        if '75x75' in src or '30x30' in src:
            continue
            
        # Try to upscale the URL
        # e.g., .../236x/... -> .../736x/...
        high_res_url = src
        if '/236x/' in src:
            high_res_url = src.replace('/236x/', '/736x/')
        elif '/474x/' in src:
            high_res_url = src.replace('/474x/', '/736x/')
            
        # Generate a pseudo-ID from the filename
        # .../a4/79/c0/a479c0d03a5389ac723d7e4ae3b92104.jpg -> a479c0d03a5389ac723d7e4ae3b92104
        try:
            item_id = src.split('/')[-1].split('.')[0]
        except:
            item_id = str(random.randint(100000, 999999))
            
        valid_items.append({
            'id': item_id,
            'url': high_res_url,
            'description': img.get('alt', ''),
            'is_promoted': False # Assume HTML scrapes aren't promoted if we can't tell
        })
        
    return valid_items
