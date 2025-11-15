import pandas as pd
import re
import unicodedata
import os
import glob
from datetime import datetime, timedelta
import unidecode

# --- Default prices per year ---
DEFAULT_PRICES = {year: f"{50 + (year-2018)*5}E" for year in range(2018, 2027)}

# --- Default groups ---
DEFAULT_GROUPS = {
    'Family': ['Family', 'Multiple families'],
    'Friends & Family': ['Friends & Family', 'Friends with foreign friends'],
    'Students': ['Students', 'School students', 'Students/School'],
    'Foreigners': ['Foreigners', 'Foreign students'],
    'Colleagues': ['Colleagues', 'Co-workers'],
    'Company': ['Company'],
    'Friends': ['Friends']
}

# Normalize status mapping
status_mapping = {}
for main_group, sub_groups in DEFAULT_GROUPS.items():
    for subgroup in sub_groups:
        status_mapping[subgroup.strip().lower()] = main_group

# --- Celebration mapping ---
CELEBRATION_GROUPS = {
    'Birthday': ['Birthday'],
    'Company event': ['Company', 'Team building'],
    'Other celebrations': ['Other', 'Occasion', 'Party'],
    'Educational': ['Trip', 'Camp'],
    'None': ['None', 'Friends']
}

celebration_mapping = {}
for main_group, sub_groups in CELEBRATION_GROUPS.items():
    for subgroup in sub_groups:
        celebration_mapping[subgroup.strip()] = main_group

# --- Source keywords ---
GROUP_KEYWORDS = {
    "ONLINE": [r"INTERNET", r"WWW", r"GOOGLE", r"FOUND ONLINE"],
    "VISITED": [r"VISITED", r"ALREADY VISITED"],
    "COUPON": [r"COUPON", r"GIFT"],
    "REFERRED": [r"REFERRED", r"FRIEND"],
    "SOCIAL": [r"FACEBOOK", r"INSTAGRAM", r"TIKTOK"],
    "CAMP": [r"CAMP", r"SCHOOL CAMP", r"SUMMER CAMP"]
}

# --- Utility functions ---
def categorize_age(age):
    try:
        age = int(age)
    except:
        return "N/A"
    ranges = [(7,9),(10,13),(14,18),(19,24),(25,32),(33,40)]
    labels = ["7–9","10–13","14–18","19–24","25–32","33–40"]
    for r,l in zip(ranges, labels):
        if r[0]<=age<=r[1]:
            return l
    return "41+"

def clean_text(text):
    if pd.isna(text):
        return ""
    text = text.upper()
    text = ''.join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c))
    return re.sub(r'[^A-Z0-9 ]', '', text).strip()

def clean_source(text):
    if pd.isna(text) or str(text).strip() == "":
        return "ONLINE"
    norm = unidecode.unidecode(str(text)).upper().strip()
    for canonical, patterns in GROUP_KEYWORDS.items():
        for pat in patterns:
            if re.search(pat, norm):
                return canonical
    return norm

def round_to_casual_time(time_obj):
    if time_obj is None:
        return None
    casual_times = ['12:00','14:00','16:00','18:00']
    casual_dt = [datetime.strptime(t,'%H:%M').time() for t in casual_times]
    if isinstance(time_obj, datetime):
        current_time = time_obj.time()
    else:
        current_time = time_obj
    best_match = min(casual_dt, key=lambda t: abs(datetime.combine(datetime.today(),t)-datetime.combine(datetime.today(),current_time)))
    return best_match.strftime('%H:%M')

def standardize_room(value):
    mapping = {
        'ROOM1':['ROOM1','R1','Alias1'],
        'ROOM2':['ROOM2','R2','Alias2'],
        'ROOM3':['ROOM3','R3','Alias3']
    }
    norm = clean_text(str(value))
    for key, aliases in mapping.items():
        if norm == clean_text(key) or norm in [clean_text(a) for a in aliases]:
            return key
    return norm

def clean_price_series(price_series, year):
    default_price = DEFAULT_PRICES.get(year,'50E')
    cleaned = []
    for val in price_series.fillna("").astype(str):
        numbers = re.findall(r'\d+', val)
        cleaned.append(f"{numbers[0]}E" if numbers else default_price)
    return pd.Series(cleaned, index=price_series.index)

def clean_escape_time(value):
    if pd.isna(value):
        return "-"
    try:
        td = pd.to_timedelta(str(value))
        return round(td.total_seconds()/60,2)
    except:
        return "-"

def assign_team_type(room, age_group):
    kids_rooms = ['ROOM1','ROOM2']
    if room in kids_rooms or age_group in ['7–9','10–13']:
        return 'Kids'
    return 'Grown-up'

# --- File processing ---
def process_file(input_path, output_path):
    filename = os.path.basename(input_path)
    year_match = re.search(r'(\d{4})', filename)
    if not year_match:
        return
    year = int(year_match.group(1))
    df = pd.read_csv(input_path,dtype=str)
    df.drop_duplicates(inplace=True)
    df['Room'] = df['Room'].apply(standardize_room)
    df['Source'] = df['Source'].apply(clean_source)
    df['Price'] = clean_price_series(df['Price'], year)
    df['EscapeTime'] = df['EscapeTime'].apply(clean_escape_time)
    df['AgeGroup'] = df['Age'].apply(lambda x: categorize_age(pd.to_numeric(x,errors='coerce')))
    df['TeamType'] = df.apply(lambda row: assign_team_type(row['Room'], row['AgeGroup']),axis=1)
    df.to_csv(output_path,index=False)

def process_all_files(input_folder, output_folder, pattern="data_*.csv"):
    os.makedirs(output_folder,exist_ok=True)
    for f in glob.glob(os.path.join(input_folder,pattern)):
        output_path = os.path.join(output_folder,f"cleaned_{os.path.basename(f)}")
        process_file(f,output_path)

def merge_cleaned_files(folder, output_file):
    files = glob.glob(os.path.join(folder,"cleaned_*.csv"))
    df_list = [pd.read_csv(f,dtype=str) for f in files]
    merged = pd.concat(df_list,ignore_index=True,sort=False)
    merged.to_csv(output_file,index=False)

if __name__ == "__main__":
    input_folder = "data/raw"
    cleaned_folder = "data/cleaned"
    merged_file = "data/merged.csv"
    process_all_files(input_folder,cleaned_folder)
    merge_cleaned_files(cleaned_folder,merged_file)
