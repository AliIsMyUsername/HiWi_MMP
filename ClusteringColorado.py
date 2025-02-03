import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Slider
import seaborn as sns
from matplotlib.ticker import FuncFormatter
from scipy.stats import linregress
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA


file_path = r'E:/HiWi/Datasets/Electric_Vehicle_Charging_Station_Data_-7419010956190451245.csv'
df = pd.read_csv(file_path)

def choppingNcleaning(df): #removes unnecessery data
    df = df.iloc[:, :-3]  # droping the the last 21 columns
    columns_to_drop = [df.columns[0]]+ [df.columns[2]]+ [df.columns[3]]+ [df.columns[6]]+ [df.columns[8]]  # First five, 7 and 8
    # # Drop the specified columns
    df = df.drop(columns=columns_to_drop, axis=1)

    df['Total Duration (minutes)'] = df['Total_Duration__hh_mm_ss_'].apply(hhmmss_to_minutes)
    df['Charging Time (minutes)'] = df['Charging_Time__hh_mm_ss_'].apply(hhmmss_to_minutes)
    # df.reset_index(drop=True, inplace=True)
    new_column_order = [
        'Address', 'Zip_Postal_Code', 'Start_Date___Time', 'End_Date___Time',
        'Total_Duration__hh_mm_ss_', 'Total Duration (minutes)', 'Charging_Time__hh_mm_ss_', 'Charging Time (minutes)', 'Energy__kWh_',
        'GHG_Savings__kg_', 'Gasoline_Savings__gallons_'
    ]

    # Reorder the columns
    df = df[new_column_order]
    # print("Current Columns:")
    # print(df.columns)
    # output_file = 'ColoradoDatasetCleaned.csv'
    # df.to_csv(output_file, index=False)
    # print(df)
    return df

def hhmmss_to_minutes(hhmmss): #changes the format of time into minutes only
    h, m, s = map(int, hhmmss.split(':'))
    return h * 60 + m + s / 60



df=choppingNcleaning(df)


# Select features for clustering
features = df[['Total Duration (minutes)', 'Charging Time (minutes)', 'Energy__kWh_']]

# Normalize the features
scaler = StandardScaler()
features_scaled = scaler.fit_transform(features)

# Determine the optimal number of clusters using the Elbow Method
inertia = []
for k in range(1, 10):
    kmeans = KMeans(n_clusters=k, random_state=42)
    kmeans.fit(features_scaled)
    inertia.append(kmeans.inertia_)

# Plot the Elbow curve
plt.figure(figsize=(8, 5))
plt.plot(range(1, 10), inertia, marker='o')
plt.title('Elbow Method for Optimal k')
plt.xlabel('Number of Clusters')
plt.ylabel('Inertia')
plt.show()

# Apply K-Means with chosen k (e.g., 3)
kmeans = KMeans(n_clusters=9, random_state=42)
df['Cluster'] = kmeans.fit_predict(features_scaled)

# Save the clustered dataset
# output_path = r'E:/HiWi/Datasets/clustered_ColoradoDataset.csv'
# df.to_csv(output_path, index=False)

# Display the first rows with clusters
# print(df.head())
# print(df.groupby('Cluster').mean())

plt.figure(figsize=(8, 5))
plt.scatter(df['Total Duration (minutes)'], df['Charging Time (minutes)'])
plt.title('Clusters of Charging Sessions')
plt.xlabel('Total Duration (minutes)')
plt.ylabel('Charging Time (minutes)')
plt.show()

# Visualize the clusters (using first two features as an example)
plt.figure(figsize=(8, 5))
plt.scatter(df['Total Duration (minutes)'], df['Charging Time (minutes)'], c=df['Cluster'], cmap='viridis')
plt.title('Clusters of Charging Sessions')
plt.xlabel('Total Duration (minutes)')
plt.ylabel('Charging Time (minutes)')
plt.show()



# Visualize Clusters (Latitude vs. Longitude)
plt.figure(figsize=(8, 6))
plt.scatter(df['Total Duration (minutes)'], df['Energy__kWh_'], c=df['Cluster'], cmap='viridis', s=50)
plt.title("Geographic Clusters of Charging Stations")
plt.xlabel("Total Duration (minutes)")
plt.ylabel("Energy__kWh_")
plt.show()

plt.figure(figsize=(8, 6))
plt.scatter(df['Charging Time (minutes)'], df['Energy__kWh_'], c=df['Cluster'], cmap='viridis', s=50)
plt.title("Geographic Clusters of Charging Stations")
plt.xlabel("Charging Time (minutes)")
plt.ylabel("Energy__kWh_")
plt.show()




pca = PCA(n_components=2)
features_2d = pca.fit_transform(features_scaled)

# Plot clusters
plt.scatter(features_2d[:, 0], features_2d[:, 1], c=df['Cluster'], cmap='viridis', s=50)
plt.xlabel('Principal Component 1')#PC1 points in the direction where the data varies the most.
plt.ylabel('Principal Component 2')#PC2 points in the second-best direction, orthogonal to PC1.
plt.title('Clusters Visualized in 2D (PCA)')
plt.show()

print(features_2d[:, 0])
print(features_2d[:, 1])