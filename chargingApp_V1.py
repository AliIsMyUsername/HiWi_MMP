from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import traceback
import pandas as pd
from selenium.webdriver.chrome.options import Options
import random
import numpy as np
import tkinter as tk
from geopandas.tools import geocode
from math import radians, sin, cos, sqrt, atan2
# import webview
import webbrowser
# import herepy
import requests
from datetime import datetime




root = tk.Tk()
root.title("Charging Station App")

root.state('zoomed')
lat=None
long=None
conType=None
preference=None
timePreference=None
destination=None
# allows the user to enter an address and it returns the coordinates lat and long
def get_location():
    global lat, long, destination
    try:
        address = str(entry.get())
        destination = address
        address_label0.config(text=f"You entered: {address}")
        location = geocode(address, provider='nominatim', user_agent='xyz', timeout=10)
        address_label1.config(text=f"Latitude: {location.geometry.loc[0].y}")
        address_label2.config(text=f"Longtude: {location.geometry.loc[0].x}")
        lat = location.geometry.loc[0].y
        long =location.geometry.loc[0].x
    except ValueError:
        address_label0.config(text="Please enter a valid address.")


entry = tk.Entry(root)
entry.pack(pady=10)
submit_button = tk.Button(root, text="Submit Address", command=get_location)
submit_button.pack()

address_label0 = tk.Label(root, text="")
address_label0.pack()

address_label1 = tk.Label(root, text="")
address_label1.pack()

address_label2 = tk.Label(root, text="")
address_label2.pack()
##########################################

# allows the user to enter the connection type
def show_selection():
    global conType
    selected = selected_optionConnection.get()
    if selected == "Select connection type":
        dropMenu_labelConnection.config(text="Please select a valid option.")
    else:
        dropMenu_labelConnection.config(text=f"You selected: {selected}")
        conType=selected


connectionOptions = ["Select connection type","Type 2", "Combo", "CHAdeMO","MennekesCOMBO"]
selected_optionConnection = tk.StringVar(value=connectionOptions[0])

dropdownConnection = tk.OptionMenu(root, selected_optionConnection, *connectionOptions)
dropdownConnection.pack(pady=10)

buttonSelection = tk.Button(root, text="Submit connection type", command=show_selection)
buttonSelection.pack()
dropMenu_labelConnection = tk.Label(root, text="")
dropMenu_labelConnection.pack()
############################################


def show_preference():
    global preference
    selected = selected_optionPreference.get()
    if selected == "Select search preference":
        dropMenu_labelPrefrence.config(text="Please select a valid option.")
    else:
        dropMenu_labelPrefrence.config(text=f"You selected: {selected}")
        preference=selected

preferenceOptions = ["Select search preference","Distance over price", "Price over distance"]
selected_optionPreference = tk.StringVar(value=preferenceOptions[0])

dropdownPreference = tk.OptionMenu(root, selected_optionPreference, *preferenceOptions)
dropdownPreference.pack(pady=10)

buttonPrefrence = tk.Button(root, text="Submit search preference", command=show_preference)
buttonPrefrence.pack()
dropMenu_labelPrefrence = tk.Label(root, text="")
dropMenu_labelPrefrence.pack()
############################################

def show_time_preference():
    global timePreference
    selected = selected_optionTimePreference.get()
    if selected == "Select time preference":
        dropMenu_labelTimePrefrence.config(text="Please select a valid option.")
    else:
        dropMenu_labelTimePrefrence.config(text=f"You selected: {selected}")
        timePreference=selected

timepreferenceOptions = ["Select time preference","I have enough time", "I am in a hurry"]
selected_optionTimePreference = tk.StringVar(value=timepreferenceOptions[0])

dropdownTimePreference = tk.OptionMenu(root, selected_optionTimePreference, *timepreferenceOptions)
dropdownTimePreference.pack(pady=10)

buttonTimePrefrence = tk.Button(root, text="Submit time preference", command=show_time_preference)
buttonTimePrefrence.pack()
dropMenu_labelTimePrefrence = tk.Label(root, text="")
dropMenu_labelTimePrefrence.pack()
############################################

