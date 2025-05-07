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


pd.set_option('display.max_columns',None) #to show all the columns
pd.set_option('display.max_rows',None) #to show all the rows
def randomTrip():
    file_path = r'E:/HiWi/Scenarios.csv'
    df = pd.read_csv(file_path)
    # print(df)
    randomBattery = random.randint(0, 11)
    randomDestination = random.randint(0, 11)
    randomSoc = random.randint(0, 11)
    randomTime = random.randint(0, 11)
    randomDescription = random.randint(0, 11)
    randomConnection = random.randint(0, 11)
    randomValues = [randomBattery, randomDestination, randomSoc, randomTime,
                    randomDescription, randomDescription, randomDescription]

    # print(randomValues)
    columns = ['Battery kWh', 'Destination km', 'Current soc', 'Time available mins', 'Description', 'Latitude',
               'Longitude','Connection type']
    randomScenario = [df['Battery kWh'].iloc[randomBattery], df['Destination km'].iloc[randomDestination],
                      df['Current soc'].iloc[randomSoc], df['Time available mins'].iloc[randomTime],
                      df['Description'].iloc[randomDescription],
                      df['Latitude'].iloc[randomDescription], df['Longitude'].iloc[randomDescription],
                      df['Connection type'].iloc[randomConnection]]
    tripDetails = pd.DataFrame([randomScenario], columns=columns)

    print(tripDetails)
    # return df['Latitude'].iloc[randomDescription], df['Longitude'].iloc[randomDescription],df['Connection type'].iloc[randomConnection]
    return tripDetails
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

    userData=randomTrip()
    lat = userData.loc[0,'Latitude']
    lon = userData.loc[0,'Longitude']
    path = "https://driver.chargepoint.com/mapCenter/" + str(lat) + "/" + str(lon) + "/15?view=list"
    driver.get(path)
    # Maximaize the opend window to ensure a bigger objects list
    driver.maximize_window()

    try:
        # Wait up to 20 seconds for the charging station list to be visible
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located(
                (By.XPATH, '//div[@class="sc-gFqAkR sc-dAbbOL sc-CCtys dcOspJ kHQqqq gqVsaY"]'))
            # same xpath of the chargingstations, just waiting for it to appeare
        )
        # buttonsLocation = driver.find_elements(By.XPATH,'//button[@class="sc-aXZVg ciuTTg link sc-fnLEGM jOGWNJ"]')  # a way to automatically get the user's location
        # buttonsLocation[0].click()
        # buttonsShare = driver.find_elements(By.XPATH,
        #                                '//button[@class="sc-aXZVg ciuTTg primary"]')  # needed only for the first element in the loop
        # buttonsShare[0].click()
        # Get all the charging stations
        allChargStation = driver.find_elements(By.XPATH,
                                               '//div[@class="sc-gFqAkR sc-dAbbOL sc-CCtys dcOspJ kHQqqq gqVsaY"]')  # Same as the previous xpath
        size = len(allChargStation)
        print(f"Number of charging stations found: {size}")
        for i in range(len(allChargStation)):
            allChargStation = driver.find_elements(By.XPATH,
                                                   '//div[@class="sc-gFqAkR sc-dAbbOL sc-CCtys dcOspJ kHQqqq gqVsaY"]')  # Same as the previous xpath
            station= allChargStation[i]
            station.click()
            WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located((By.XPATH, '//div[@data-accordion-component="AccordionItemHeading"]'))
            )

            infoAndPriceButtons = driver.find_elements(By.XPATH,
                                                       '//div[@data-accordion-component="AccordionItemHeading"]')
            # Click on available buttons to extract extra information and make them visible
            for button in infoAndPriceButtons:
                button.click()

            address = driver.find_element(By.XPATH, '//div[@class="sc-gFqAkR sc-dAbbOL dcOspJ kHQqqq"]').text
            availability = driver.find_element(By.XPATH,
                                               '//div[@class="sc-gFqAkR sc-fUnMCh sc-dxUMQK dcOspJ gxCHVP ckHQeR"]').text
            rate = driver.find_element(By.XPATH, '//div[@class="sc-elxqWl cUXcTO"]').text
            powerType = driver.find_element(By.XPATH, '//div[@class="sc-fPXMVe sc-APcvf gdLKmB fPhTpt"]').text
            price = driver.find_elements(By.XPATH, '//div[@class="sc-cyRcrZ celkDu"]')[0].text
            print('Address=', address, ', Availability=', availability, ', Charging rate=', rate,
                  ', Power and connection type=', powerType, ', Price=', price)
            linesOfRate = rate.split("\n")
            chargingRate = linesOfRate[0]
            power = linesOfRate[1]
            type = linesOfRate[2]
            linesOfConnection = powerType.split("\n")
            connectionType = linesOfConnection[1]
            outputDF.loc[len(outputDF)] = [address, availability, chargingRate, power, type, connectionType, price]
            backButton = driver.find_element(By.XPATH, '//span[@class="sc-jSoCLE iVARjs"]')
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
        outputDF.to_csv("output.csv", index=False)
        print(outputDF)


    driver.quit()
    outputDF.to_csv("output.csv", index=False)
    return outputDF, userData

def optimiser_WSM():

    # file_path = r'E:/HiWi/SampleData.csv'
    outputLadekarteDf,userDataDf = ladekarte()

    # Availability scoring
    availability_map = {
        "Available": 3,
        "In Use": 1,
        "Out of Service": -np.inf  # wont be used due to inf
    }
    outputLadekarteDf['availability_score'] = outputLadekarteDf['Availability'].map(availability_map)

    # Normalize power and inverse price
    outputLadekarteDf['PowerKW'] = outputLadekarteDf['Power'].str.extract(r'([\d.]+)').astype(float)
    outputLadekarteDf['power_score'] = outputLadekarteDf['PowerKW'] / outputLadekarteDf['PowerKW'].max()
    outputLadekarteDf['price_score'] = 1 / outputLadekarteDf['Price'].str.extract(r'([\d.]+)').astype(float)

    # Connection preference (user-defined)
    preferred_connection = userDataDf.loc[0,'Connection type']
    outputLadekarteDf['connection_score'] = outputLadekarteDf['Connection type'].apply(
        lambda x: 1 if x == preferred_connection else 0.5)

    # Weighted score (tune weights as needed)
    w1, w2, w3, w4 = 3, 2, 2, 1
    outputLadekarteDf['total_score'] = (
            w1 * outputLadekarteDf['availability_score'] +
            w2 * outputLadekarteDf['power_score'] +
            w3 * outputLadekarteDf['price_score'] +
            w4 * outputLadekarteDf['connection_score']
    )

    # Filter out out-of-service
    df_filtered = outputLadekarteDf[outputLadekarteDf['availability_score'] > -np.inf]

    # Best station
    best = df_filtered.loc[df_filtered['total_score'].idxmax()]
    print("Best option:\n", best)


# randomTrip()

# ladekarte()

optimiser_WSM() #weighted scoring method