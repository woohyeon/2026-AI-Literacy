import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np

# Load the merged dataset from the local directory
csv_path = "./merged_data.csv"
if not os.path.exists(csv_path):
    print("Error: 'merged_data.csv' not found. Please run 'run_analysis.py' first.")
    import sys
    sys.exit(1)

df = pd.read_csv(csv_path)

# Set Matplotlib settings for Korean font
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# ==============================================================================
# Plot 1: National Trend Comparison (Gender = Total)
# ==============================================================================
df_national = df[df['Region'] == '전국'].copy()
df_nat_total = df_national[df_national['Gender'] == 'Total'].sort_values('Year')

fig, ax1 = plt.subplots(figsize=(8, 5))

color = '#1f77b4'
ax1.set_xlabel('연도 (Year)', fontsize=12, labelpad=10)
ax1.set_ylabel('자살률 (인구 10만 명당)', color=color, fontsize=12)
line1 = ax1.plot(df_nat_total['Year'], df_nat_total['Suicide_Rate'], color=color, marker='o', linewidth=2.5, label='전국 자살률')
ax1.tick_params(axis='y', labelcolor=color)
ax1.set_xticks(df_nat_total['Year'])

ax2 = ax1.twinx()  
color = '#e377c2'
ax2.set_ylabel('삶의 만족도 평균 (5점 만점)', color=color, fontsize=12)
line2 = ax2.plot(df_nat_total['Year'], df_nat_total['Avg_Satisfaction_Score'], color=color, marker='s', linewidth=2.5, linestyle='--', label='삶의 만족도 평균')
ax2.tick_params(axis='y', labelcolor=color)

# Combine legends
lines = line1 + line2
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='upper left')

plt.title('전국 삶의 만족도 평균과 자살률 추이 (2020-2024)', fontsize=14, fontweight='bold', pad=15)
fig.tight_layout()
plt.savefig("./national_trends.png", dpi=200)
plt.close()

# ==============================================================================
# Plot 2: Scatter Plot of Satisfaction Rate vs Suicide Rate (Regional data, Gender = Total)
# ==============================================================================
df_regional = df[df['Region'] != '전국'].copy()
df_reg_total = df_regional[df_regional['Gender'] == 'Total'].dropna(subset=['Satisfaction_Rate', 'Suicide_Rate'])

plt.figure(figsize=(9, 6))
x = df_reg_total['Satisfaction_Rate'].values
y = df_reg_total['Suicide_Rate'].values

# Scatter points
plt.scatter(x, y, alpha=0.6, color='#2ca02c', s=80, label='지역별 연도별 데이터')

# Fit regression line
coef = np.polyfit(x, y, 1)
poly1d_fn = np.poly1d(coef)
x_sorted = np.sort(x)
plt.plot(x_sorted, poly1d_fn(x_sorted), color='#ff7f0e', linewidth=2.5, label=f'선형 회귀선 (r = -0.1704)')

# Annotate outliers for 2024
df_2024 = df_reg_total[df_reg_total['Year'] == 2024]
for idx, row in df_2024.iterrows():
    if row['Suicide_Rate'] > 33 or row['Satisfaction_Rate'] < 20 or row['Satisfaction_Rate'] > 50:
        plt.annotate(f"{row['Region']}(24)", (row['Satisfaction_Rate'], row['Suicide_Rate']),
                     textcoords="offset points", xytext=(0,5), ha='center', fontsize=9, fontweight='bold')

plt.title('지역별 삶의 만족도(만족 비율)와 자살률 상관관계 (2020-2024)', fontsize=14, fontweight='bold', pad=15)
plt.xlabel('삶의 만족도 비율 (%) - 매우만족 + 약간만족', fontsize=12)
plt.ylabel('자살률 (인구 10만 명당)', fontsize=12)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.savefig("./regional_correlation_scatter.png", dpi=200)
plt.close()

# ==============================================================================
# Plot 3: Gender Comparison (Male vs Female) Scatter Plot
# ==============================================================================
df_gender = df_regional[df_regional['Gender'].isin(['남자', '여자'])].dropna(subset=['Satisfaction_Rate', 'Suicide_Rate'])

plt.figure(figsize=(10, 6))
colors = {'남자': '#1f77b4', '여자': '#ff7f0e'}
markers = {'남자': 'o', '여자': 's'}

for gender in ['남자', '여자']:
    df_sub = df_gender[df_gender['Gender'] == gender]
    gx = df_sub['Satisfaction_Rate'].values
    gy = df_sub['Suicide_Rate'].values
    
    # Scatter points
    plt.scatter(gx, gy, alpha=0.6, color=colors[gender], marker=markers[gender], s=80, label=f'{gender} 데이터')
    
    # Fit regression line
    coef_g = np.polyfit(gx, gy, 1)
    poly1d_fn_g = np.poly1d(coef_g)
    gx_sorted = np.sort(gx)
    
    r_val = df_sub['Satisfaction_Rate'].corr(df_sub['Suicide_Rate'])
    plt.plot(gx_sorted, poly1d_fn_g(gx_sorted), color=colors[gender], linewidth=2.5, 
             linestyle='-' if gender=='남자' else '--', label=f'{gender} 회귀선 (r = {r_val:.4f})')

plt.title('성별에 따른 삶의 만족도 비율과 자살률 상관관계 (2020-2024)', fontsize=14, fontweight='bold', pad=15)
plt.xlabel('삶의 만족도 비율 (%)', fontsize=12)
plt.ylabel('자살률 (인구 10만 명당)', fontsize=12)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.savefig("./gender_correlation_scatter.png", dpi=200)
plt.close()

