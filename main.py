import requests
from bs4 import BeautifulSoup
import creds

login_url = ('')
secure_url = ('')

payload = {
    'username' : creds.username,
    'password' : creds.password
}

with requests.session() as s:
    pass