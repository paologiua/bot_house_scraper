from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time

option = webdriver.ChromeOptions()

option.add_experimental_option("excludeSwitches", ["enable-automation"])
option.add_experimental_option('useAutomationExtension', False)
option.add_argument('--disable-blink-features=AutomationControlled')

#Open Browser
driver = webdriver.Chrome('chromedriver', options=option)

driver.get("https://www.idealista.it/")

WebDriverWait(driver=driver, timeout=10).until(
    lambda x: x.execute_script("return document.getElementById('didomi-notice-disagree-button') != null")
)
time.sleep(2)

def get_page(driver, url):
    from bs4 import BeautifulSoup

    driver.get(url)
    content = (WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.TAG_NAME, "html"))).get_attribute('outerHTML'))
    return BeautifulSoup(content, "html.parser")

def get_publication_info(room_html):
    detail = room_html.find_all("span", {"item-detail"})[-1]
    if("fumare" in detail.text):
        return [None, "Più di una settimana fa"]

    hours_from_pub = detail.find("small", {"class": "txt-highlight-red"})
    if(hours_from_pub):
        return [hours_from_pub.text, date_to_string(today_less_hours(int(hours_from_pub.text.replace(" ore", ""))))]

    today = int(date_to_string(get_today_date()).split("/")[0])
    day_pub = today - 1
    if("Inserito" not in detail.text):
        day_pub = int(detail.text.split()[0])
    if(today > day_pub):
        return [None, date_to_string(get_today_date()).replace(str(today), str(day_pub), 1)]

    return [None, date_to_string(today_less_one_month()).replace(str(today), str(day_pub), 1)]

def get_today_date():
    from datetime import datetime, timedelta
    import pytz

    return datetime.now(pytz.timezone('Europe/Rome'))

def today_less_hours(hours):
    from datetime import timedelta

    return (get_today_date() - timedelta(hours=hours))

def today_less_one_month():
    date = get_today_date()
    month = (date.month - 2) % 12 + 1
    if(date.month == 1):
        return date.replace(month=month, year=date.year-1)
    return date.replace(month=month)

def date_to_string(date):
    return date.strftime("%d/%m/%Y")

def get_text_el(el):
    return el.text if el else "None"

import pandas as pd
import random
from datetime import datetime

header = ['room_url', 'room_name', 'room_price', 'room_phone', 'hours_from_pub', 'publication_date']

while(True):
    data = []

    page = get_page(driver, "https://www.idealista.it/aree/affitto-stanze/con-sesso_ragazzo/lista-1?ordine=pubblicazione-desc&shape=%28%28g%7ExtGsbuv%40iwBydGcjAuhEai%40cnKr_HzKhtBhqE%7EGvv%40_KvXci%40duCaKfuCbf%40flAkuCfsD%29%29")

    rooms = page.find_all("article", {"class": "item-multimedia-container"})
    for room in rooms:
        link = room.find("a", {"class": "item-link"})

        room_url = "https://www.idealista.it%s" % link["href"]
        room_name = link.get_text()

        room_price = get_text_el(room.find("span", {"class": "item-price"}))
        room_phone = get_text_el(room.find("span", {"class": "icon-phone"}))

        pub_info = get_publication_info(room)
        hours_from_pub = pub_info[0]
        publication_date = pub_info[1]

        room_data = [room_url, room_name, room_price, room_phone, hours_from_pub, publication_date]
        print(room_data)
        
        data.append(room_data)

    if(not page.find("a", {"class": "icon-arrow-right-after"})):
        break

    df = pd.DataFrame(data, columns=header)
    df.to_csv('room%s.csv' % datetime.now().strftime("%d-%m-%Y_%H:%M:%S"))
    time.sleep((30 + random.randint(-10, 10)) * 60)

