# crawler.py
import requests
from bs4 import BeautifulSoup

def crawl_website(url):
    """Simple web crawler using requests and BeautifulSoup"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            
            if href.startswith('/'):
                from urllib.parse import urljoin
                href = urljoin(url, href)
            
            if href.startswith('http'):
                links.append(href)
        
        return list(set(links))
        
    except Exception as e:
        print(f"Error crawling {url}: {e}")
        return []
