# Escape Room Data Analysis Project

### Project Description
This project analyzes escape room performance using synthetized and anonymized data from Vilnius and Kaunas.
Original data and concept required for dashboards is property of escape rooms called Break Free.
Although the data does not represent real values, the analytical logic and insights reflect realistic business scenarios.  
The dataset covers the years **2019–2025**.

---

### Project Structure
```
escape-room-project/
│
├── data/
│   └── sample_data_structure.csv
│
├── powerbi/
│   ├── EscapeRoom_Dashboard.pbix
│   └── screenshots/
│       ├── 01_main_dashboard.png
│       ├── 02_room_analysis.png
│       ├── 03_revenue_by_room.png
│       └── 04_admin_leaderboard.png
│
├── README.md
├── LICENSE
└── .gitignore
```

---

### Data Sources
The project uses synthetic copies of real escape room booking data.  
Source files originated from multiple Excel sheets with differing structures for Vilnius and Kaunas.

---

### Task 1: Data Extraction
**Goal:**  
Export all Excel sheets into separate CSV files.

**Process:**  
- Each Excel sheet converted to an individual CSV.  
- Different file structures between cities handled separately.  
- Year extracted from filenames using regex.

---

### Task 2: Data Cleaning
**Goal:**  
Standardize all datasets so they can be merged and used in Power BI.

**Cleaning Steps:**  
- Fix column names across all files.  
- Remove duplicates and invalid rows.  
- Standardize room names with a consistent mapping.  
- Normalize price values using regex extraction and default rules.  
- Parse escape times using `pandas.to_timedelta` and convert to minutes.  
- Round start times (“Laikas”) to one of six predefined time slots.  

---

### Task 3: Feature Engineering
**Goal:**  
Create unified categories for analysis.

**Steps:**  
- Consolidate source groups from 30 → 6.  
- Consolidate celebration categories from 14 → 5.  
- Create 7-level age group category from Age1–Age7 columns.  
- Derive TeamType based on age and room type.  
- Fill missing age groups where possible using business logic.

---

### Task 4: Process File Function
**Goal:**  
Apply full data cleaning pipeline to each CSV.

**Function Responsibilities:**  
- Read raw CSV  
- Extract year  
- Standardize room names  
- Clean text fields with regex  
- Normalize prices, times, and escape durations  
- Build AgeGroup and TeamType columns  
- Reorder all columns  
- Export cleaned file  

**Outputs:**  
- `clean_vilnius.csv`  
- `clean_kaunas.csv`

---

### Task 5: Data Merging
**Goal:**  
Combine cleaned Vilnius and Kaunas files into one unified dataset.

**Process:**  
- Align column names and formats  
- Remove rare or inconsistent values  
- Merge into final dataset for Power BI  

**Final Output:**  
`escape_rooms_2015_2025.csv`

---

### Power BI Analysis

**Goal:**  
Provide insights to support further growth of Escape rooms.

---

### Kids vs Grown Ups  
**Data explored:** 2019–2025  

**Findings:**  

![Kids vs Grown-up](insights/Kids_vs_Grown-up.png)

- The dominant age group is **10–13 years old**, indicating the need for escape rooms specifically designed for this segment.  
- **City 1** maintains a stable flow of approximately **32% kids** from total clients.  
- **City 2** shows inconsistent performance with **3–6% yearly variation** in kid-room demand compared to City 1.

![Kids vs Grown-up table zoomed](insights/Kids_vs_Grown-up_zoom.png)

These findings indicate a clear market opportunity for expanding offerings targeted at ages 10–13.

---

### Profitability and ROI

Based on the age group insights, the decision was made that future business growth requires a room designed for ages **10–13** in **City 2**.

Internal cost analyses (not included in the synthetic dataset but used for business decisions) indicated that the most profitable and quickest new room to establish would be **AV2**.

![Decision on kids room](insights/Kid_Room_Decision.png)

**Notes:**  
- AV1 already exists in City2.  
- AV2 offers the best balance between setup cost, build duration, and estimated demand.

**Next Steps:**  
Planning is underway for additional rooms targeted at ages 10–13 in City 2.

---

### Administrator Reward System  
**Period analyzed:** October 2025  

Retention and customer satisfaction improve significantly with high-quality administrative work.  
To support this, a monthly administrator reward program will be introduced.

![TOP admins](insights/TOP_Admins.png)

**Evaluation Metrics:**  
- **Room Count:** More rooms handled results in a higher score.  
- **Average Price:** Higher revenue per booking (larger groups) increases the score.  
- **Average Escape Time:** Extremely short escape times may indicate rushed service.  
- **Average Number of Hints:** Too many hints may suggest poor room management.

Administrators with the highest combined performance score will receive monthly recognition and incentives.

---

### City 1 – Room Development Opportunities  
**Data explored:** 2022–2025  

**Key Insights:**  
- **AS4** is the best-performing room with **779 entries (2025 YTD)**.  
- City 1 will open a new adult-oriented room modeled on AS4’s successful theme.  
- A concept from **City 2 (VS4)** with **356 entries (2025 YTD)** will be adapted for another new room in City 1.

![Both city popularity](insights/Both_City_Room_Popularity.png)

These results show strong opportunity for thematic expansion based on the best-performing rooms in both cities.

### License
Synthetic data used only for educational and analytical purposes.  
See `LICENSE` for details.
