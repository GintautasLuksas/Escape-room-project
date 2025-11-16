import pandas as pd
import re
import unicodedata
import os
import glob
from datetime import datetime, timedelta
import unidecode

DEFAULT_PRICES_City1 = {
    2018: "20E",
    2019: "20E",
    2020: "30E",
    2021: "30E",
    2022: "40E",
    2023: "50E",
    2024: "80E",
    2025: "100E",
    2026: "150E"
}

DEFAULT_GROUPS = {
    "Family": [
        "family_single", "family_multiple"
    ],
    "Family_with_friends": [
        "family_with_friends", "family_with_foreign_friends"
    ],
    "Students": [
        "students", "school_students", "students_mixed", "student_group_variant"
    ],
    "Foreign_visitors": [
        "foreign_visitors", "foreign_student_group"
    ],
    "Colleagues": [
        "female_colleagues", "colleagues"
    ],
    "Company_Organization": [
        "company_organization"
    ],
    "Friends": [
        "friends_variant_a", "friends_variant_b"
    ]
}

status_mapping = {}

for main_group, sub_groups in DEFAULT_GROUPS.items():
    for subgroup in sub_groups:
        normalized = subgroup.strip().lower()
        status_mapping[normalized] = main_group


status_mapping["student_group_alias"] = "Students"
CELEBRATION_GROUPS = {
    "Birthday": [
        "birthday_party", "surprise_birthday"
    ],
    "Anniversary": [
        "wedding_anniversary", "relationship_anniversary"
    ],
    "Work_Event": [
        "team_building", "promotion_celebration"
    ],
    "Holiday": [
        "new_year", "christmas", "easter"
    ],
    "Other": [
        "random_celebration", "just_for_fun"
    ]
}

celebration_mapping = {}
for main_group, sub_groups in CELEBRATION_GROUPS.items():
    for subgroup in sub_groups:
        key = subgroup.strip().lower()
        celebration_mapping[key] = main_group



GROUP_KEYWORDS = {
    "ONLINE": [
        r"\bINTERNET", r"\bSEARCH_ENGINE\b", r"\bWWW\b",
        r"LOOKED_ONLINE", r"FOUND_ONLINE", r"ONLINE_SEARCH", r"INTERNET_MISSPELLED"
    ],
    "RETURNING": [
        r"\bRETURNED\b", r"\bVISITED_BEFORE\b", r"\bPREVIOUSLY_PLAYED\b",
        r"ONE_ALREADY_PLAYED", r"PARENTS_VISITED", r"\bVISITED_ROOM\b", r"VISITED_.*ROOM"
    ],
    "COUPON": [
        r"\bCOUPON", r"\bGIFT_VOUCHER\b", r"RECEIVED_COUPON", r"COUPON_VARIANT",
        r"HAD_COUPON", r"CAME_WITH_COUPON"
    ],
    "REFERRED": [
        r"REFERRED", r"\bBY_FRIEND\b", r"FRIENDS_REFERRED",
        r"\bBY_COLLEAGUE\b", r"RECOMMENDATION"
    ],
    "SOCIAL_MEDIA": [
        r"\bFACEBOOK\b", r"\bFB\b", r"\bINSTAGRAM\b", r"\bIG\b",
        r"\bTIKTOK\b", r"\bTRIP_REVIEW\b", r"\bSOCIAL_PLATFORM\b",
        r"\bSINGLE_W\b"
    ],
    "CAMPS": [
        r"\bCAMP\b", r"SCHOOL_CAMP", r"SUMMER_CAMP"
    ]
}



def categorize_age(age):
    try:
        age = int(age)
    except:
        return "N/A"

    if 7 <= age <= 9: return "7–9"
    elif 10 <= age <= 13: return "10–13"
    elif 14 <= age <= 17: return "14–17"
    elif 8 <= age <= 24: return "19–24"
    elif 25 <= age <= 29: return "25–29"
    elif 30 <= age <= 40: return "30–40"
    elif age >= 41: return "41+"
    return "N/A"

def fill_missing_age_group(row):
    '''
    Fill missing 'Age Group' based on room.
    '''
    if row['Age Group'] != "N/A":
        return row['Age Group']

    room = row['Room Type']
    if room in ["KV1", "AV2"]:
        return "7–9"
    elif room in ["KV3", "AV1", "KV2"]:
        return "10–13"
    else:
        return "25–29"


