from scrapy.selector import Selector
import re

html = open('temp_ar_inst.html', encoding='utf-8').read()
sel = Selector(text=html)

# Check what classes are highly repeated
classes = sel.css('[class]::attr(class)').getall()
from collections import Counter
counts = Counter()
for c in classes:
    for cls in c.split():
        counts[cls] += 1

print("MOST COMMON CLASSES:")
for k, v in counts.most_common(10):
    print(f"{k}: {v}")

items = sel.css('.elementor-widget-container')
print(f"Random widget text: {items[20].css('::text').getall()[:10] if len(items)>20 else 'None'}")

