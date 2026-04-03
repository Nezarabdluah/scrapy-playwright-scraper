import urllib.request
import re
from urllib.parse import unquote
import json

url = 'https://your-uni.com/'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    html = urllib.request.urlopen(req).read().decode('utf-8')
    # extract menu links
    main_menu = re.findall(r'<ul[^>]*id=[\'\"]menu-[^\'\"]+[\'\"]', html)
    menus = re.findall(r'<ul[^>]*>(.*?)</ul>', html, re.DOTALL)
    links_found = set()
    for menu in menus:
        links = re.findall(r'href=[\'\"]([^\'\"]+)[\'\"][^>]*>([^<]+)</a>', menu)
        for link, text in links:
            t = text.strip()
            if t and link.startswith('https://your-uni.com/'):
                links_found.add(f"{t}: {unquote(link)}")
    
    with open('menu_links.json', 'w', encoding='utf-8') as f:
        json.dump(list(links_found), f, ensure_ascii=False, indent=4)
    print("Menu links written to menu_links.json")
except Exception as e:
    print(f'Error: {e}')