def assign_team_type(row):
    always_kids = {"KV3", "AV1", "KV2"}
    always_grownups = {"KS1", "AS3", "KS2", "AS4", "KS3"}
    conditional_rooms = {"AS1", "AS2", "AV2", "KV1"}

    room = row['Room Type']
    age_group = row['Age Group']

    if room in always_kids:
        return "Kids"
    elif room in always_grownups:
        return "Grown-up"
    elif room in conditional_rooms:
        if age_group in ["7–9", "10–13"]:
            return "Kids"
        else:
            return "Grown-up"
    else:
        return "Unknown"



def clean_source(text: str) -> str:
    import re, unidecode, pandas as pd
    if pd.isna(text) or str(text).strip() == "":
        return "ONLINE"

    norm = unidecode.unidecode(str(text)).upper().strip()

    for canonical, patterns in GROUP_KEYWORDS.items():
        for pat in patterns:
            if re.search(pat, norm):
                return canonical

    return norm


def round_to_casual_time(time_obj):
    '''
    Round a time or datetime object to the nearest casual time.
    Times earlier than 13:30 are rounded to 12:00.
    '''
    if time_obj is None:
        return None

    casual_times = ['12:00', '14:00', '16:00', '18:00', '20:00', '22:00']
    casual_dt = [datetime.strptime(t, '%H:%M').time() for t in casual_times]

    if isinstance(time_obj, datetime):
        current_time = time_obj.time()
    else:
        current_time = time_obj

    if current_time < datetime.strptime('12:00', '%H:%M').time():
        return '10:00'

    min_diff = timedelta(hours=24)
    best_match = None
    dummy_date = datetime.today().date()
    current_dt = datetime.combine(dummy_date, current_time)

    for t in casual_dt:
        casual_dt_time = datetime.combine(dummy_date, t)
        diff = abs(current_dt - casual_dt_time)
        if diff < min_diff:
            min_diff = diff
            best_match = t

    if best_match:
        return best_match.strftime('%H:%M')
    else:
        return None


def clean_text(text):
    '''Normalize and clean text by converting to uppercase, removing accents, and filtering out unwanted characters.'''
    if pd.isna(text):
        return ""
    text = text.upper()
    text = ''.join((c if not unicodedata.combining(c) else '') for c in unicodedata.normalize('NFKD', text))
    return re.sub(r'[^A-Z0-9 ]', '', text).strip()


def clean_price_series_City1(price_series: pd.Series, file_year: int) -> pd.Series:
    '''
    Clean City1 price series by:
    1. Splitting merged Excel price cells across multiple rows.
       Example: '160' over 3 rows with default 50E -> [100E, 30E, 30E]
    2. Ignoring coupon codes or numbers outside 30–600 range.
    3. Filling default price where necessary.
    '''
    default_price_str = DEFAULT_PRICES_City1.get(file_year, "30E")
    default_price = int(re.search(r'\d+', default_price_str).group())

    values = price_series.fillna("").astype(str).str.upper().tolist()
    cleaned = []
    i = 0
    n = len(values)

    while i < n:
        val = values[i].strip()

        # --- Extract numeric price if valid (30–600) ---
        matches = re.findall(r'\d+', val)
        valid_matches = [int(m) for m in matches if 30 <= int(m) <= 600]

        if valid_matches:
            total_price = valid_matches[0]

            # Count following empty/NO_PRICE/NAN rows as part of merged block
            j = i + 1
            empty_count = 0
            while j < n and values[j].strip() in ["", "NO_PRICE", "NAN"]:
                empty_count += 1
                j += 1

            block_size = 1 + empty_count
            leftover = max(total_price - default_price * empty_count, default_price)

            # First row gets leftover, rest get default
            cleaned.append(f"{leftover}E")
            for _ in range(empty_count):
                cleaned.append(f"{default_price}E")

            i += block_size
            continue

        coupon_keywords = ["COUPOUN", "GERA DOVANA", "GIFT", "GIFTY"]
        if any(k in val for k in coupon_keywords):
            cleaned.append(f"{default_price}E")
            i += 1
            continue

        cleaned.append(f"{default_price}E")
        i += 1

    return pd.Series(cleaned, index=price_series.index)




def clean_escape_time(value):
    '''
    Convert time strings 'HH:MM' or 'HH:MM:SS' to total minutes as float.
    Return '-' if invalid or missing.
    '''
    if pd.isna(value):
        return "-"
    value_str = str(value).strip()
    try:
        # Use pandas to_timedelta for parsing
        td = pd.to_timedelta(value_str)
        total_minutes = td.total_seconds() / 60
        return round(total_minutes, 2)  # rounded to 2 decimals
    except Exception:
        return "-"

