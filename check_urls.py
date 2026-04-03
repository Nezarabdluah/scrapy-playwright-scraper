import urllib.request
import urllib.parse
urls = [
    'https://your-uni.com/course-list/',
    'https://your-uni.com/courses/',
    'https://your-uni.com/التخصصات-الجامعية/'
]
for u in urls:
    try:
        req = urllib.request.Request(urllib.parse.quote(u, safe=':/'), headers={'User-Agent': 'Mozilla/5.0'})
        res = urllib.request.urlopen(req)
        print(f'{u} : {res.status}')
    except urllib.error.HTTPError as e:
        print(f'{u} : HTTP Error {e.code}')
    except Exception as e:
        print(f'{u} : Error {e}')