def show_input():
    if lat is not None and long is not None and conType is not None:
        # print_location(lat, long, conType)
        best,lat1,lon1=optimiser_WSM()
        # Convert the best row to a string
        best_text = best.to_string()
        result_label.config(text="Best option:\n" + best_text)
        root.update_idletasks()
        show_map(lat1, lon1)


    else:
        print("enter connection and address first")



showInput_button = tk.Button(root, text="Find a charging station", command=show_input)
showInput_button.pack(pady=10)

showInput_label = tk.Label(root, text="")
showInput_label.pack()

result_label = tk.Label(root, text="", justify='left', font=("Arial", 12))
result_label.pack(padx=10, pady=10)

# address_label0 = tk.Label(root, text="")
# address_label0.pack()
#
# address_label1 = tk.Label(root, text="")
# address_label1.pack()
#
# address_label2 = tk.Label(root, text="")
# address_label2.pack()

# def print_location(lat,long,conType):
#     print(lat)
#     print(long)
#     print(conType)

def ladekarte():
    # to make the browser invasible
    options = Options()
    options.add_argument("--headless")
    # using webdrivermamager there's no need to download and install chrome driver
    service = Service(ChromeDriverManager().install())
    # driver = webdriver.Chrome(service=service, options=options)#invasible
    driver = webdriver.Chrome(service=service)  # vasible
    columns = ["Address", "Availability", "Charging rate", "Power", "Current type", "Connection type", "Price"]
    outputDF = pd.DataFrame(columns=columns)


    path = "https://driver.chargepoint.com/mapCenter/" + str(lat) + "/" + str(long) + "/15?view=list"
    driver.get(path)
    # Maximaize the opend window to ensure a bigger objects list
    driver.maximize_window()

    try:

        xPathStations= '//div[@class="sc-gFqAkR sc-dAbbOL sc-duAPit dcOspJ kHQqqq joWlqH"]' # xpath of the buttons of eachc harging station
        xPathInfoPrice = '//div[@data-accordion-component="AccordionItemHeading"]' #//div[@data-accordion-component="AccordionItemHeading"]
        xPathAddress = '//div[@class="sc-gFqAkR sc-dAbbOL dcOspJ kHQqqq"]'
        xPathAvialability = '//div[@class="sc-gFqAkR sc-fUnMCh sc-kTbCBX dcOspJ gxCHVP cyCmrT"]'
        xPathRate = '//div[@class="sc-leQnM gTwmVa"]' #charge rate, power and type acdc
        xPathPower = '//div[@class="sc-fPXMVe sc-dYoqmx gdLKmB jyAqvx"]' #acdc and connection type
        xPathPriceDirect = '//div[@class="sc-gNXrtx jBCTjX"]'
        xPathPrice = '//div[@class="sc-cyRcrZ celkDu"]'
        xPathBackButton= '//span[@class="sc-gpaZuh gavyXh"]'

        # Wait up to 20 seconds for the charging station list to be visible
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located(
                (By.XPATH, xPathStations))
            # same xpath of the chargingstations, just waiting for it to appeare
        )
        # buttonsLocation = driver.find_elements(By.XPATH,'//button[@class="sc-aXZVg ciuTTg link sc-fnLEGM jOGWNJ"]')  # a way to automatically get the user's location
        # buttonsLocation[0].click()
        # buttonsShare = driver.find_elements(By.XPATH,
        #                                '//button[@class="sc-aXZVg ciuTTg primary"]')  # needed only for the first element in the loop
        # buttonsShare[0].click()
        # Get all the charging stations
        allChargStation = driver.find_elements(By.XPATH,xPathStations)
        size = len(allChargStation)
        print(f"Number of charging stations found: {size}")
        for i in range(len(allChargStation)):
            allChargStation = driver.find_elements(By.XPATH,xPathStations)
            station= allChargStation[i]
            station.click()
            WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located((By.XPATH, xPathInfoPrice))
            )

            infoAndPriceButtons = driver.find_elements(By.XPATH,xPathInfoPrice)

            print(len(infoAndPriceButtons))
            # Click on available buttons to extract extra information and make them visible
            # counter = 0
            # for button in infoAndPriceButtons:
                # time.sleep(10)
                # button.click()
                # print("button",counter)
                # counter=counter+1
            address = driver.find_element(By.XPATH, xPathAddress).text
            print(address)
            availability = driver.find_element(By.XPATH,xPathAvialability).text
            rate = driver.find_element(By.XPATH,xPathRate ).text
            print(rate)
            powerType = driver.find_element(By.XPATH, xPathPower).text
            print(powerType)
            price = driver.find_elements(By.XPATH, xPathPrice)[1].text
            # print("this is the whole price info1 ", price, "this is the whole price info2 ")
            # price = driver.find_elements(By.XPATH, xPathPriceDirect)[1].text
            # print("this is the whole price info3 ",price,"this is the whole price info4 ")
            # price = driver.find_elements(By.XPATH, xPathPrice)[1].text
            # print(price,"1")
            # price = driver.find_elements(By.XPATH, xPathPrice)[2].text
            # print(price,"2")
            print('Address=', address, ', Availability=', availability, ', Charging rate=', rate, ', Power and connection type=', powerType, ', Price=', price)
            linesOfRate = rate.split("\n")
            chargingRate = linesOfRate[0]
            power = linesOfRate[1]
            type = linesOfRate[2]
            linesOfConnection = powerType.split("\n")
            connectionType = linesOfConnection[1]
            outputDF.loc[len(outputDF)] = [address, availability, chargingRate, power, type, connectionType, price]
            backButton = driver.find_element(By.XPATH,xPathBackButton )
            backButton.click()
            time.sleep(1)
            driver.execute_script("arguments[0].scrollIntoView();", station)
            print('######################################################')

        time.sleep(10)


    except Exception as e:
        print(f"Error occurred: {e}")
        traceback.print_exc()

    finally:
        # Close the browser after the interaction

        time.sleep(5)
        # timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # # outputDFBestResult.to_csv(f"output_{timestamp}.csv", index=False)
        # outputDF.to_csv(f"output_{timestamp}.csv", index=False)
        print(outputDF)


    driver.quit()
    # timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # outputDF.to_csv(f"output_{timestamp}.csv", index=False)
    # outputDF.to_csv("output.csv", index=False)
    return outputDF

