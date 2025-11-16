import os
import pandas as pd

'''Merge cleaned CSV files from two cities into one dataset.
    Adds a 'city' column to each entry, cleans column names,
    handles price and escape time, and prepares data for further analysis.'''


def merge_city_data(city1_path, city2_path, output_path):

    drop_columns = [
        'Extra1','Extra2','Extra3','Extra4','Extra5','Extra6',
        'Extra7','Extra8','Extra9','Extra10','Extra11','Extra12',
        'Extra13','Extra14','Age7'
    ]

    if not os.path.exists(city1_path) or not os.path.exists(city2_path):
        print("One or both input files do not exist.")
        return

    df1 = pd.read_csv(city1_path, dtype=str)
    df1["city"] = "City1"
    df1.drop(columns=[col for col in drop_columns if col in df1.columns], inplace=True)

    df2 = pd.read_csv(city2_path, dtype=str)
    df2["city"] = "City2"
    df2.drop(columns=[col for col in drop_columns if col in df2.columns], inplace=True)

    merged_df = pd.concat([df1, df2], ignore_index=True, sort=False)

    # Standardize column names
    merged_df.rename(columns={
        "OriginalPrice": "Price",
        "HelperCount": "Helpers",
        "EscapeTime": "EscapeTime",
        "SourceInfo": "Source",
        "TeamStatus": "Status",
        "Celebration": "Celebration",
        "Workers": "Staff",
        "Comments": "Notes"
    }, inplace=True)

    # Clean price column
    if "Price" in merged_df.columns:
        merged_df["Price"] = (
            merged_df["Price"]
            .fillna("")
            .str.replace("E","",regex=False)
            .str.strip()
        )
        merged_df["Price"] = pd.to_numeric(merged_df["Price"], errors="coerce").astype("Int64")

    if "EscapeTime" in merged_df.columns:
        merged_df["EscapeTime"] = merged_df["EscapeTime"].replace("-", pd.NA)

    if "Source" in merged_df.columns:
        merged_df["Source"] = merged_df["Source"].fillna("").str.strip().str.upper()
        counts = merged_df["Source"].value_counts()
        rare = counts[counts < 20].index
        merged_df.loc[merged_df["Source"].isin(rare), "Source"] = "ONLINE"
        merged_df.loc[merged_df["Source"] == "", "Source"] = "ONLINE"

    merged_df.drop_duplicates(inplace=True)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    merged_df.to_csv(output_path, index=False)
    print(f"Merged data saved to: {output_path}")


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    city1_file = os.path.join(BASE_DIR, "data", "city1", "cleaned", "city1_all.csv")
    city2_file = os.path.join(BASE_DIR, "data", "city2", "cleaned", "city2_all.csv")
    output_file = os.path.join(BASE_DIR, "data", "full_data.csv")

    print("City1 file exists:", os.path.exists(city1_file))
    print("City2 file exists:", os.path.exists(city2_file))

    merge_city_data(city1_file, city2_file, output_file)
