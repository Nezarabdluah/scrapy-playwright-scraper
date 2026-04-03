import urllib.request
import re

url = 'https://your-uni.com/'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    html = urllib.request.urlopen(req).read().decode('utf-8')
    links = re.findall(r'href=[\'\"](https://your-uni.com/[^\'\"]+)[\'\"]', html)
    for link in set(links):
        if 'جامع' in urllib.parse.unquote(link) or 'تخصص' in urllib.parse.unquote(link):
            print(urllib.parse.unquote(link))
except Exception as e:
    print(f"Error: {e}")
