from dotenv import load_dotenv
import os

load_dotenv()

# DB Configuration
MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_PORT = int(os.getenv('MYSQL_PORT'))
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_DB = os.getenv('MYSQL_DB')

# Scraping Configuration
base_profile_path = os.path.expanduser(r'~\AppData\Local\Google\Chrome\User Data')
default_path = os.path.join(base_profile_path, 'Default')

if os.path.exists(default_path):
    PROFILE_PATH = default_path 
else:
    raise FileNotFoundError("Chrome profile folder tidak ditemukan.")

# WhatsApp
DEFAULT_NUMBER = os.getenv('DEFAULT_NUMBER')