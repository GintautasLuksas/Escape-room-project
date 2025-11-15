import pandas as pd
import os
import random

# --- Room mapping ---
ROOM_MAPPING = {
    # Vilnius S
    "UZ GROTU": "VS1", "XFAILAI": "VS2", "NEIMANOMA MISIJA": "VS3",
    "ALKATRASAS": "VS4", "KODAS BANKAS": "VS5",
    # Kaunas V
    "ALISA": "KV1", "SMEKLU PASLAPTYS": "KV2", "SLAPTA LABORATORIJA": "KV3",
    # Both V
    "APLEISTAS NAMAS": "AV1", "HARIS": "AV2",
    # Vilnius V
    "BANKO APIPLESIMAS": "VV1", "SLAPTAS KALEJIMAS": "VV2",
    "ATEIVIU KAMBARYS": "VV3", "APLEISTA LABORATORIJA": "VV4",
    "SLAPTIEJI AGENTAI": "VV5",
    # Both S
    "MAFIJA": "AS1", "MAFIJA2": "AS2", "APOKALIPSE": "AS3", "SERIJINIS ZUDIKAS": "AS4",
    # Kaunas S
    "DA VINCI": "KS1", "AKLAS APIPLESIMAS": "KS2",
}

AGE_SWAP = {
    "19–24": "25–29",
    "25–32": "19–24",
    "33–40": "30+",
    "41+": "30+"
}


SOURCE_MAP = {
    'BUVĘ PAS MUS': 'SRC1',
    'INTERNETE': 'SRC2',
    'KUPONAS': 'SRC3',
    'REKOMENDAVO': 'SRC4',
    'SOC TINKLAI': 'SRC5',
    'STOVYKLOS': 'SRC6'
}


STATUS_MAP = {
    'Draugai': 'GRP1',
    'Įmonė / Organizacija': 'GRP2',
    'Kolegos': 'GRP3',
    'Moksleiviai ir studentai': 'GRP4',
    'Kita': 'GRP5',
    'Šeimos': 'GRP6',
    'Šeima su draugais': 'GRP7',
    'Užsieniečiai': 'GRP8'
}



CELEB_MAP = {
    'Be šventės': 'EVT1',
    'Gimtadienis': 'EVT2',
    'Įmonės renginiai': 'EVT3',
    'Kitos šventės': 'EVT4',
    'Švietimo veiklos': 'EVT5'
}


AI_NAMES = [
    "Asta", "Rokas", "Egle", "Tomas", "Lina",
    "Marius", "Vaida", "Simonas", "Rasa", "Dainius",
    "Paulius", "Zenonas", "Akvilė", "Tauras", "Laimute"
]


random.seed()

def synthesize_data(input_path, output_path):
    df = pd.read_csv(input_path, dtype=str)

    # --- Remove 2018 entries ---
    if "Data" in df.columns:
        df = df[~df["Data"].astype(str).str.startswith("2018")]
        print(f"Removed 2018 entries. Remaining rows: {len(df)}")

    # --- Rename columns ---
    rename_map = {
        "Laikas": "Time",
        "Kambarys": "Room type",
        "Kaina": "Revenue",
        "Pagalbu_sk": "Helps",
        "Escape_laikas": "Escape Time",
        "Amžiaus grupė": "Age Group",
        "Saltinis": "Source",
        "Statusas": "Status",
        "Svente": "Celebration",
        "Darbuotojai": "Admin",
        "city": "City"
    }
    df.rename(columns=rename_map, inplace=True)

    # --- Room mapping ---
    df["Room type"] = df["Room type"].map(ROOM_MAPPING).fillna(df["Room type"])

    # --- Revenue +20 ---
    if "Revenue" in df.columns:
        df["Revenue"] = pd.to_numeric(df["Revenue"], errors="coerce").fillna(0)
        df["Revenue"] = df["Revenue"] + 20

    # --- Time adjustment (-1:30 hours) ---
    if "Time" in df.columns:
        def adjust_time(t):
            try:
                h, m = map(int, str(t).split(":")[:2])
                total_minutes = h * 60 + m - 90
                if total_minutes < 0:
                    total_minutes += 24 * 60
                h_new = total_minutes // 60
                m_new = total_minutes % 60
                return f"{h_new:02d}:{m_new:02d}"
            except:
                return t
        df["Time"] = df["Time"].apply(adjust_time)

    # --- Escape Time -8 minutes ---
    if "Escape Time" in df.columns:
        def adjust_escape_time(t):
            try:
                h, m = map(int, str(t).split(":")[:2])
                total_minutes = h * 60 + m - 8
                if total_minutes < 0:
                    total_minutes += 24 * 60
                h_new = total_minutes // 60
                m_new = total_minutes % 60
                return f"{h_new:02d}:{m_new:02d}"
            except:
                return t
        df["Escape Time"] = df["Escape Time"].apply(adjust_escape_time)

    # --- Age Group swap ---
    df["Age Group"] = df["Age Group"].replace(AGE_SWAP)

    # --- Source, Status, Celebration mapping ---
    df["Source"] = df["Source"].map(SOURCE_MAP).fillna(df["Source"])
    df["Status"] = df["Status"].map(STATUS_MAP).fillna(df["Status"])
    df["Celebration"] = df["Celebration"].map(CELEB_MAP).fillna(df["Celebration"])

    # --- Admin names (randomized) ---
    weights = [random.uniform(0.5, 3.0) for _ in AI_NAMES]  # some admins appear more
    df["Admin"] = [random.choices(AI_NAMES, weights=weights, k=1)[0] for _ in range(len(df))]

    # --- Drop unwanted columns ---
    drop_cols = ["Age", "Age1", "Age2", "Age3", "Age4", "Age5", "Age6", "Komentaras"]
    df.drop(columns=[c for c in drop_cols if c in df.columns], inplace=True)

    # --- City mapping ---
    df["City"] = df["City"].apply(lambda x: "City1" if str(x).upper() == "KAUNAS" else "City2" if str(x).upper() == "VILNIUS" else x)

    # --- Save output ---
    df.to_csv(output_path, index=False)
    print(f"Synthesized dataset saved to {output_path}")

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(BASE_DIR, "..", "data", "full_data.csv")
    output_file = os.path.join(BASE_DIR, "..", "data", "full_data_synth.csv")
    synthesize_data(input_file, output_file)
