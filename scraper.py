from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options
import csv
import re

def create_driver():
    edge_options = Options()
    edge_options.add_argument("--log-level=3")
    edge_options.add_argument("--headless=new") 
    edge_options.add_argument("--disable-gpu")
    edge_options.add_argument("--window-size=1920,1080")
    edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    edge_options.add_argument("--blink-settings=imagesEnabled=false") 
    edge_options.add_argument("--disable-dev-shm-usage")
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("--disable-extensions")

    prefs = {"profile.managed_default_content_settings.images": 2, 
            "profile.managed_default_content_settings.stylesheet": 2}
    edge_options.add_experimental_option("prefs", prefs)
    
    return webdriver.Edge(options=edge_options) 

def get_scraped_flats(n):
    scraped_data = []
    
    # Uruchamiamy pierwszą instancję przeglądarki przed pętlą
    driver = create_driver()
    try: 
        for i in range(1,n+1):
            if i > 1 and (i - 1) % 40 == 0:
                driver.quit() # To uwalnia zapchany RAM
                driver = create_driver() # To startuje czystą sesję
            url = f'https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/mazowieckie/warszawa/warszawa/warszawa?limit=36&ownerTypeSingleSelect=ALL&by=DEFAULT&direction=DESC&page={i}'
            print(f"Opening site {url}")
            driver.get(url)
            if i == 1:
                try:
                    cookie_button = WebDriverWait(driver,5).until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
                    cookie_button.click()
                    print('Button clicked')
                except Exception as e:
                    print(f"Button doesnt exist or button was already clikced. Error: {e}")
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'ul[data-sentry-component="CardsList"] > li'))
                )
            except Exception:
                print(f"Brak ofert na stronie {i} lub strona za długo się ładuje. Pomijam.")
                continue


            flats = driver.find_elements(By.CSS_SELECTOR, 'ul[data-sentry-component="CardsList"] > li')

            print(f"Liczba znalezionych ofert: {len(flats)}")
            driver.save_screenshot("otodom_debug.png")

            for flat in flats:
                try:
                    name = flat.find_element(By.CSS_SELECTOR, '[data-cy="listing-item-title"]').text
                    raw_price = flat.find_element(By.CSS_SELECTOR, 'span[data-sentry-element="MainPrice"]').text
                    raw_square_footage = flat.find_element(By.XPATH, './/dd[contains(., "m²")]').text
                    raw_rooms = flat.find_element(By.XPATH, './/dd[contains(., "pok")]').text
                    raw_address = flat.find_element(By.CSS_SELECTOR, 'p[data-sentry-component="Address"]').text
                    raw_floor = flat.find_element(By.XPATH, './/dd[contains(., "piętro") or contains(., "parter")]').text
                    
                    

                    price = re.sub(r'[^\d]', '', raw_price)
                    square_footage = re.sub(r'[^\d,.]', '', raw_square_footage).replace(',', '.')
                    rooms_match = re.search(r'\d+', raw_rooms)
                    rooms = rooms_match.group(0) if rooms_match else ''
                    floor_match = re.search(r'\d+|parter', raw_floor.lower())
                    floor = floor_match.group(0) if floor_match else ""
                    address_parts = [p.strip() for p in raw_address.split(',')]
                    address_parts = [p for p in address_parts if p not in ['Warszawa', 'mazowieckie']]

                    street  = ""
                    estate = ""
                    district = ""

                    if len(address_parts) == 1:
                        district = address_parts[0]
                    elif len(address_parts) == 2:
                        district = address_parts[1]
                        estate = address_parts[0]
                    elif len(address_parts) >= 3:
                        district = address_parts[2]
                        estate = address_parts[1]
                        street = address_parts[0]

                    if street:
                        street = re.sub(r'\s+\d+.*$', '', street)

                    print(f'{name} | {price} | {square_footage} | {rooms} | {floor} | {street} | {estate} | {district}')

                    if not name or not price:
                        continue

                    scraped_data.append({
                        'Name':name,
                        'Price':price,
                        'Square_Footage':square_footage,
                        'Rooms': rooms,
                        'Floor': floor,
                        'Street': street,
                        'Estate': estate,
                        'District': district
                    })
                except Exception as e:
                    print(f'{e}')

    except Exception as e:
        print(f"Error {e}")
    finally:
        if scraped_data:
            try:
                with open('flats.csv',mode='w',newline='',encoding='utf-8') as file:
                    fieldnames =['Name','Price','Square_Footage','Rooms','Floor','Street','Estate','District']
                    writer = csv.DictWriter(file,fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(scraped_data)
            except Exception as e:
                print(f"{e}")
        print("Data is downloaded")
        driver.quit()

if __name__ == "__main__":
    get_scraped_flats(490)