def optimiser_WSM():

    # file_path = r'E:/HiWi/SampleData.csv'
    outputLadekarteDf = ladekarte()
    outputLadekarteDf['Distance KM'] = None

    for i in range(len(outputLadekarteDf)):
        print(outputLadekarteDf['Address'].loc[i])
        try:
            location = geocode(outputLadekarteDf['Address'].loc[i], provider='nominatim', user_agent='xyz', timeout=10)
        except Exception as e:
            print(f"{e}")
            continue

        if location is None or location.empty:
            continue
        point = location.geometry.iloc[0]
        if point.is_empty:
            print("Returned geometry is empty.")
            continue
        else:
            lat1 = point.y
            lon1 = point.x
            print(lat1, lon1)
            # distance = haversine(lat, long, lat1, lon1)  #gets the direct distance between the two points regardless of any obstacles or traffic in between
            distance = getDistance(lat, long, lat1, lon1)    #gets the direct distance between the two points while taking any obstacles or traffic in between into account
            print(distance)
            outputLadekarteDf.at[i, 'Distance KM'] = distance
    # Availability scoring
    availability_map = {
        "Available": 3,
        "In Use": 1,
        "Out of Service": -100000  # wont be used due to inf
    }
    outputLadekarteDf['availability_score'] = outputLadekarteDf['Availability'].map(availability_map)

    # Normalize power and inverse price
    outputLadekarteDf['PowerKW'] = outputLadekarteDf['Power'].str.extract(r'([\d.]+)').astype(float)
    outputLadekarteDf['power_score'] = outputLadekarteDf['PowerKW'] / outputLadekarteDf['PowerKW'].max()
    outputLadekarteDf['price_score'] = 1 / outputLadekarteDf['Price'].str.extract(r'([\d.]+)').astype(float)
    outputLadekarteDf['distance_score'] = 1 - (outputLadekarteDf['Distance KM'] / outputLadekarteDf['Distance KM'].max())
    outputLadekarteDf['distance_score'] = pd.to_numeric(outputLadekarteDf['distance_score'],errors='coerce')  # to make cast the values into float instead of an object to avoid later errors
    outputLadekarteDf['Charging_rate_score'] = outputLadekarteDf['Charging rate'].str.extract(r'([\d.]+)').astype(float)
    # print(outputLadekarteDf['price_score'].dtype)
    # print(outputLadekarteDf['distance_score'].dtype)
    # Connection preference (user-defined)
    preferred_connection = conType
    outputLadekarteDf['connection_score'] = outputLadekarteDf['Connection type'].apply(lambda x: 1 if x == preferred_connection else 0.5)
    chargingRates = outputLadekarteDf['Charging rate'].str.extract(r'([\d.]+)')[0].astype(float)
    # outputLadekarteDf['Estimated_charging_time']=None
    randomSOC= random.uniform(0.2,0.79)
    print('SOC = ',randomSOC)
    if timePreference == "I have enough time":
        # outputLadekarteDf['Adjusted_charging_time']
        for i,chargeRate in enumerate (chargingRates):
            estimatedChargingTime = calcChargetime(chargeRate, randomSOC)
            outputLadekarteDf.at[i,'Estimated_charging_time_hr']=estimatedChargingTime
            adjustedChargingTime=1.2*estimatedChargingTime
            outputLadekarteDf.at[i, 'Adjusted_charging_time_hr'] = adjustedChargingTime
    elif timePreference== "I am in a hurry":
        for i, chargeRate in enumerate(chargingRates):
            estimatedChargingTime = calcChargetime(chargeRate, randomSOC)
            outputLadekarteDf.at[i, 'Estimated_charging_time_hr'] = estimatedChargingTime
            adjustedChargingTime = 0.8 * estimatedChargingTime
            outputLadekarteDf.at[i, 'Adjusted_charging_time_hr'] = adjustedChargingTime
    else:
        for i, chargeRate in enumerate(chargingRates):
            estimatedChargingTime = calcChargetime(chargeRate, randomSOC)
            outputLadekarteDf.at[i, 'Estimated_charging_time_hr'] = estimatedChargingTime


    # Weighted score (tune weights as needed) should be adjusted in th future  ,"I have enough time", "I am in a hurry"]
    if preference == "Distance over price":
        if timePreference =='I have enough time':
            w1, w2, w3, w4, w5,w6 = 3, 2, 2, 1, 10, 2
        elif timePreference =='I am in a hurry':
            w1, w2, w3, w4, w5, w6 = 3, 2, 2, 1, 10, 5
        else: w1, w2, w3, w4, w5, w6 = 3, 2, 2, 1, 10, 1
    elif preference == "Price over distance":
        if timePreference == 'I have enough time':
            w1, w2, w3, w4, w5, w6 = 3, 2, 2, 1, 10, 2
        elif timePreference == 'I am in a hurry':
            w1, w2, w3, w4, w5, w6 = 3, 2, 2, 1, 10, 5
        else:
            w1, w2, w3, w4, w5, w6 = 3, 2, 2, 1, 10, 1
    else:
         # will be differnt with a warrning in case the user didn't choose any preference
        if timePreference == 'I have enough time':
            w1, w2, w3, w4, w5, w6 = 3, 2, 2, 1, 10, 2
        elif timePreference == 'I am in a hurry':
            w1, w2, w3, w4, w5, w6 = 3, 2, 2, 1, 10, 5
        else:
            w1, w2, w3, w4, w5, w6 = 3, 2, 2, 1, 10, 1

    outputLadekarteDf['total_score'] = (
            w1 * outputLadekarteDf['availability_score'] +
            w2 * outputLadekarteDf['power_score'] +
            w3 * outputLadekarteDf['price_score'] +
            w4 * outputLadekarteDf['connection_score']+
            w5 * outputLadekarteDf['distance_score']+
            w6 * outputLadekarteDf['Charging_rate_score']
    )
    print(outputLadekarteDf)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # outputDFBestResult.to_csv(f"output_{timestamp}.csv", index=False)
    outputLadekarteDf.to_csv(f"output_{timestamp}.csv", index=False)
    # Filter out out-of-service
    df_filtered = outputLadekarteDf[outputLadekarteDf['availability_score'] > -np.inf]
    print(outputLadekarteDf)
    # Best station
    best = df_filtered.loc[df_filtered['total_score'].idxmax()]
    # print(type(best))
    bestDF = best.to_frame()
    # print(type(best))
    # timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    bestDF=bestDF.T
    bestDF.to_csv(f"output_best_{timestamp}.csv", index=False)
    print(bestDF)


    print("Best option:\n", best)
    bestAddress= best['Address']   #still need to create a function to get the coordinates of the best address
    try:
        bestAddress = geocode(bestAddress, provider='nominatim', user_agent='xyz', timeout=10)
    except Exception as e:
        print(f"{e}")
    if bestAddress is None or bestAddress.empty:
        print('the Address is not valid')
    else:
        point = bestAddress.geometry.iloc[0]
        if point.is_empty:
            print('the Address is not valid')
        else:
            lat1 = point.y
            lon1 = point.x
            # show_map(lat1, lon1)

    # bestDF = best.to_frame()
    # print(bestDF.loc["Connection type", 1])
    # columnsBestResult = [
    #     "User Address", "User Latitude", "User Longitude", "User Connection",
    #     "Station Address", "Station Latitude", "Station Longitude",
    #     "Connection Type", "Preference", "Availability", "Charging Rate", "Power",
    #     "Current Type", "Price", "Total Score"
    # ]
    #
    # outputDFBestResult = pd.DataFrame(columns=columnsBestResult)
    #
    # new_row = {
    #     "User Address": destination,
    #     "User Latitude": lat,
    #     "User Longitude": long,
    #     "User Connection": conType,
    #
    #     "Station Address": bestAddress, #bestDF.loc[" Address", 1],
    #     "Station Latitude": lat1,
    #     "Station Longitude": lon1,
    #
    #     "Connection Type": bestDF.loc["Connection type", 0],
    #     "Availability": bestDF.loc["Availability", 0],
    #     "Charging Rate": bestDF.loc["Charging rate", 0],
    #     "Power": bestDF.loc["Power", 0],
    #     "Current Type": bestDF.loc["Current type", 0],
    #     "Price": bestDF.loc["Price", 0],
    #
    #     "Preference": preference,
    #     "Total Score": bestDF.loc["total_score", 0]
    # }
    #
    # outputDFBestResult = pd.concat([outputDFBestResult, pd.DataFrame([new_row])], ignore_index=True)
    # timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # outputDFBestResult.to_csv(f"output_{timestamp}.csv", index=False)

    return best,lat1,lon1

