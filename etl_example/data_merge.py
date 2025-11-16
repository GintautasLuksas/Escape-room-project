import os
import pandas as pd

'''This script merges multiple monthly CSV files into yearly datasets for each location.

- Loads CSVs listed per year for each city/location
- Forces the first column to become column named 'Date'
- Standardizes time-related column names to 'SessionDuration'
- Handles missing or empty CSVs without crashing
- Drops duplicate rows before saving
- Outputs final yearly CSVs into given location'''


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def read_csv_force_first_col_date(file_path):
    '''
    Load CSV and force first column to be a datetime named 'Date'.
    Handles empty files gracefully.
    '''
    if not os.path.exists(file_path):
        print(f"Missing file: {file_path}")
        return pd.DataFrame()

    df = pd.read_csv(file_path, dtype=str, encoding="utf-8")

    if df.empty:
        print(f"Empty file: {file_path}")
        return df

    first_col = df.columns[0]
    df.rename(columns={first_col: "Date"}, inplace=True)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    for col in df.columns:
        cleaned = col.lower().replace(" ", "")
        if cleaned in ["duration", "timeescaped", "sessionlength"]:
            df.rename(columns={col: "Escape Time"}, inplace=True)

    return df


def combine_yearly_csvs(input_dir, file_dict, output_dir):

    '''Combine multiple monthly CSV files into a single yearly CSV.'''
    os.makedirs(output_dir, exist_ok=True)

    for year, file_list in file_dict.items():
        combined = []
        ok_files = []
        bad_files = []

        for filename in file_list:
            file_path = os.path.join(input_dir, filename)
            df = read_csv_force_first_col_date(file_path)

            if not df.empty:
                combined.append(df)
                ok_files.append(filename)
            else:
                bad_files.append(filename)

        output_file = os.path.join(output_dir, f"combined_{year}.csv")

        if combined:
            final_df = pd.concat(combined, ignore_index=True)
            final_df.drop_duplicates(inplace=True)
            final_df.to_csv(output_file, index=False, encoding="utf-8")
            print(f"Year {year}: saved {output_file}")
        else:
            pd.DataFrame().to_csv(output_file, index=False, encoding="utf-8")
            print(f"Year {year}: no data, created empty file")

        print(f"--- {year} Summary ---")
        print(f"Included: {ok_files}")
        print(f"Missing: {bad_files}\n")


def main():
    # Location A
    input_a = os.path.join(BASE_DIR, "data", "loc_a", "extracted")
    output_a = os.path.join(BASE_DIR, "data", "loc_a", "merged")

    files_a = {
        2021: ["month01_a.csv", "month02_a.csv", "month03_a.csv"],
        2022: ["month01_a.csv", "month02_a.csv", "month03_a.csv"],
        2023: ["month01_a.csv", "month02_a.csv", "month03_a.csv"],
        2024: ["month01_a.csv", "month02_a.csv", "month03_a.csv"],
    }

    combine_yearly_csvs(input_a, files_a, output_a)

    # Location B
    input_b = os.path.join(BASE_DIR, "data", "loc_b", "extracted")
    output_b = os.path.join(BASE_DIR, "data", "loc_b", "merged")

    files_b = {
        2021: ["month01_b.csv", "month02_b.csv", "month03_b.csv"],
        2022: ["month01_b.csv", "month02_b.csv", "month03_b.csv"],
        2023: ["month01_b.csv", "month02_b.csv", "month03_b.csv"],
        2024: ["month01_b.csv", "month02_b.csv", "month03_b.csv"],
    }

    combine_yearly_csvs(input_b, files_b, output_b)


if __name__ == "__main__":
    main()
