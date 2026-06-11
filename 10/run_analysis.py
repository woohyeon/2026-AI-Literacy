import pandas as pd
import os
import sys

# Set encoding for console output
sys.stdout.reconfigure(encoding='utf-8')

# Relative paths for data directory
data_dir = "./data"
file_sat = os.path.join(data_dir, "삶의_만족도_시도__20260606195059.xlsx")
file_sui = os.path.join(data_dir, "인구십만명당_자살률_시도_시_군_구__20260606194913.xlsx")

# Check if Excel files exist
if not os.path.exists(file_sat) or not os.path.exists(file_sui):
    print("Error: Excel files not found in './data' folder.")
    sys.exit(1)

# Load sheets
df_sat_raw = pd.read_excel(file_sat, sheet_name='데이터')
df_sui_raw = pd.read_excel(file_sui, sheet_name='데이터')

# 1. Clean Suicide Rate Data
sui_years = [2020, 2021, 2022, 2023, 2024]
sui_records = []

# Map region names to standard
def standardize_region(name):
    name = str(name).strip()
    if name == '전라북도':
        return '전북특별자치도'
    if name == '제주도':
        return '제주특별자치도'
    return name

# Skip row 0 (header row) and parse
for idx, row in df_sui_raw.iloc[1:].iterrows():
    region = standardize_region(row['행정구역별(1)'])
    if region == 'nan' or not region:
        continue
    
    # Each year has 3 columns: 계, 남자, 여자
    for i, year in enumerate(sui_years):
        col_base_idx = 1 + i * 3
        # Extract values
        val_total = pd.to_numeric(row.iloc[col_base_idx], errors='coerce')
        val_male = pd.to_numeric(row.iloc[col_base_idx + 1], errors='coerce')
        val_female = pd.to_numeric(row.iloc[col_base_idx + 2], errors='coerce')
        
        sui_records.append({
            'Region': region,
            'Year': year,
            'Suicide_Rate_Total': val_total,
            'Suicide_Rate_Male': val_male,
            'Suicide_Rate_Female': val_female
        })

df_sui_clean = pd.DataFrame(sui_records)

# 2. Clean Satisfaction Data
# Forward fill both region and 특성별(1) columns to fill merged cell NaNs
df_sat_raw['행정구역별(1)'] = df_sat_raw['행정구역별(1)'].ffill()
df_sat_raw['특성별(1)'] = df_sat_raw['특성별(1)'].ffill()

sat_records = []
sat_years = [2020, 2021, 2022, 2023, 2024]

for idx, row in df_sat_raw.iloc[1:].iterrows():
    region = standardize_region(row['행정구역별(1)'])
    cat1 = str(row['특성별(1)']).strip()
    cat2 = str(row['특성별(2)']).strip()
    
    if region == 'nan' or not region:
        continue
    
    # We only care about 전체 (Total) and 성별 (Gender)
    if cat1 == '전체' and cat2 == '계':
        gender = 'Total'
    elif cat1 == '성별' and cat2 in ['남자', '여자']:
        gender = cat2
    else:
        continue # Skip other demographics
        
    for i, year in enumerate(sat_years):
        col_base_idx = 3 + i * 6
        # Columns: 계, 매우 만족, 약간 만족, 보통, 약간 불만족, 매우 불만족
        very_sat = pd.to_numeric(row.iloc[col_base_idx + 1], errors='coerce')
        sat = pd.to_numeric(row.iloc[col_base_idx + 2], errors='coerce')
        neutral = pd.to_numeric(row.iloc[col_base_idx + 3], errors='coerce')
        unsat = pd.to_numeric(row.iloc[col_base_idx + 4], errors='coerce')
        very_unsat = pd.to_numeric(row.iloc[col_base_idx + 5], errors='coerce')
        
        # Calculate metrics
        sat_rate = very_sat + sat
        unsat_rate = very_unsat + unsat
        
        # Weighted score (5-point scale)
        avg_score = (very_sat * 5.0 + sat * 4.0 + neutral * 3.0 + unsat * 2.0 + very_unsat * 1.0) / 100.0
        
        sat_records.append({
            'Region': region,
            'Year': year,
            'Gender': gender,
            'Sat_Very': very_sat,
            'Sat_Somewhat': sat,
            'Sat_Neutral': neutral,
            'Unsat_Somewhat': unsat,
            'Unsat_Very': very_unsat,
            'Satisfaction_Rate': sat_rate,
            'Dissatisfaction_Rate': unsat_rate,
            'Avg_Satisfaction_Score': avg_score
        })

