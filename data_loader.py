import requests
import pdfplumber
import pandas as pd
import os
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Constants
DATA_DIR = "data"
CSV_PATH = os.path.join(DATA_DIR, "nhtsa_data.csv")

# Landing pages for each year
YEAR_URLS = {
    2020: "https://www.nhtsa.gov/document/2020-aala-listed-alphabetically",
    2021: "https://www.nhtsa.gov/document/2021-aala-listed-alphabetically",
    2022: "https://www.nhtsa.gov/document/2022-aala-listed-alphabetically",
    2023: "https://www.nhtsa.gov/document/2023-aala-listed-alphabetically",
    2024: "https://www.nhtsa.gov/document/2024-aala-listed-alphabetically",
    2025: "https://www.nhtsa.gov/document/2025-aala-listed-alphabetically",
    2026: "https://www.nhtsa.gov/document/2026-aala-listed-alphabetically"
}

# Country Mapping for Normalization
# Based on official NHTSA AALA document key
COUNTRY_MAPPING = {
    # United States
    "US": "United States",
    "USA": "United States",
    "U.S.": "United States",
    
    # Mexico
    "M": "Mexico",
    "MEX": "Mexico",
    "MX": "Mexico",
    
    # Canada
    "CN": "Canada",
    "CAN": "Canada",
    "CA": "Canada",
    
    # Japan
    "J": "Japan",
    "JPN": "Japan",
    "JP": "Japan",
    
    # Germany
    "G": "Germany",
    "GER": "Germany",
    "GERMANY": "Germany",
    
    # Denmark
    "DE": "Denmark",
    
    # South Korea
    "K": "South Korea",
    "KOR": "South Korea",
    "KR": "South Korea",
    "KOREA": "South Korea",
    
    # United Kingdom / Great Britain
    "UK": "United Kingdom",
    "GB": "United Kingdom",
    
    # Italy
    "I": "Italy",
    "ITA": "Italy",
    "IT": "Italy",
    
    # France
    "F": "France",
    "FRA": "France",
    "FR": "France",
    
    # Sweden
    "SW": "Sweden",
    "SWE": "Sweden",
    "SE": "Sweden",
    
    # Hungary
    "H": "Hungary",
    "HUN": "Hungary",
    "HU": "Hungary",
    
    # Austria
    "AT": "Austria",
    "AUT": "Austria",
    "A": "Austria",
    
    # Belgium
    "BE": "Belgium",
    "BEL": "Belgium",
    
    # China
    "CH": "China",
    "CHN": "China",
    
    # Czech Republic
    "CZ": "Czech Republic",
    "CZE": "Czech Republic",
    
    # Finland
    "FN": "Finland",
    "FIN": "Finland",
    "FI": "Finland",
    
    # Spain
    "SP": "Spain",
    "ESP": "Spain",
    
    # Slovakia
    "SL": "Slovakia",
    "SVK": "Slovakia",
    "SK": "Slovakia",
    
    # Turkey
    "T": "Turkey",
    "TUR": "Turkey",
    "TR": "Turkey",
    
    # Brazil
    "BR": "Brazil",
    "BRA": "Brazil",
    
    # South Africa
    "SA": "South Africa",
    "RSA": "South Africa",
    "ZA": "South Africa",
    "AF": "South Africa",  # BMW uses AF for Africa/South Africa
    
    # Australia
    "AU": "Australia",
    "AUS": "Australia",
    
    # Poland
    "PL": "Poland",
    "POL": "Poland",
    
    # Thailand
    "TH": "Thailand",
    "THA": "Thailand",
    
    # Indonesia
    "ID": "Indonesia",
    "IDN": "Indonesia",
    
    # India
    "IN": "India",
    "IND": "India",
    
    # Philippines
    "P": "Philippines",
    
    # Portugal
    "PO": "Portugal",
    "PRT": "Portugal",
    "PT": "Portugal",
    
    # Netherlands
    "N": "Netherlands",
    "NLD": "Netherlands",
    "NL": "Netherlands",
    
    # Romania
    "R": "Romania",
    
    # Russia
    "RU": "Russia",
    "RUS": "Russia",
    
    # Singapore
    "SI": "Singapore",
    
    # Cuba
    "CU": "Cuba",
    
    # Other
    "OT": "Other",
    
    # Malaysia (not in official list but may appear)
    "MYS": "Malaysia",
    "MY": "Malaysia",
    
    # Argentina (not in official list but may appear)
    "ARG": "Argentina",
    "AR": "Argentina",
    
    # Taiwan (not in official list but may appear)
    "TW": "Taiwan",
    "TWN": "Taiwan",
    
    # Vietnam (not in official list but may appear)
    "VNM": "Vietnam",
    "VN": "Vietnam",
    
    # Serbia (not in official list but may appear)
    "SERBIA": "Serbia",
}

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def get_pdf_url_from_landing_page(landing_url):
    print(f"Scraping landing page: {landing_url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(landing_url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to access landing page {landing_url}. Status: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        # Look for links ending in .pdf
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$'))
        
        # Filter for likely report links (often contain 'AALA' or 'Alphabetical')
        for link in pdf_links:
            href = link.get('href')
            if 'AALA' in href or 'Alphabetical' in href:
                full_url = urljoin("https://www.nhtsa.gov", href)
                return full_url
        
        # Fallback: just return the first PDF link if no specific keyword found
        if pdf_links:
            full_url = urljoin("https://www.nhtsa.gov", pdf_links[0].get('href'))
            return full_url
            
        print("No PDF link found on page.")
        return None
        
    except Exception as e:
        print(f"Error scraping {landing_url}: {e}")
        return None

def download_pdf(url, path):
    if os.path.exists(path):
        print(f"File already exists: {path}")
        return True

    print(f"Downloading PDF from {url}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.nhtsa.gov/"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            with open(path, 'wb') as f:
                f.write(response.content)
            print(f"PDF saved to {path}")
            return True
        else:
            print(f"Failed to download PDF. Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"Download error: {e}")
        return False

def normalize_country(code, context=""):
    """
    Normalize country codes to full country names.
    Handles various formats:
    - Single letter codes: G, J, H, K, M, I, etc.
    - Standard ISO codes: US, MX, JP, etc.
    - Values with parentheses: "G (AWD)", "US (2.0L)"
    - City + Country: "Cassino Italy", "Detroit MI USA"
    - US/Canadian cities with state/province abbreviations
    """
    if not isinstance(code, str):
        return None
    
    original = code.strip()
    if not original:
        return None
    
    # Remove parenthetical info like "(AWD)", "(2.0L)", "(FWD)"
    code = re.sub(r'\s*\([^)]*\)', '', original).strip()
    
    # Handle multi-line values - take first part
    if '\n' in code:
        code = code.split('\n')[0].strip()
    
    code_upper = code.upper()
    
    # US state abbreviations - map city names with US states to United States
    US_STATES = {
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID',
        'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS',
        'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK',
        'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV',
        'WI', 'WY', 'DC'
    }
    
    # Canadian province abbreviations
    CA_PROVINCES = {'ON', 'QC', 'BC', 'AB', 'MB', 'SK', 'NS', 'NB', 'NL', 'PE', 'YT', 'NT', 'NU'}
    
    # Known German cities (for cases where just city name is provided)
    GERMAN_CITIES = {'LEIPZIG', 'MUNICH', 'BERLIN', 'HAMBURG', 'STUTTGART', 'COLOGNE', 
                     'FRANKFURT', 'DUSSELDORF', 'BREMEN', 'HANNOVER', 'WOLFSBURG',
                     'INGOLSTADT', 'REGENSBURG', 'RUSSELSHEIM', 'ZWICKAU'}
    
    # Check if any word is a US state abbreviation
    words = code_upper.replace(',', ' ').split()
    for word in words:
        if word in US_STATES:
            return "United States"
        if word in CA_PROVINCES:
            return "Canada"
        if word in GERMAN_CITIES:
            return "Germany"
    
    # Check if it starts with known country prefixes like "Us," "M," "K,"
    if code_upper.startswith('US,') or code_upper.startswith('US '):
        return "United States"
    if code_upper.startswith('M,') or code_upper.startswith('M '):
        return "Mexico"
    if code_upper.startswith('K,'):
        return "South Korea"
    if code_upper.startswith('G,'):
        return "Germany"
    
    # Check if it's a city + country format like "Cassino Italy", "Detroit MI USA"
    # Try to extract the country from the end
    if len(words) >= 2:
        # Check last word first
        last_word = words[-1]
        if last_word in COUNTRY_MAPPING:
            return COUNTRY_MAPPING[last_word]
        # Check if last two words form a country name
        if len(words) >= 2:
            last_two = ' '.join(words[-2:])
            if last_two in ["SOUTH KOREA", "SOUTH AFRICA", "UNITED STATES", "UNITED KINGDOM", "CZECH REPUBLIC"]:
                return last_two.title()
    
    # Direct lookup
    if code_upper in COUNTRY_MAPPING:
        return COUNTRY_MAPPING[code_upper]
    
    # Check for known full country names (case insensitive)
    known_countries = [
        "UNITED STATES", "MEXICO", "CANADA", "JAPAN", "GERMANY", "SOUTH KOREA",
        "UNITED KINGDOM", "GREAT BRITAIN", "ITALY", "FRANCE", "SWEDEN", "HUNGARY", 
        "AUSTRIA", "BELGIUM", "CHINA", "CZECH REPUBLIC", "FINLAND", "SPAIN", 
        "SLOVAKIA", "TURKEY", "BRAZIL", "SOUTH AFRICA", "AUSTRALIA", "POLAND", 
        "THAILAND", "INDONESIA", "MALAYSIA", "ARGENTINA", "TAIWAN", "VIETNAM", 
        "INDIA", "PORTUGAL", "NETHERLANDS", "RUSSIA", "SERBIA", "DENMARK",
        "PHILIPPINES", "ROMANIA", "SINGAPORE", "CUBA"
    ]
    for country in known_countries:
        if country in code_upper:
            return country.title()
    
    # If nothing matched, return the cleaned code title-cased if it's long enough
    if len(code) > 3:
        return code.title()
        
    return code

def parse_pdf(pdf_path, year):
    print(f"Parsing PDF: {pdf_path}")
    data = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    for row in table:
                        # Clean row
                        cleaned_row = [cell.strip() if cell else "" for cell in row]
                        
                        # Skip empty or header rows
                        if not any(cleaned_row) or "Manufacturer" in cleaned_row[0] or "Car Line" in cleaned_row[0]:
                            continue
                        
                        # Heuristic: Valid data rows usually have a Manufacturer (col 0) and Car Line (col 1)
                        if not cleaned_row[0]: 
                            continue

                        # Add Year
                        cleaned_row.append(year)
                        data.append(cleaned_row)
    except Exception as e:
        print(f"Error parsing {pdf_path}: {e}")
        
    print(f"Extracted {len(data)} rows from {year}.")
    return data

# Manufacturer name normalization mapping
MANUFACTURER_NORMALIZATION = {
    # General Motors variations
    "GM LLC": "General Motors",
    "General Motors LLC": "General Motors",
    
    # FCA / Stellantis variations
    "FCA": "Stellantis",
    "Fiat Chrysler": "Stellantis",
    
    # Honda variations
    "Honda Motor Co.,": "Honda",
    "Honda Motor Co., Ltd.": "Honda",
    
    # Hyundai variations
    "Hyundai Motor": "Hyundai",
    "Hyundai Motor Company": "Hyundai",
    
    # Jaguar Land Rover variations (including OCR errors)
    "Jaguar Land Rover": "Jaguar Land Rover",
    "JaguaLr iLmaintedd Rover": "Jaguar Land Rover",
    "Jaguar Land Rover Limited": "Jaguar Land Rover",
    
    # Mazda variations
    "Mazda Motor": "Mazda",
    "Mazda Motor Corporation": "Mazda",
    
    # Mitsubishi variations
    "Mitsubishi Motors": "Mitsubishi",
    "Mitsubishi Motors Corporation": "Mitsubishi",
    
    # Nissan variations
    "Nissan North": "Nissan",
    "Nissan North America,": "Nissan",
    "Nissan North America, Inc": "Nissan",
    
    # Bugatti variations
    "Bugatti Automobiles": "Bugatti",
    "Bugatti Automobiles S.A.S.": "Bugatti",
    
    # Rolls-Royce variation
    "Rolls-Royce Motor": "Rolls-Royce",
    
    # Tesla variation
    "Tesla Inc.": "Tesla",
    
    # Lotus variation
    "Lotus Cars Ltd.": "Lotus",
    
    # Lucid variation
    "Lucid USA, Inc.": "Lucid",
    
    # Kia variation
    "Kia Motors": "Kia",
}

# Invalid manufacturer entries to skip
INVALID_MANUFACTURERS = {
    "Limited", "XC90 Aut (8vxl) FWD + ERAD (T8 AWD)", ""
}

def clean_manufacturer(raw_manufacturer):
    """
    Clean manufacturer name from raw PDF data.
    Handles multiline concatenation and extracts just the manufacturer name.
    """
    if not raw_manufacturer or not isinstance(raw_manufacturer, str):
        return None
    
    # Take only the first line if there are multiple
    first_line = raw_manufacturer.split('\n')[0].strip()
    
    # Skip if this looks like a legend entry (2-letter codes)
    if re.match(r'^[A-Z]{1,2}\s+[A-Z][a-z]+$', first_line):
        return None  # e.g., "AU Australia", "BE Belgium"
    
    # Skip invalid entries
    if first_line in INVALID_MANUFACTURERS:
        return None
    
    # Skip if it looks like a car model (contains model patterns)
    if re.match(r'^[A-Z0-9]+\s+(Aut|AWD|FWD|RWD)', first_line):
        return None
    
    # Skip if this contains data patterns (percentages, vehicle types)
    if re.search(r'\d+%|MPV|PC\s|Truck', first_line):
        # Try to extract just the manufacturer name (first word or known pattern)
        known_manufacturers = list(MANUFACTURER_NORMALIZATION.keys()) + [
            "Audi", "BMW AG", "Bentley", "Ford Motor Company", "Porsche AG",
            "Subaru", "Toyota", "Volkswagen", "Volvo", "Mercedes-Benz USA",
            "Lamborghini", "Polestar"
        ]
        for mfg in known_manufacturers:
            if first_line.startswith(mfg):
                return mfg
        # If no known manufacturer found, try to get first word
        words = first_line.split()
        if words:
            return words[0]
        return None
    
    return first_line

def normalize_manufacturer(manufacturer):
    """Normalize manufacturer name to canonical form."""
    if not manufacturer:
        return None
    
    # Check if it starts with a known pattern that needs normalization
    for pattern, normalized in MANUFACTURER_NORMALIZATION.items():
        if manufacturer.startswith(pattern) or manufacturer == pattern:
            return normalized
    
    # Handle Subaru with car name attached
    if manufacturer.startswith("Subaru Subaru"):
        return "Subaru"
    if manufacturer.startswith("Tesla Inc. Tesla"):
        return "Tesla"
    
    return manufacturer

def clean_car_line(raw_car_line):
    """Clean car line name from raw PDF data."""
    if not raw_car_line or not isinstance(raw_car_line, str):
        return None
    
    # Take only the first line
    first_line = raw_car_line.split('\n')[0].strip()
    
    # Skip if empty
    if not first_line:
        return None
        
    return first_line

def parse_country_percentage(value):
    """
    Parse a country percentage string like "50%G" or "26% H" into (percentage, country_code).
    Returns (None, None) if parsing fails.
    """
    if not value or not isinstance(value, str):
        return None, None
    
    value = value.strip()
    if not value:
        return None, None
    
    # Take first line if multiline
    value = value.split('\n')[0].strip()
    
    # Pattern: number% followed by optional space and country code
    # Examples: "50%G", "26% H", "50% G", "100% J"
    match = re.match(r'(\d+)\s*%\s*([A-Za-z]+)?', value)
    if match:
        percentage = int(match.group(1))
        country_code = match.group(2).upper() if match.group(2) else None
        return percentage, country_code
    
    return None, None

def parse_us_canada_percentage(value):
    """Parse the US/Canada percentage string into a numeric value."""
    if not value or not isinstance(value, str):
        return 0
    
    value = value.strip()
    match = re.match(r'(\d+)\s*%?', value)
    if match:
        return int(match.group(1))
    return 0

def process_data(raw_data):
    """
    Process raw PDF data into structured format.
    
    Typical column structure from NHTSA PDFs:
    [0]: Manufacturer
    [1]: Brand/Car Line (sometimes duplicate)
    [2]: Model/Car Line name
    [3]: Vehicle Type (PC, MPV, Truck)
    [4]: % Content US/Canada
    [5]: % from Country 1 (e.g., "50%G")
    [6]: % from Country 2 (e.g., "26%H")
    [7]: Engine source country code (e.g., "G", "J", "US")
    [8]: (often empty or additional info)
    [9]: Transmission source country code (e.g., "H", "G", "US")
    [10]: (often empty or additional info)
    [11] or [-3]: Assembly location/country
    [12] or [-2]: (often empty)
    [-1]: Year (added by parser)
    """
    # Legend entries to skip (country code definitions)
    LEGEND_PATTERNS = [
        r'^AU\s', r'^AT\s', r'^BE\s', r'^BR\s', r'^CH\s', r'^CU\s', r'^CN\s',
        r'^CZ\s', r'^DE\s', r'^F\s', r'^FN\s', r'^G\s', r'^H\s', r'^I\s',
        r'^ID\s', r'^IN\s', r'^J\s', r'^K\s', r'^M\s', r'^N\s', r'^OT\s',
        r'^P\s', r'^PL\s', r'^PO\s', r'^R\s', r'^RU\s', r'^SA\s', r'^SI\s',
        r'^SL\s', r'^SP\s', r'^SW\s', r'^T\s', r'^TH\s', r'^UK\s', r'^US\s'
    ]
    
    processed = []
    for row in raw_data:
        if len(row) < 8:  # Need at least enough columns for key data
            continue
            
        year = row[-1]
        
        # Extract and clean manufacturer
        raw_manufacturer = row[0]
        
        # Skip legend entries
        is_legend = False
        for pattern in LEGEND_PATTERNS:
            if re.match(pattern, str(raw_manufacturer)):
                is_legend = True
                break
        if is_legend:
            continue
        
        manufacturer = clean_manufacturer(raw_manufacturer)
        if not manufacturer:
            continue
        
        # Normalize to canonical manufacturer name
        manufacturer = normalize_manufacturer(manufacturer)
            
        # Extract and clean car line
        raw_car_line = row[2] if len(row) > 2 else row[1]
        car_line = clean_car_line(raw_car_line)
        if not car_line:
            car_line = row[1] if len(row) > 1 else ""  # Fallback to column 1
        
        # Percent content US/Canada is in column 4
        percent_content_raw = row[4] if len(row) > 4 else "0"
        percent_us_canada = parse_us_canada_percentage(percent_content_raw)
        
        # Country-specific percentages in columns 5 and 6
        country1_raw = row[5] if len(row) > 5 else ""
        country2_raw = row[6] if len(row) > 6 else ""
        
        pct1, code1 = parse_country_percentage(country1_raw)
        pct2, code2 = parse_country_percentage(country2_raw)
        
        # Normalize country codes for percentages
        country1_name = normalize_country(code1, manufacturer) if code1 else None
        country2_name = normalize_country(code2, manufacturer) if code2 else None
        
        # Engine source is in column 7
        engine = row[7] if len(row) > 7 else ""
        
        # Transmission source is in column 9
        trans = row[9] if len(row) > 9 else ""
        
        # Assembly country is at index -3 (third from last, before empty col and year)
        assembly = row[-3] if len(row) > 3 else ""
        
        # Normalize country codes to full names
        engine_norm = normalize_country(engine, manufacturer)
        trans_norm = normalize_country(trans, manufacturer)
        assembly_norm = normalize_country(assembly, manufacturer)
        
        entry = {
            "Year": year,
            "Manufacturer": manufacturer,
            "Car Line": car_line,
            "% US/Canada": percent_us_canada,
            "Primary Country": country1_name if country1_name else "",
            "Primary %": pct1 if pct1 else 0,
            "Secondary Country": country2_name if country2_name else "",
            "Secondary %": pct2 if pct2 else 0,
            "Engine Source": engine_norm if engine_norm else engine,
            "Transmission Source": trans_norm if trans_norm else trans,
            "Assembly Country": assembly_norm if assembly_norm else assembly,
            "Raw": str(row)
        }
        processed.append(entry)
        
    return pd.DataFrame(processed)

def main():
    ensure_data_dir()
    
    all_raw_data = []
    failed_downloads = []
    
    for year, landing_url in YEAR_URLS.items():
        pdf_filename = f"MY{year}_AALA.pdf"
        pdf_path = os.path.join(DATA_DIR, pdf_filename)
        
        # 1. Check if exists
        if os.path.exists(pdf_path):
            print(f"Found existing file for {year}")
        else:
            # 2. Get PDF URL
            pdf_url = get_pdf_url_from_landing_page(landing_url)
            if pdf_url:
                # 3. Download
                success = download_pdf(pdf_url, pdf_path)
                if not success:
                    failed_downloads.append((year, pdf_url))
            else:
                print(f"Could not find PDF link for {year}")
                failed_downloads.append((year, landing_url))
        
        # 4. Parse if exists
        if os.path.exists(pdf_path):
            year_data = parse_pdf(pdf_path, year)
            all_raw_data.extend(year_data)
            
    # Report failures
    if failed_downloads:
        print("\n" + "="*50)
        print("WARNING: Failed to download some reports.")
        print("Please manually download the following and save to 'data/' folder:")
        for year, url in failed_downloads:
            print(f"Year {year}: {url} -> Save as MY{year}_AALA.pdf")
        print("="*50 + "\n")
    
    # Process and Save
    if all_raw_data:
        df = process_data(all_raw_data)
        df.to_csv(CSV_PATH, index=False)
        print(f"Saved processed data to {CSV_PATH}")
        print(df.head())
    else:
        print("No data extracted.")

if __name__ == "__main__":
    main()
