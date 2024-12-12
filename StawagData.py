import pandas as pd
import os
from datetime import datetime, timedelta, timezone
from geopy.geocoders import Nominatim
from geopy.geocoders import GeoNames
from geopy.point import Point
from geopandas.tools import geocode
import time
directory_path = r'C:\Users\Abdulrahman Ali\Downloads'
excel_file_name = 'STAWAG.xlsx'
excel_file_path = os.path.join(directory_path, excel_file_name)
df = pd.read_excel(excel_file_path)#Creating df with the original dataset
#changing the representaion of timestamps
df['Session begin (UTC)'] = pd.to_datetime(df['Session begin (UTC)'])
df['Session begin (UTC)'] = df['Session begin (UTC)'].dt.strftime("%Y-%m-%dT%H:%M:%S%z")
df['Session end (UTC)'] = pd.to_datetime(df['Session end (UTC)'])
df['Session end (UTC)'] = df['Session end (UTC)'].dt.strftime("%Y-%m-%dT%H:%M:%S%z")

#combining all the info for addresses in one unit
selected_columns = ['Street','Zipcode', 'City','Country']
new_df = df[selected_columns]

# Function to concatenate values of multiple columns
def concatenate_columns(row):
     return ','.join(str(value) for value in row)

# Apply concatenate_columns function to each row and store result in a new column
new_df['combined_column'] = new_df.apply(concatenate_columns, axis=1)
df.rename(columns={'House number': 'Address'}, inplace=True)
df['Address'] = new_df['combined_column']
df.drop('CPO', axis=1, inplace=True)
df.drop('Country', axis=1, inplace=True)
df.drop('City', axis=1, inplace=True)
df.rename(columns={'Zipcode': 'Longtude'}, inplace=True)
df.rename(columns={'Street': 'Latitude'}, inplace=True)
data = {
    'Adresses': [],
    'Longtude': [],
    'Latitude': [],
}

df_Add_Coor = pd.DataFrame(data)

counter=0
new_df['combined_column']=new_df['combined_column'].drop_duplicates()
for adress in new_df['combined_column']:
    if pd.notna(adress):  # Check if the value is not NaN
        location = geocode(adress, provider='nominatim', user_agent='xyz', timeout=10)
        print(counter,'-',adress)
        print(location)
        df_Add_Coor.loc[counter, 'Adresses'] = adress
        df_Add_Coor.loc[counter, 'Longtude'] = location.geometry.loc[0].x
        df_Add_Coor.loc[counter, 'Latitude'] = location.geometry.loc[0].y
        counter = counter + 1

    else:
        continue
df1=df_Add_Coor # just changing the df name
for index1, address1 in df.iterrows():
    for index2, address2 in df1.iterrows():
        if address1['Address'] == address2['Adresses']:#assining the addresses and locations
            df.at[index1, 'Longtude'] = df1.at[index2, 'Longtude']
            df.at[index1, 'Latitude'] = df1.at[index2, 'Latitude']
            break  # Exit the inner loop once a match is found
    else:
        continue  # Continue to the next iteration of the outer loop if no match is found
df.to_json('STAWAG_V2.json', orient='records')