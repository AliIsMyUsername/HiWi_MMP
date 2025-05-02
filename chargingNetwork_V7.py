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
def randomTrip():
    file_path = r'E:/HiWi/Scenarios.csv'
    df = pd.read_csv(file_path)
    # print(df)
    randomBattery = random.randint(0, 11)
    randomDestination = random.randint(0, 11)
    randomSoc = random.randint(0, 11)
    randomTime = random.randint(0, 11)
    randomDescription = random.randint(0, 11)
    randomValues = [randomBattery, randomDestination, randomSoc, randomTime,
                    randomDescription, randomDescription, randomDescription]

    # print(randomValues)
    columns = ['Battery kWh', 'Destination km', 'Current soc', 'Time available mins', 'Description', 'Latitude',
               'Longitude']
    randomScenario = [df['Battery kWh'].iloc[randomBattery], df['Destination km'].iloc[randomDestination],
                      df['Current soc'].iloc[randomSoc], df['Time available mins'].iloc[randomTime],
                      df['Description'].iloc[randomDescription],
                      df['Latitude'].iloc[randomDescription], df['Longitude'].iloc[randomDescription]]
    tripDetails = pd.DataFrame([randomScenario], columns=columns)

    print(tripDetails)
    return df['Latitude'].iloc[randomDescription], df['Longitude'].iloc[randomDescription]

def ladekarte():
    # to make the browser invasible
    options = Options()
    options.add_argument("--headless")
    # using webdrivermamager there's no need to download and install chrome driver
    service = Service(ChromeDriverManager().install())
    # driver = webdriver.Chrome(service=service, options=options)#invasible
    driver = webdriver.Chrome(service=service)  # vasible
    columns = ["Address", "Availability", "Charging rate", "Power", "Current type", "connection type", "Price"]
    outputDF = pd.DataFrame(columns=columns)

    coordinates=randomTrip()
    lat = coordinates[0]
    lon = coordinates[1]
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
        for station in allChargStation:
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


    driver.quit()
    outputDF.to_csv("output.csv", index=False)

# def optimiser():


ladekarte()
