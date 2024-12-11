import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Slider
import seaborn as sns
from matplotlib.ticker import FuncFormatter
from scipy.stats import linregress


file_path = r'E:/HiWi/Datasets/Electric_Vehicle_Charging_Station_Data_-7419010956190451245.csv'
df = pd.read_csv(file_path)

def chopping(df): #removes unnecessery data
    df = df.iloc[:, :-4]  # droping the the last 21 columns
    columns_to_drop = list(df.columns[:5]) + [df.columns[6]]+ [df.columns[8]]  # First five, 7 and 8
    # # Drop the specified columns
    df = df.drop(columns=columns_to_drop, axis=1)
    # output_file = 'ChargePoint Data CY20Q4_edited.csv'
    # df.to_csv(output_file, index=False)
    # print(df)
    return df

def hhmmss_to_minutes(hhmmss): #changes the format of time into minutes only
    h, m, s = map(int, hhmmss.split(':'))
    return h * 60 + m + s / 60

def sortingByYear(df):
    # # Ensure the date column is in datetime format
    df['Start_Date___Time'] = pd.to_datetime(df['Start_Date___Time'])

    # # Extract the years present in the dataset
    years = df['Start_Date___Time'].dt.year.unique()
    #
    # Create a dictionary to store DataFrames for each year
    yearly_dfs = {}

    # Split the DataFrame by year
    for year in years:
        yearly_dfs[year] = df[df['Start_Date___Time'].dt.year == year].copy()
        print(f"Data for {year} contains {len(yearly_dfs[year])} rows.")
        # Apply the conversion
        yearly_dfs[year]['Total Duration (minutes)'] = yearly_dfs[year]['Total_Duration__hh_mm_ss_'].apply(hhmmss_to_minutes)
        yearly_dfs[year]['Charging Time (minutes)'] = yearly_dfs[year]['Charging_Time__hh_mm_ss_'].apply(hhmmss_to_minutes)
        yearly_dfs[year].reset_index(drop=True, inplace=True)


        # Save each year's DataFrame to a new CSV file (optional)
        # yearly_dfs[year]
        ploting(yearly_dfs[year],year)
        # yearly_dfs[year].to_csv(f'data_{year}.csv', index=False)


def ploting(yearlyDf,year):
    plt.figure(figsize=(10, 8))
    plt.plot(yearlyDf.index, yearlyDf['Total Duration (minutes)'], label='Total Duration (min)')
    plt.plot(yearlyDf.index, yearlyDf['Charging Time (minutes)'], label='Charging Time (min)')

    # mean_y1 = np.mean(df['Total Duration (minutes)'])
    # plt.axhline(mean_y1, color='red', linestyle='--', label=f'Mean (y = {mean_y1:.2f})')

    # mean_y2 = np.mean(df['Charging Time (minutes)'])
    # plt.axhline(mean_y2, color='green', linestyle='--', label=f'Mean (y = {mean_y2:.2f})')

    # slope, intercept, _, _, _ = linregress(df.index, df['Total Duration (minutes)'])
    # trend_line = slope * df.index + intercept

    # Plot trend line
    # plt.plot(df.index, trend_line, color='green', label='Trend Line')

    # Adding labels, title, and legend
    plt.xlabel('Charging event')
    plt.ylabel('Time(min)')
    plt.title('Comparison of Connection time and Charging time in '+ str(year))
    plt.legend()
    plt.grid(True)
    # Show the plot
    plt.show()

choppedDf=chopping(df)
sortingByYear(choppedDf)

