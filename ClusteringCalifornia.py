import pandas as pd
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt

# Load the dataset
file_path = r'E:/HiWi/Datasets/American data/ChargePoint Data CY20Q4.csv'
df = pd.read_csv(file_path)

# Convert 'hh:mm:ss' to minutes
def time_to_minutes(time_str):
    h, m, s = map(int, time_str.split(":"))
    return h * 60 + m + s / 60

df['Total Duration (minutes)'] = df['Total Duration (hh:mm:ss)'].apply(time_to_minutes)
df['Charging Time (minutes)'] = df['Charging Time (hh:mm:ss)'].apply(time_to_minutes)

# Select features for clustering
features = df[['Total Duration (minutes)', 'Charging Time (minutes)', 'Energy (kWh)',
               'GHG Savings (kg)', 'Gasoline Savings (gallons)', 'Latitude', 'Longitude']]

# Scale the features
scaler = StandardScaler()
features_scaled = scaler.fit_transform(features)

# K-Means Clustering
kmeans = KMeans(n_clusters=3, random_state=42)
df['Cluster'] = kmeans.fit_predict(features_scaled)

# Visualize Clusters (Latitude vs. Longitude)
plt.figure(figsize=(8, 6))
plt.scatter(df['Longitude'], df['Latitude'], c=df['Cluster'], cmap='viridis', s=50)
plt.title("Geographic Clusters of Charging Stations")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.show()

# Save clustered data
output_path = "clustered_CaliforniaDataset.csv"
df.to_csv(output_path, index=False)
print(df.groupby('Cluster').mean())

