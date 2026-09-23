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
from geopandas.tools import geocode
from datetime import datetime


# notes for future tasks
# still need to reduce the time for each run and include the function to mearge all the files and delete the previous ones


lat=None
long=None
conType=None
preference=None
timePreference=None
destination=None
# allows the user to enter an address and it returns the coordinates lat and long
def get_location(address):
    global lat, long, destination
    try:
        # address = 'Aachen'
        destination = address
        location = geocode(address, provider='nominatim', user_agent='xyz', timeout=10)
        lat = location.geometry.loc[0].y
        long =location.geometry.loc[0].x
    except ValueError:
        print("Invalid address.")

# to make the browser invasible
options = Options()
options.add_argument("--headless")
# using webdrivermamager there's no need to download and install chrome driver
service = Service(ChromeDriverManager().install())
# driver = webdriver.Chrome(service=service, options=options)#invasible
driver = webdriver.Chrome(service=service)  # vasible




def ladekarte(timestamp):


    columns = ["Address", "Availability","Timestamp" ]
    outputDF = pd.DataFrame(columns=columns)


    path = "https://driver.chargepoint.com/mapCenter/" + str(lat) + "/" + str(long) + "/18?view=list"
    driver.get(path)
    # Maximaize the opend window to ensure a bigger objects list
    driver.maximize_window()

    try:

        xPathStations= '//div[@class="sc-gFqAkR sc-dAbbOL sc-duAPit dcOspJ kHQqqq joWlqH"]' # xpath of the buttons of each charging station
        xPathInfoPrice = '//div[@data-accordion-component="AccordionItemHeading"]' #//div[@data-accordion-component="AccordionItemHeading"]
        xPathAddress = '//div[@class="sc-gFqAkR sc-dAbbOL dcOspJ kHQqqq"]'
        xPathAvialability = '//div[@class="sc-gFqAkR sc-fUnMCh sc-kTbCBX dcOspJ gxCHVP cyCmrT"]'
        # xPathRate = '//div[@class="sc-leQnM gTwmVa"]' #charge rate, power and type acdc
        # xPathPower = '//div[@class="sc-fPXMVe sc-dYoqmx gdLKmB jyAqvx"]' #acdc and connection type
        # xPathPrice = '//div[@class="sc-cyRcrZ celkDu"]'
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
            # Click on available buttons to extract extra information and make them visible
            # for button in infoAndPriceButtons:
            #     button.click()
            address = driver.find_element(By.XPATH, xPathAddress).text
            availability = driver.find_element(By.XPATH,xPathAvialability).text
            # rate = driver.find_element(By.XPATH,xPathRate ).text
            # powerType = driver.find_element(By.XPATH, xPathPower).text
            # price = driver.find_elements(By.XPATH, xPathPrice)[1].text
            print('Address=', address, ', Availability=', availability, 'Timestamp=', timestamp)
            # linesOfRate = rate.split("\n")
            # chargingRate = linesOfRate[0]
            # power = linesOfRate[1]
            # type = linesOfRate[2]
            # linesOfConnection = powerType.split("\n")
            # connectionType = linesOfConnection[1]
            outputDF.loc[len(outputDF)] = [address, availability,timestamp]
            backButton = driver.find_element(By.XPATH,xPathBackButton )
            backButton.click()
            time.sleep(1)
            driver.execute_script("arguments[0].scrollIntoView();", station)
            print('######################################################')

        time.sleep(3)


    except Exception as e:
        print(f"Error occurred: {e}")
        traceback.print_exc()

    finally:
        # Close the browser after the interaction

        time.sleep(2)
        timestampOfTheName = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # # outputDFBestResult.to_csv(f"output_{timestamp}.csv", index=False)
        # outputDF.to_csv(f"output_{timestamp}.csv", index=False)
        print(outputDF)


    outputDF.to_csv(f"output_{timestampOfTheName}.csv", index=False)
    outputDF.to_csv("output.csv", index=False)
    return outputDF

try:
    while True:
        run_start = time.monotonic()
        print("\n" + "=" * 60)
        print(f"Starting run at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        timestampOfTheRun = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        try:
            get_location("nizzaallee 2")
            ladekarte(timestampOfTheRun)

            get_location("Seilgraben 31")
            ladekarte(timestampOfTheRun)

            get_location("Aachen Bushof")
            ladekarte(timestampOfTheRun)

            get_location("Jesuitenstraße 12, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("Lagerhausstraße 20, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("Kullenhofstr. 80, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("55 Ahornstraße, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("Am Gut Wolf 4, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("Vaalser Str. 48")
            ladekarte(timestampOfTheRun)

            get_location("Sandkaulstraße 20, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("Kurbrunnenstraße 18, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("Campus-Boulevard 53, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("Wirichsbongardstraße 47, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("Süsterfeldstraße 63, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("Viktoriaallee 49, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("Vaalser Straße 460, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("Vaalser Straße 410, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("Hans-Böckler-Allee 62, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("Kullenhofstraße. 80, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("Kullenhofstr. 0, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("Forckenbeckstraße 61, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("Judengasse 7, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("Monheimsallee 44, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("Pontwall 14, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("mauerstraße 1a aachen")
            ladekarte(timestampOfTheRun)

            get_location("Marienplatz 17, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("Henricistraße 68, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("Hirschgraben 35, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("Krefelder Str. 155, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("Hubert-Wienen-Straße 24, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("Kackertstraße 2, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("Annastraße 64, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("Süsterfeldstraße 200, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("Wirichsbongardstraße 53, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("Turmstraße 1, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("Couvenstraße 6, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("Krefelder Str. 205, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("Lombardenstraße 24, Aachen")
            ladekarte(timestampOfTheRun)

            get_location("Krefelder Str. 199, Aachen")
            ladekarte(timestampOfTheRun)



        except Exception as e:
            print(f"Error during this run: {e}")
            traceback.print_exc()
        run_duration = time.monotonic() - run_start
        print("\n" + "=" * 60)
        print(f"End run at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        interval = 15 * 60  # 15 minutes in seconds

        remaining = interval - run_duration

        if remaining > 0:
            print(f"Waiting {remaining / 60:.2f} minutes ")
            time.sleep(remaining)
        else:
            print("Run took longer than 15 minutes.")



except KeyboardInterrupt:
    print("\nProgram stopped by user.")

finally:
    driver.quit()
    print("Driver closed.")
# while True:
#     try:
#         print("\n" + "=" * 60)
#         print(f"Starting run at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
#
#
#         ladekarte()
#
#     except Exception as e:
#         print(f"Error in main loop: {e}")
#         traceback.print_exc()
#
#     print(f"\nRun finished at {datetime.now().strftime('%Y-%m-%d %H:%M')}")
#     print("Waiting 15 minutes until next run...")
#
#     time.sleep(5 * 60)