def normalize_text(text) -> str:
    '''
    Normalize text by stripping whitespace, uppercasing,
    and removing accents. If input is not a string, return empty string.
    '''
    if not isinstance(text, str):
        return ''
    text = text.strip().upper()
    text = ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )
    return text

def standardize_room(value) -> str:
    '''
    Map various room name aliases to standardized room names using extended mapping.
    '''
    mapping = {
        "KV1": ["KV1A", "KV1B"],
        "AV2": ["AV2A", "AV2B", "AV2C"],
        "AS1": ["AS1A", "AS1B", "AS1C", "AS1D", "AS1E", "AS1F", "AS1G", "AS1H", "AS1I", "AS1J"],
        "AS2": ["AS2A", "AS2B", "AS2C", "AS2D", "AS2E", "AS2F", "AS2G", "AS2H", "AS2I", "AS2J"],
        "KS1": ["KS1A", "KS1B", "KS1C", "KS1D", "KS1E", "KS1F", "KS1G", "KS1H"],
        "AS3": ["AS3A", "AS3B", "AS3C"],
        "KV3": ["KV3A", "KV3B", "KV3C", "KV3D", "KV3E", "KV3F", "KV3G"],
        "KS2": ["KS2A", "KS2B", "KS2C", "KS2D", "KS2E", "KS2F"],
        "AS4": ["AS4A", "AS4B", "AS4C", "AS4D", "AS4E"],
        "AV1": ["AV1A", "AV1B", "AV1C", "AV1D"],
        "KV2": ["KV2A", "KV2B"],
        "KS3": ["KS3A"]
    }

    normalized_value = normalize_text(value)
    for standard_name, aliases in mapping.items():
        normalized_aliases = [normalize_text(alias) for alias in aliases]
        if normalized_value == normalize_text(standard_name) or normalized_value in normalized_aliases:
            return standard_name
    return None

def filter_rooms(room_list):
    '''
    Filter and standardize rooms in a list, keeping only allowed rooms.
    '''
    allowed_rooms = {
        'AS2', 'KS1', 'AS1', 'AS3', 'AV2',
        'AS4', 'KV3', 'KV2',
        'KV1', 'AV1', 'KS2'
    }
    standardized = [standardize_room(room) for room in room_list]
    filtered = [room for room in standardized if room in allowed_rooms]
    return filtered


