import pandas as pd
import re
import unicodedata
import os
import glob
from datetime import datetime, timedelta
import unidecode

'''This script cleans and standatise the data and merges into one City1 file with full data'''


DEFAULT_PRICES = {
    2018: "30",
    2019: "30",
    2020: "40",
    2021: "40",
    2022: "50",
    2023: "50",
    2024: "50",
    2025: "90",
    2026: "100"
}

DEFAULT_GROUPS = {
    'Family': ['Family', 'Multiple families'],
    'Friends & Family': ['Friends & Family'],
    'Students': ['Students', 'School students'],
    'Foreigners': ['Foreigners'],
    'Colleagues': ['Colleagues'],
    'Organization': ['Organization'],
    'Friends': ['Friends']
}

status_mapping = {}
for main_group, sub_groups in DEFAULT_GROUPS.items():
    for subgroup in sub_groups:
        normalized = subgroup.strip().lower()
        status_mapping[normalized] = main_group

status_mapping['students / school'] = 'Students'

CELEBRATION_GROUPS = {
    'Birthday': ['Birthday'],
    'Company event': ['Company', 'Team building'],
    'Other events': ['Other celebration', 'Stag/Bachelorette'],
    'Educational': ['Excursion', 'Camp'],
    'None': ['No celebration']
}

celebration_mapping = {}
for main_group, sub_groups in CELEBRATION_GROUPS.items():
    for subgroup in sub_groups:
        key = subgroup.strip()
        celebration_mapping[key] = main_group

GROUP_KEYWORDS = {
    "ONLINE": [r"\bINTERNET", r"\bGOOGLE\b", r"\bWWW\b"],
    "RETURNING": [r"\bRETURNED\b"],
    "COUPON": [r"\bCOUPON", r"\bGIFT"],
    "REFERRED": [r"REFERRED", r"FRIENDS"],
    "SOCIAL MEDIA": [r"\bFACEBOOK\b", r"\bINSTAGRAM\b", r"\bTIKTOK\b"],
    "CAMPS": [r"\bCAMP\b"]
}

def categorize_age(age):
    try:
        age = int(age)
    except:
        return "N/A"

    if 7 <= age <= 9: return "7–9"
    elif 10 <= age <= 13: return "10–13"
    elif 14 <= age <= 18: return "14–17"
    elif 19 <= age <= 24: return "18–24"
    elif 25 <= age <= 29: return "25–29"
    elif 30 <= age <= 40: return "30–40"
    elif age >= 41: return "41+"
    return "N/A"

def fill_missing_age_group(row):
    if row['AgeGroup'] != "N/A":
        return row['AgeGroup']

    room = row['Room']
    if room in ["Room1", "Room2"]:
        return "7–9"
    elif room in ["Room3", "Room4"]:
        return "10–13"
    else:
        return "25–29"

def assign_team_type(row):
    kids_rooms = {"Room3", "Room4"}
    adult_rooms = {"Room5", "Room6"}
    conditional_rooms = {"Room1", "Room2"}

    room = row['Room']
    age_group = row['AgeGroup']

    if room in kids_rooms:
        return "Kids"
    elif room in adult_rooms:
        return "Adults"
    elif room in conditional_rooms:
        if age_group in ["7–9", "10–13"]:
            return "Kids"
        else:
            return "Adults"
    else:
        return "Unknown"

def clean_source(text: str) -> str:
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
    return best_match.strftime('%H:%M') if best_match else None

def clean_text(text):
    if pd.isna(text):
        return ""
    text = text.upper()
    text = ''.join((c if not unicodedata.combining(c) else '') for c in unicodedata.normalize('NFKD', text))
    return re.sub(r'[^A-Z0-9 ]', '', text).strip()

def clean_price_series(price_series: pd.Series, file_year: int) -> pd.Series:
    default_price_str = DEFAULT_PRICES.get(file_year, "30")
    default_price = int(re.search(r'\d+', default_price_str).group())
    values = price_series.fillna("").astype(str).str.upper().tolist()
    cleaned = []
    i = 0
    n = len(values)
    while i < n:
        val = values[i].strip()
        matches = re.findall(r'\d+', val)
        valid_matches = [int(m) for m in matches if 30 <= int(m) <= 600]
        if valid_matches:
            total_price = valid_matches[0]
            j = i + 1
            empty_count = 0
            while j < n and values[j].strip() in ["", "NO_PRICE", "NAN"]:
                empty_count += 1
                j += 1
            block_size = 1 + empty_count
            leftover = max(total_price - default_price * empty_count, default_price)
            cleaned.append(f"{leftover}")
            for _ in range(empty_count):
                cleaned.append(f"{default_price}")
            i += block_size
            continue
        coupon_keywords = ["COUPON", "GIFT"]
        if any(k in val for k in coupon_keywords):
            cleaned.append(f"{default_price}")
            i += 1
            continue
        cleaned.append(f"{default_price}")
        i += 1
    return pd.Series(cleaned, index=price_series.index)

def clean_escape_time(value):
    if pd.isna(value):
        return "-"
    value_str = str(value).strip()
    try:
        td = pd.to_timedelta(value_str)
        return round(td.total_seconds() / 60, 2)
    except Exception:
        return "-"

def normalize_text(text) -> str:
    if not isinstance(text, str):
        return ''
    text = text.strip().upper()
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    return text

def standardize_room(value) -> str:
    mapping = {
        "Room1": ["Alias1", "Alias2"],
        "Room2": ["Alias3", "Alias4"],
        "Room3": ["Room3"],
        "Room4": ["Room4"],
        "Room5": ["Room5"],
        "Room6": ["Room6"]
    }
    normalized_value = normalize_text(value)
    for standard_name, aliases in mapping.items():
        normalized_aliases = [normalize_text(alias) for alias in aliases]
        if normalized_value == normalize_text(standard_name) or normalized_value in normalized_aliases:
            return standard_name
    return None

def filter_rooms(room_list):
    allowed_rooms = {"Room1", "Room2", "Room3", "Room4", "Room5", "Room6"}
    standardized = [standardize_room(room) for room in room_list]
    return [room for room in standardized if room in allowed_rooms]


