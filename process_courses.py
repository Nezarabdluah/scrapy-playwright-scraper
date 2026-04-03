import csv
import pathlib

def clean_courses(input_path: str, output_path: str):
    print(f"Loading data from {input_path}...")
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            if not fieldnames:
                print("CSV is empty or invalid.")
                return
            rows = list(reader)
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return

    print("Processing price string...")
    
    # We want to replace 'title' with 'course_name' and 'description' with 'university_name'
    # And add 'fee', 'duration', 'intakes' instead of 'price'
    
    new_fieldnames = []
    for f in fieldnames:
        if f == 'title':
            new_fieldnames.append('course_name')
        elif f == 'description':
            new_fieldnames.append('university_name')
        elif f == 'price':
            continue
        else:
            new_fieldnames.append(f)
            
    new_fieldnames.extend(['fee', 'duration', 'intakes'])

    cleaned_rows = []
    for row in rows:
        new_row = {}
        
        # Copy and rename fields
        for k, v in row.items():
            if k == 'title':
                new_row['course_name'] = v
            elif k == 'description':
                new_row['university_name'] = v
            elif k == 'price':
                continue
            else:
                new_row[k] = v

        price_str = row.get('price', '')
        fee_part = ""
        duration_part = ""
        intake_part = ""

        if price_str:
            parts = [p.strip() for p in price_str.split('•')]
            for part in parts:
                p_lower = part.lower()
                if 'intake' in p_lower:
                    intake_part = part
                elif 'year' in p_lower and ('myr' in p_lower or 'usd' in p_lower or '/' in p_lower or any(c.isdigit() for c in p_lower)):
                    if 'myr' in p_lower or 'usd' in p_lower or 'rm' in p_lower:
                        fee_part = part
                    else:
                        duration_part = part
                elif 'month' in p_lower or 'week' in p_lower:
                    duration_part = part
                elif 'myr' in p_lower or 'usd' in p_lower:
                    fee_part = part
                
        new_row['fee'] = fee_part
        new_row['duration'] = duration_part
        new_row['intakes'] = intake_part
        
        cleaned_rows.append(new_row)

    # Save the cleaned data
    out_dir = pathlib.Path(output_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=new_fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_rows)
        
    print(f"Cleaned data saved to {output_path} with {len(cleaned_rows)} rows.")

if __name__ == "__main__":
    input_file = "e:/جلب بيانات/scraper_project/data/your_uni/specialties_en/courses.csv"
    output_file = "e:/جلب بيانات/scraper_project/data/your_uni/specialties_en/courses_cleaned.csv"
    clean_courses(input_file, output_file)
