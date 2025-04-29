from bs4 import BeautifulSoup
import json


def get_token(html):
    soup = BeautifulSoup(html, 'html.parser')
    script = soup.find('script', text=lambda t: t and 'window.CHRONOGOLF_CONFIG' in t)
    if not script:
        return None
    json_str = script.string.split('=', 1)[1].strip()
    config = json.loads(json_str)
    return config.get('CSRF_TOKEN')