def process_file(input_path, output_path):
    '''Load a CSV file, clean and standardize the data, then save the cleaned DataFrame.'''
    filename = os.path.basename(input_path)
    year_match = re.search(r'(\d{4})', filename)
    if not year_match:
        print(f"Year not found in filename: {filename}. Skipping file.")
        return
    file_year = int(year_match.group(1))

    try:
        df = pd.read_csv(input_path, dtype=str)
        if df.empty:
            print(f"Skipping empty file: {input_path}")
            return
    except pd.errors.EmptyDataError:
        print(f"Skipping empty or invalid file: {input_path}")
        return

    df.drop_duplicates(inplace=True)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    df = df[df['Date'].dt.year == file_year]
    if df.empty:
        print(f"No rows matching year {file_year} in file: {filename}. Skipping save.")
        return
    df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')

    if 'Time' in df.columns:
        df['Time'] = df['Time'].fillna(method='ffill')
        parsed = pd.to_datetime(df['Time'], format='%H:%M:%S', errors='coerce')
        mask = parsed.isna()
        if mask.any():
            parsed.loc[mask] = pd.to_datetime(df.loc[mask, 'Time'], format='%H:%M', errors='coerce')
        df['Time'] = parsed
        bad = df['Time'].isna().sum()
        if bad:
            print(f"Dropping {bad} rows with invalid 'Time'")
            df = df.dropna(subset=['Time'])
        df['Time'] = df['Time'].dt.time.apply(round_to_casual_time)

    if 'Room Type' in df.columns:
        df['Room Type'] = df['Room Type'].apply(standardize_room)
        df = df[df['Room Type'].notna() & (df['Room Type'] != '')]
        df = df[~df['Room Type'].isin(['PETRAS'])]

    if 'Admin' in df.columns:
        df['Admin'] = df['Admin'].apply(clean_text)
        df['Admin'] = df['Admin'].replace('', pd.NA).fillna(method='ffill').fillna('')

    if 'Revenue' in df.columns:
        df['Revenue'] = clean_price_series_City1(df['Revenue'], file_year)

    if 'Escape Time' in df.columns:
        df['Escape Time'] = df['Escape Time'].apply(clean_escape_time)

    if 'Helps' in df.columns:
        df['Helps'] = pd.to_numeric(df['Helps'], errors='coerce').fillna(0).astype(int)

    if 'Celebration' in df.columns:
        df['Celebration'] = df['Celebration'].fillna('Be šventės')
        def map_celebration(value):
            value_clean = str(value).strip()
            return celebration_mapping.get(value_clean, 'Be šventės')
        df['Celebration'] = df['Celebration'].apply(map_celebration)

    if 'Status' in df.columns:
        df['Status'] = df['Status'].fillna('Draugai').apply(
            lambda x: 'Draugai' if isinstance(x, str) and re.fullmatch(r'[\s,]*', x) else x
        )
        def map_status(value):
            value_clean = str(value).strip().lower()
            return status_mapping.get(value_clean, 'Kita')
        df['Status'] = df['Status'].apply(map_status)

    if 'Source' in df.columns:
        df['Source'] = df['Source'].fillna('INTERNETE').replace('', 'Internete')
        df['Source'] = df['Source'].apply(clean_source)

    if 'Age' in df.columns:
        df.rename(columns={'Age': 'Age'}, inplace=True)
    if 'Age' not in df.columns:
        df['Age'] = pd.NA

    age_cols = [col for col in df.columns if re.match(r'Unnamed: \d+', col)]
    for idx, col in enumerate(age_cols, 1):
        df.rename(columns={col: f'Age{idx}'}, inplace=True)
    age_columns = ['Age'] + [f'Age{i}' for i in range(1, len(age_cols)+1) if f'Age{i}' in df.columns]

    def extract_row_ages(row):
        ages = []
        for col in age_columns:
            val = row.get(col, '')
            if pd.isna(val) or str(val).strip() == '':
                continue
            match = re.search(r'\d+', str(val))
            if match:
                ages.append(int(match.group()))
        return ages

    row_age_values = df.apply(extract_row_ages, axis=1)
    df['Age Group'] = row_age_values.apply(lambda ages: categorize_age(ages[0]) if ages else "N/A")
    df['Age Group'] = df.apply(fill_missing_age_group, axis=1)
    df['TeamType'] = df.apply(assign_team_type, axis=1)

    column_order = [
        'Date', 'Time', 'Room Type', 'Revenue', 'Helps', 'Escape Time',
        'Age', 'Age1', 'Age2', 'Age3', 'Age4', 'Age5', 'Age6', 'Age7', 'Age Group', 'TeamType',
        'Source', 'Status', 'Celebration', 'Admin',
    ]
    column_order = [col for col in column_order if col in df.columns]
    df = df.reindex(columns=column_order, fill_value='')

    df.to_csv(output_path, index=False)
    print(f"Processed and saved: {output_path}")




def process_all_files(input_folder, output_folder, file_pattern="combined_data_*.csv"):
    '''Process all files matching pattern from input_folder and save cleaned versions to output_folder.'''
    os.makedirs(output_folder, exist_ok=True)

    input_paths = glob.glob(os.path.join(input_folder, file_pattern))
    if not input_paths:
        print("No files found matching pattern.")
        return

    for input_path in input_paths:
        base_name = os.path.basename(input_path)
        output_path = os.path.join(output_folder, f"City1_cleaned_{base_name}")
        process_file(input_path, output_path)

def merge_cleaned_files(cleaned_folder, output_path):
    '''
    Merge all cleaned CSV files from cleaned_folder into one DataFrame,
    aligning columns by union and filling missing columns with NaN.
    Save the merged DataFrame to output_path.
    '''
    files = glob.glob(os.path.join(cleaned_folder, "City1_cleaned_combined_data_*.csv"))
    if not files:
        print("No cleaned files found to merge.")
        return

    df_list = []
    for f in files:
        df = pd.read_csv(f, dtype=str)
        df_list.append(df)

    merged_df = pd.concat(df_list, axis=0, ignore_index=True, sort=False)

    merged_df.to_csv(output_path, index=False)
    print(f"Merged all cleaned files into {output_path}")



if __name__ == "__main__":

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_folder = os.path.join(BASE_DIR, "data", "City1", "merged_data")
    cleaned_folder = os.path.join(BASE_DIR, "data", "City1", "cleaned")
    merged_output_path = os.path.join(cleaned_folder, "City1_all_year.csv")

    os.makedirs(cleaned_folder, exist_ok=True)

    process_all_files(input_folder, cleaned_folder)

    merge_cleaned_files(cleaned_folder, merged_output_path)