def show_map(lat1, long1):
    # url = f"https://www.google.com/maps?q={lat1},{long1}" # this url shows only the location of the charging station
    # url = f"https://www.google.com/maps/dir/{lat},{long}/{lat1},{long1}&travelmode=driving" # the url includes the starting and the end point and suggests a route between them
    url = f"https://www.google.com/maps/dir/?api=1&origin={lat},{long}&destination={lat1},{long1}&travelmode=driving" #the url includes the starting and the end point and suggests a route between them for a car
    # webview.create_window("Location of charging station", url)
    # webview.start()
    webbrowser.open(url)
def haversine(lat1, lon1, lat2, lon2):
    # Earth radius in kilometers (use 3956 for miles)
    R = 6371.0

    # Convert degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Differences
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Haversine formula
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance

def getDistance(lat1, lon1, lat2, lon2):
    api_key = 'CrNfNTA8TZFCLkEmb1fJzXOtN37r0oiE8GUlOPVqBJc'  # api from here maps
    url = "https://router.hereapi.com/v8/routes"

    params = {
        "transportMode": "car",
        "origin": f"{lat1},{lon1}",
        "destination": f"{lat2},{lon2}",
        "return": "summary",
        "routingMode": "fast", #fastest way between the tow points regardless of the distance
        # "routingMode": "short", #shortest way between the tow points regardless of the traffic
        "apikey": api_key
    }

    response = requests.get(url, params=params)
    data = response.json()
    summary = data["routes"][0]["sections"][0]["summary"]
    distance = summary["length"] / 1000  # the acctual driving distance in km between the two coordinates
    return distance

def calcChargetime(chargeRate, currentSOC):
    chargeTime=((0.8-currentSOC)*375)/(chargeRate*1.6)
    print(chargeTime)
    return chargeTime

# # Convert the best row to a string
# best_text = best.to_string()
#
# # Show it in a label
# label = tk.Label(root, text="Best option:\n" + best_text, justify='left', font=("Arial", 12))
# label.pack(padx=10, pady=10)


# optimiser_WSM() #weighted scoring method

root.mainloop()

