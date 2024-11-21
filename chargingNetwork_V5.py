from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import traceback

# Path to your ChromeDriver
driver_path = "C:/Users/Abdulrahman Ali/Downloads/chromedriver-win64/chromedriver.exe"

# Create a Service object
service = Service(driver_path)

# Initialize the browser with the Service object
driver = webdriver.Chrome(service=service)

# Open the chargepoint website
#chargepoint website/latitude/longtude/search range with 1 is the whole world and 18 is the surroundig area of around 5km*5km
driver.get("https://driver.chargepoint.com/mapCenter/50.78681303118092/6.075362185399102/15?view=list")
# Maximaize the opend window to ensure a bigger objects list
driver.maximize_window()

try:
    # Wait up to 20 seconds for the charging station list to be visible
    WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.XPATH, '//div[@class="sc-gFqAkR sc-dAbbOL sc-iVDsrp dcOspJ kHQqqq joTtKM"]'))
    )

    # Get all the charging stations
    allChargStation = driver.find_elements(By.XPATH, '//div[@class="sc-gFqAkR sc-dAbbOL sc-iVDsrp dcOspJ kHQqqq joTtKM"]')
    size = len(allChargStation)
    print(f"Number of charging stations found: {size}")
    for station in allChargStation:
        station.click()
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.XPATH, '//div[@data-accordion-component="AccordionItemHeading"]'))
        )

        infoAndPriceButtons = driver.find_elements(By.XPATH, '//div[@data-accordion-component="AccordionItemHeading"]')
        # Click on available buttons to extract extra information and make them visible
        for button in infoAndPriceButtons:
            button.click()

        address=driver.find_element(By.XPATH, '//div[@class="sc-gFqAkR sc-dAbbOL dcOspJ kHQqqq"]').text
        availability=driver.find_element(By.XPATH, '//div[@class="sc-gFqAkR sc-fUnMCh sc-feNupb dcOspJ gxCHVP jTLVZJ"]').text
        rate=driver.find_element(By.XPATH, '//div[@class="sc-dxUMQK gDdSqj"]').text
        powerType=driver.find_element(By.XPATH, '//div[@class="sc-fPXMVe sc-eWHaVC gdLKmB gGanZx"]').text
        price=driver.find_elements(By.XPATH, '//div[@class="sc-cyRcrZ celkDu"]')[0].text
        print('Address=', address, ', Availability=', availability, ', Charging rate=', rate,', Power and connection type=', powerType, ', Price=', price)

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
    driver.quit()
