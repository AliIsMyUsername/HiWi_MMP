import pandas as pd
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

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
features = df[['Total Duration (minutes)', 'Charging Time (minutes)', 'Energy (kWh)']]

# output_path = "CaliforniaDataset_cleaned.csv"
# df.to_csv(output_path, index=False)

# Scale the features
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

# K-Means Clustering
kmeans = KMeans(n_clusters=9, random_state=42)
df['Cluster'] = kmeans.fit_predict(features_scaled)

# # Visualize Clusters (Latitude vs. Longitude)
# plt.figure(figsize=(8, 6))
# plt.scatter(df['Longitude'], df['Latitude'], c=df['Cluster'], cmap='viridis', s=50)
# plt.title("Geographic Clusters of Charging Stations")
# plt.xlabel("Longitude")
# plt.ylabel("Latitude")
# plt.show()

# Save clustered data
# output_path = "clustered_CaliforniaDataset.csv"
# df.to_csv(output_path, index=False)
# print(df.groupby('Cluster').mean())

plt.figure(figsize=(8, 5))
plt.scatter(df['Total Duration (minutes)'], df['Charging Time (minutes)'])
plt.title('Data of Charging Sessions')
plt.xlabel('Total Duration (minutes)')
plt.ylabel('Charging Time (minutes)')
plt.show()



plt.figure(figsize=(8, 5))
plt.scatter(df['Total Duration (minutes)'], df['Charging Time (minutes)'], c=df['Cluster'], cmap='viridis')
plt.title('Clusters of Charging Sessions')
plt.xlabel('Total Duration (minutes)')
plt.ylabel('Charging Time (minutes)')
plt.show()


pca = PCA(n_components=2)
features_2d = pca.fit_transform(features_scaled)

# Plot clusters
plt.scatter(features_2d[:, 0], features_2d[:, 1], c=df['Cluster'], cmap='viridis', s=50)
plt.xlabel('Principal Component 1')#PC1 points in the direction where the data varies the most.
plt.ylabel('Principal Component 2')#PC2 points in the second-best direction, orthogonal to PC1.
plt.title('Clusters Visualized in 2D (PCA)')
plt.show()

# print(features_2d[:, 0])
# print(features_2d[:, 1])