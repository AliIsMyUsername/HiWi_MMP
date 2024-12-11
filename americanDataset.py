import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Slider
import seaborn as sns
from matplotlib.ticker import FuncFormatter
from scipy.stats import linregress

# originally for 'ChargePoint Data CY20Q4'

# directory_path = r'E:\HiWi\Datasets'
# print(os.listdir(directory_path))
# excel_file_name = 'ElectricVehicleChargingStationUsageJuly2011Dec2020_2797601732187952259'
# excel_file_path = os.path.join(directory_path, excel_file_name)
# df_entireData = pd.read_excel(excel_file_path)
# excel_file = pd.ExcelFile(excel_file_path)
# df = pd.read_excel(excel_file_path)
# print(df.head())



# file_path = r'E:/HiWi/Datasets/ChargePoint Data CY20Q4.csv'
# df = pd.read_csv(file_path)
# df = df.iloc[:, :-21] #droping the the last 21 columns
# columns_to_drop = list(df.columns[:3]) + list(df.columns[4:8])  # First three (0, 1, 2) and (4, 7)
#
# # Drop the specified columns
# df = df.drop(columns=columns_to_drop, axis=1)
# output_file = 'ChargePoint Data CY20Q4_edited.csv'
# df.to_csv(output_file, index=False)
# print(df)
file_path = r'E:/HiWi/Datasets/American data/data_2020.csv'
df = pd.read_csv(file_path)

def hhmmss_to_minutes(hhmmss):
    h, m, s = map(int, hhmmss.split(':'))
    return h * 60 + m + s / 60

# # Ensure the date column is in datetime format
# df['Start Date'] = pd.to_datetime(df['Start Date'])  # Replace 'Date' with your actual column name
#
# # Extract the years present in the dataset
# years = df['Start Date'].dt.year.unique()
#
# # Create a dictionary to store DataFrames for each year
# yearly_dfs = {}
#
# # Split the DataFrame by year
# for year in years:
#     yearly_dfs[year] = df[df['Start Date'].dt.year == year]
#     print(f"Data for {year} contains {len(yearly_dfs[year])} rows.")
#     # Apply the conversion
#     yearly_dfs[year]['Total Duration (minutes)'] = yearly_dfs[year]['Total Duration (hh:mm:ss)'].apply(hhmmss_to_minutes)
#     yearly_dfs[year]['Charging Time (minutes)'] = yearly_dfs[year]['Charging Time (hh:mm:ss)'].apply(hhmmss_to_minutes)
#
#     # Save each year's DataFrame to a new CSV file (optional)
#     yearly_dfs[year].to_csv(f'data_{year}.csv', index=False)

# Display the result
# print(df)

# Plotting the two columns
plt.figure(figsize=(10, 8))
plt.plot(df.index, df['Total Duration (minutes)'], label='Total Duration (min)')
plt.plot(df.index, df['Charging Time (minutes)'], label='Charging Time (min)')

mean_y1 = np.mean(df['Total Duration (minutes)'])
plt.axhline(mean_y1, color='red', linestyle='--', label=f'Mean (y = {mean_y1:.2f})')

mean_y2 = np.mean(df['Charging Time (minutes)'])
plt.axhline(mean_y2, color='green', linestyle='--', label=f'Mean (y = {mean_y2:.2f})')

slope, intercept, _, _, _ = linregress(df.index, df['Total Duration (minutes)'])
trend_line = slope * df.index + intercept

# Plot trend line
plt.plot(df.index, trend_line, color='green', label='Trend Line')

# Adding labels, title, and legend
plt.xlabel('Charging event')
plt.ylabel('Time(min)')
plt.title('Comparison of Connection time and Charging time in 2020')
plt.legend()
plt.grid(True)

# Show the plot
plt.show()