# ==============================================================================
# Plot 4: Correlation Matrix Heatmap
# ==============================================================================
cols_for_corr = ['Suicide_Rate', 'Avg_Satisfaction_Score', 'Satisfaction_Rate', 'Dissatisfaction_Rate', 
                 'Sat_Very', 'Sat_Somewhat', 'Sat_Neutral', 'Unsat_Somewhat', 'Unsat_Very']
corr_matrix = df_regional[df_regional['Gender'] == 'Total'][cols_for_corr].corr()

korean_labels = {
    'Suicide_Rate': '자살률',
    'Avg_Satisfaction_Score': '평균 만족도 점수',
    'Satisfaction_Rate': '만족 비율',
    'Dissatisfaction_Rate': '불만족 비율',
    'Sat_Very': '매우 만족',
    'Sat_Somewhat': '약간 만족',
    'Sat_Neutral': '보통',
    'Unsat_Somewhat': '약간 불만족',
    'Unsat_Very': '매우 불만족'
}
corr_matrix.rename(index=korean_labels, columns=korean_labels, inplace=True)

fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(corr_matrix.values, cmap='coolwarm', vmin=-1, vmax=1)

cbar = ax.figure.colorbar(im, ax=ax)
cbar.ax.set_ylabel("상관계수 (r)", rotation=-90, va="bottom")

ax.set_xticks(np.arange(len(corr_matrix.columns)))
ax.set_yticks(np.arange(len(corr_matrix.index)))
ax.set_xticklabels(corr_matrix.columns, rotation=45, ha="right", rotation_mode="anchor")
ax.set_yticklabels(corr_matrix.index)

for i in range(len(corr_matrix.index)):
    for j in range(len(corr_matrix.columns)):
        val = corr_matrix.values[i, j]
        text = ax.text(j, i, f"{val:.2f}",
                       ha="center", va="center", color="black" if abs(val) < 0.5 else "white",
                       fontweight='bold')

plt.title('삶의 만족도 상세 항목 및 자살률 상관관계 히트맵 (2020-2024)', fontsize=14, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig("./correlation_matrix_heatmap.png", dpi=200)
plt.close()

# ==============================================================================
# Plot 5: Regional Suicide Rate Ranking & Satisfaction Comparison (2024)
# ==============================================================================
df_reg_total_2024 = df_regional[(df_regional['Gender'] == 'Total') & (df_regional['Year'] == 2024)].copy()
df_ranked = df_reg_total_2024.sort_values('Suicide_Rate', ascending=True)

fig, ax1 = plt.subplots(figsize=(12, 7))
y_pos = np.arange(len(df_ranked))
width = 0.35

rects1 = ax1.barh(y_pos - width/2, df_ranked['Suicide_Rate'], width, color='#d62728', alpha=0.85, label='자살률 (10만명당)')
ax1.set_xlabel('자살률 (인구 10만 명당)', color='#d62728', fontsize=12)
ax1.tick_params(axis='x', labelcolor='#d62728')
ax1.set_yticks(y_pos)
ax1.set_yticklabels(df_ranked['Region'], fontsize=10, fontweight='bold')

ax2 = ax1.twiny()
rects2 = ax2.barh(y_pos + width/2, df_ranked['Satisfaction_Rate'], width, color='#1f77b4', alpha=0.75, label='삶의 만족 비율 (%)')
ax2.set_xlabel('삶의 만족 비율 (%)', color='#1f77b4', fontsize=12)
ax2.tick_params(axis='x', labelcolor='#1f77b4')

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='lower right')

plt.title('2024년 시도별 자살률 순위 및 삶의 만족 비율 비교', fontsize=14, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig("./regional_suicide_ranking_2024.png", dpi=200)
plt.close()

# ==============================================================================
# Plot 6: Satisfaction Profile Stacked Bar Chart (2024)
# ==============================================================================
df_profile = df_reg_total_2024.sort_values('Avg_Satisfaction_Score', ascending=True)

regions = df_profile['Region'].values
very_sat = df_profile['Sat_Very'].values
sat = df_profile['Sat_Somewhat'].values
neutral = df_profile['Sat_Neutral'].values
unsat = df_profile['Unsat_Somewhat'].values
very_unsat = df_profile['Unsat_Very'].values

colors_stack = ['#2ca02c', '#98df8a', '#d3d3d3', '#ffbb78', '#ff7f0e']
labels_stack = ['매우 만족', '약간 만족', '보통', '약간 불만족', '매우 불만족']

fig, ax = plt.subplots(figsize=(12, 7))

b1 = ax.bar(regions, very_sat, color=colors_stack[0], label=labels_stack[0])
b2 = ax.bar(regions, sat, bottom=very_sat, color=colors_stack[1], label=labels_stack[1])
b3 = ax.bar(regions, neutral, bottom=very_sat+sat, color=colors_stack[2], label=labels_stack[2])
b4 = ax.bar(regions, unsat, bottom=very_sat+sat+neutral, color=colors_stack[3], label=labels_stack[3])
b5 = ax.bar(regions, very_unsat, bottom=very_sat+sat+neutral+unsat, color=colors_stack[4], label=labels_stack[4])

ax.set_ylabel('비율 (%)', fontsize=12)
ax.set_xlabel('지역 (평균 만족도 점수 순 정렬)', fontsize=12, labelpad=10)
plt.xticks(rotation=45, ha='right')
ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left')

plt.title('2024년 지역별 삶의 만족도 답변 분포 비율 (평균 점수 오름차순)', fontsize=14, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig("./satisfaction_profile_2024.png", dpi=200)
plt.close()

print("All plots successfully generated and saved to current directory.")
