import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
ADMIN_ID = os.getenv("ADMIN_ID")

# Pinterest Configuration
PINTEREST_SEARCH_URL = "https://www.pinterest.com/search/pins/?q=toned%20women%20beach%20style&rs=typed"

# Delay Configuration (in minutes)
PUBLISH_DELAY_MINUTES = 20
