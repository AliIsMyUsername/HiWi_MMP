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
    print(df)
    return df

chopping(df)
print(df)