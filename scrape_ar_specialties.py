from playwright.sync_api import sync_playwright
import json
import csv
import pathlib
import time

def scrape_arabic_specialties():
    links_file = 'e:/جلب بيانات/scraper_project/menu_links.json'
    output_file = 'e:/جلب بيانات/scraper_project/data/your_uni/specialties_ar/specialties.csv'
    
    with open(links_file, 'r', encoding='utf-8') as f:
        all_links = json.load(f)
        
    specialties = []
    for item in all_links:
        name, url = item.split(': ', 1)
        name = name.strip()
        url = url.strip()
        if 'جامع' not in name and 'معهد' not in name and 'اكاديمي' not in name and 'الرئيسية' not in name:
            specialties.append({'name': name, 'url': url})
            
    print(f"Found {len(specialties)} specialties to scrape.")
    
    results = []
    out_dir = pathlib.Path(output_file).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,  # VERY IMPORTANT: False disables basic bot detection
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        page = context.new_page()
        
        for idx, spec in enumerate(specialties):
            print(f"[{idx+1}/{len(specialties)}] Scraping {spec['name']}...")
            try:
                page.goto(spec['url'], timeout=60000, wait_until="domcontentloaded")
                
                # Wait for potential Cloudflare challenge to pass
                page.wait_for_timeout(3000)
                
                title_elem = page.locator("h1").first
                title = title_elem.inner_text() if title_elem.count() > 0 else spec['name']
                
                page_title = page.title()
                if "403" in page_title or "Forbidden" in page_title or "Just a moment" in page_title:
                    print("  ...Cloudflare Challenge Detected! Waiting 15s...")
                    page.wait_for_timeout(15000)
                    title_elem = page.locator("h1").first
                    title = title_elem.inner_text() if title_elem.count() > 0 else spec['name']
                    
                if "403" in title or "Forbidden" in title:
                    raise Exception("Still Blocked by Cloudflare")
                    
                paragraphs = page.locator('.entry-content p, .elementor-text-editor p').all_inner_texts()
                
                content_parts = []
                for p_text in paragraphs:
                    p_clean = p_text.strip()
                    if p_clean and len(p_clean) > 20:
                        content_parts.append(p_clean)
                        
                description = " ".join(content_parts)
                if len(description) > 1000:
                    description = description[:997] + "..."
                    
                results.append({
                    'title': title.strip() if title else spec['name'],
                    'url': spec['url'],
                    'description': description
                })
                print(" -> Success!")
                
            except Exception as e:
                print(f" -> Failed to scrape {spec['url']}: {e}")
                
        browser.close()
        
    if results:
        with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
            # Adding 'sep=,' allows ALL versions of Excel to parse columns correctly
            f.write("sep=,\n")
            writer = csv.DictWriter(f, fieldnames=['title', 'url', 'description'])
            writer.writeheader()
            writer.writerows(results)
        print(f"\nData saved to {output_file} with {len(results)} rows.")
    else:
        print("\nNo data extracted!")

if __name__ == '__main__':
    scrape_arabic_specialties()
