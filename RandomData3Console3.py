import random
from pyrosm import OSM
import pandas as pd
from datetime import datetime

# Global variables
filePath = None
poisWithNameAddress = None
userNumber = None


def loadOsmFile():
    """Load and process the OSM file to extract POIs"""
    global filePath, poisWithNameAddress
    try:
        # Specify the path of the .osm.pbf file
        filePath = r"C:\Users\Abdulrahman Ali\Downloads\New folder\bremen-251008.osm.pbf"

        print(f"Loading file: {filePath}")

        # Create an OSM object
        osm = OSM(filePath)
        # print(osm)

        # Extract Points of Interest (POIs)
        pois = osm.get_pois()
        # print(pois)
        # if isinstance(pois, pd.DataFrame):
        #     pois.to_csv("pois.csv", index=False)
        # elif isinstance(pois, dict):
        #     pd.DataFrame([pois]).to_csv("pois.csv", index=False)
        # elif isinstance(pois, list):
        #     pd.DataFrame(pois).to_csv("pois.csv", index=False)
        # else:
        #     raise TypeError(f"Unexpected data type for pois: {type(pois)}")

        # Select the important columns
        poisSelected = pois[['name', 'amenity', 'shop', 'office', 'addr:housenumber', 'addr:street', 'geometry']].copy()

        # Merge the columns 'amenity' and 'shop' into a new column called 'category'
        poisSelected['category'] = poisSelected['amenity'].combine_first(poisSelected['shop'])

        # Delete the original columns (optional)
        poisSelected.drop(columns=['amenity', 'shop'], inplace=True)

        # Remove any rows that do not contain a category
        poisSelected = poisSelected[poisSelected['category'].notna()]

        # Create a new column for the full address (street + housenumber + ", Bremen")
        poisSelected['full_address'] = poisSelected.apply(
            lambda row: (
                f"{row['addr:street']} {row['addr:housenumber']}, Bremen"
                if pd.notna(row['addr:street']) and pd.notna(row['addr:housenumber'])
                else (f"{row['addr:street']}, Bremen" if pd.notna(row['addr:street']) else None)
            ),
            axis=1
        )

        # Filter places that have both a name and a complete address
        poisWithNameAddress = poisSelected[
            poisSelected['name'].notna() & poisSelected['full_address'].notna()
            ].copy()

        # Modify 'full_address' to also include the place name
        poisWithNameAddress.loc[:, 'full_address'] = poisWithNameAddress.apply(
            lambda row: f"{row['name']}, {row['full_address']}", axis=1
        )

        # Keep only the required columns
        poisWithNameAddress = poisWithNameAddress[['name', 'category', 'full_address']]

        print(f"File loaded successfully! Total POIs: {len(poisWithNameAddress)}")
        print('######################################################')

        return poisWithNameAddress

    except Exception as e:
        print(f"Error occurred: {e}")
        return None


def getRandomPlaces():
    """Function to select a user-specified number of random places"""
    global poisWithNameAddress, userNumber

    while True:
        try:
            userNumber = int(input("Enter how many places you want to display (positive number): "))
            if userNumber <= 0:
                print("Please enter a positive number.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter an integer number.")

    if userNumber > len(poisWithNameAddress):
        print(f"Only {len(poisWithNameAddress)} places available — showing all.")
        userNumber = len(poisWithNameAddress)

    print(f"\nDisplaying {userNumber} random places:")
    print('######################################################')

    # Select a number of rows equal to the user input
    randomSample = poisWithNameAddress.sample(n=userNumber, random_state=None)

    # Display the results
    print("\nResults:")
    print(randomSample)
    print('######################################################')

    # Save the results in a new CSV file with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    outputFile = f"user_random_{userNumber}_pois_{timestamp}.csv"
    randomSample.to_csv(outputFile, index=False)
    print(f"\nResults saved to file: {outputFile}")
    return randomSample


# Main execution
if __name__ == "__main__":
    # Load OSM file and process POIs
    poisWithNameAddress = loadOsmFile()

    if poisWithNameAddress is not None:
        # Get random places based on user input
        getRandomPlaces()