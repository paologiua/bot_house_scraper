#!/usr/bin/python

import telebot

API_TOKEN = '5352956589:AAGXK6s0U9LjE2B_rnZxPdMwfRIrupw_I3s'
bot = telebot.TeleBot(API_TOKEN)

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
        time_from_pub = hours_from_pub.text.split(" ")
        time_from_pub = time_from_pub[0] if "min" not in time_from_pub[1] else "0." + time_from_pub[0]
        return [hours_from_pub.text, date_to_string(today_less_hours(int(float(time_from_pub))))]

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

def array_dif(arr1, arr2):
    diff = list(set(arr1) - set(arr2))

    return {key: value for key, value in arr1.items() if key in diff}

def get_translate_url(url):
    import urllib.parse
    
    return "https://translate.google.com/translate?sl=it&tl=it&hl=it&u=%s&client=webapp" % urllib.parse.quote(url)

def send_everyone(bot, message):
    with open('chat_ids.json') as chats:
        chats = json.load(chats)
    
        for chat in chats:
            bot.send_message(chat, message)


url = "https://www.idealista.it/aree/affitto-stanze/con-sesso_ragazzo/lista-1?ordine=pubblicazione-desc&shape=%28%28g%7ExtGsbuv%40iwBydGcjAuhEai%40cnKr_HzKhtBhqE%7EGvv%40_KvXci%40duCaKfuCbf%40flAkuCfsD%29%29"

import json
import random
from datetime import datetime
from urllib.parse import urlparse

header = ['room_url', 'room_name', 'room_price', 'room_phone', 'hours_from_pub', 'publication_date']

old_data = {}

while(True):
    new_data = {}

    page = get_page(driver, get_translate_url(url))

    rooms = page.select(".item-multimedia-container:not(.item_contains_branding)")
    for room in rooms:
        link = room.find("a", {"class": "item-link"})

        room_url = "https://www.idealista.it%s" % urlparse(link["href"]).path
        room_name = link.get_text()

        room_price = get_text_el(room.find("span", {"class": "item-price"}))
        room_phone = get_text_el(room.find("span", {"class": "icon-phone"}))
        
        pub_info = get_publication_info(room)
        hours_from_pub = pub_info[0]
        publication_date = pub_info[1]

        new_data[room_url] = [room_name, room_price, room_phone, hours_from_pub, publication_date]

    print(datetime.now().strftime("%d-%m-%Y_%H:%M:%S:"))
    
    new_houses = array_dif(new_data, old_data)
    print(json.dumps(array_dif(new_data, old_data),indent=4) + "\n")
    
    for url in list(reversed(new_houses.keys())):
        send_everyone(bot, f'''
room_url: {url},
room_name: {new_houses[url][0]},
room_price: {new_houses[url][1]},
room_phone: {new_houses[url][2]},
hours_from_pub: {new_houses[url][3]},
publication_date: {new_houses[url][4]},
            ''')

    old_data = new_data

    if(not page.find("a", {"class": "icon-arrow-right-after"})):
        break
        
    time.sleep((30 + random.randint(-10, 10)) * 60)