df_sat_clean = pd.DataFrame(sat_records)

# 3. Merge Data
sui_long_records = []
for idx, row in df_sui_clean.iterrows():
    # Total
    sui_long_records.append({
        'Region': row['Region'],
        'Year': row['Year'],
        'Gender': 'Total',
        'Suicide_Rate': row['Suicide_Rate_Total']
    })
    # Male
    sui_long_records.append({
        'Region': row['Region'],
        'Year': row['Year'],
        'Gender': '남자',
        'Suicide_Rate': row['Suicide_Rate_Male']
    })
    # Female
    sui_long_records.append({
        'Region': row['Region'],
        'Year': row['Year'],
        'Gender': '여자',
        'Suicide_Rate': row['Suicide_Rate_Female']
    })
df_sui_long = pd.DataFrame(sui_long_records)

# Merge
df_merged = pd.merge(df_sat_clean, df_sui_long, on=['Region', 'Year', 'Gender'], how='inner')

# Write output to local project folder
out_file = "./analysis_results.txt"

with open(out_file, "w", encoding="utf-8") as f:
    f.write("=== DATASET MERGED SUCCESSFUL ===\n")
    f.write(f"Merged Shape: {df_merged.shape}\n\n")
    
    # Filter out '전국' for regional analysis
    df_regional = df_merged[df_merged['Region'] != '전국'].copy()
    
    # 1. Overall correlation (excluding '전국')
    f.write("=== OVERALL CORRELATIONS (Regional data, 2020-2024 combined) ===\n")
    for gender in ['Total', '남자', '여자']:
        df_sub = df_regional[df_regional['Gender'] == gender]
        f.write(f"\nGender: {gender} (N={len(df_sub)})\n")
        corr_sat = df_sub['Satisfaction_Rate'].corr(df_sub['Suicide_Rate'])
        corr_unsat = df_sub['Dissatisfaction_Rate'].corr(df_sub['Suicide_Rate'])
        corr_score = df_sub['Avg_Satisfaction_Score'].corr(df_sub['Suicide_Rate'])
        
        f.write(f"  Corr(Satisfaction Rate, Suicide Rate): {corr_sat:.4f}\n")
        f.write(f"  Corr(Dissatisfaction Rate, Suicide Rate): {corr_unsat:.4f}\n")
        f.write(f"  Corr(Avg Satisfaction Score, Suicide Rate): {corr_score:.4f}\n")
        
    # 2. Year-by-year correlation (Gender = Total, excluding '전국')
    f.write("\n=== YEAR-BY-YEAR CORRELATIONS (Gender = Total) ===\n")
    df_tot = df_regional[df_regional['Gender'] == 'Total']
    for year in sorted(df_tot['Year'].unique()):
        df_year = df_tot[df_tot['Year'] == year]
        corr_score = df_year['Avg_Satisfaction_Score'].corr(df_year['Suicide_Rate'])
        corr_sat = df_year['Satisfaction_Rate'].corr(df_year['Suicide_Rate'])
        corr_unsat = df_year['Dissatisfaction_Rate'].corr(df_year['Suicide_Rate'])
        f.write(f"Year {year} (N={len(df_year)}):\n")
        f.write(f"  Avg Score vs Suicide Rate: {corr_score:.4f}\n")
        f.write(f"  Satisfaction Rate vs Suicide Rate: {corr_sat:.4f}\n")
        f.write(f"  Dissatisfaction Rate vs Suicide Rate: {corr_unsat:.4f}\n")
        
    # 3. Print sample of the merged data
    f.write("\n=== SAMPLE DATA (First 15 rows) ===\n")
    f.write(df_regional.head(15).to_string())
    f.write("\n")

print(f"Analysis complete. CSV saved to './merged_data.csv' and text output to './analysis_results.txt'")
df_merged.to_csv("./merged_data.csv", index=False, encoding='utf-8-sig')
