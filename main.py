#!/usr/bin/python

import os
import os.path
import json
import telebot

def load_json_from_file(file_name, default_format):
    try:
        with open(os.path.dirname(os.path.realpath(__file__)) + '/%s' % file_name) as f:
            return json.load(f)
    except:
        write_json_to_file(file_name, default_format)
        return default_format

def write_json_to_file(file_name, dictionary):
    with open(os.path.dirname(os.path.realpath(__file__)) + '/%s' % file_name, 'w') as f:
        json.dump(dictionary, f, indent = 4)

def send_everyone(bot, message):
    chat_ids = load_json_from_file("options.json", OPTIONS_DEFAULT_FORMAT)['chat_ids']
    
    for chat_id in chat_ids:
        message_not_sent = True
        while(message_not_sent):
            try:
                message_not_sent = not bot.send_message(chat_id, message)
            except Exception as e:
                if "chat not found" in str(e):
                    options_dict = load_json_from_file("options.json", OPTIONS_DEFAULT_FORMAT)
                    options_dict["chat_ids"].remove(chat_id)
                    write_json_to_file("options.json", options_dict)
                    message_not_sent = False
                else:
                    print("Error sending to %s, retry in 3 seconds ..." % chat_id)
                    time.sleep(3)

def room_to_str(room_dict, room_url):
    return f'''room_url: {room_url},
room_name: {room_dict[room_url][0]},
room_price: {room_dict[room_url][1]},
room_phone: {room_dict[room_url][2]},
publication_time: {room_dict[room_url][3]},
publication_date: {room_dict[room_url][4]}'''

def get_last_room(web_site, status_dict, tab=''):
    last_check = status_dict[web_site]['last_check']
    return tab + (room_to_str(last_check, list(last_check.keys())[0]).replace("\n", "\n%s" % tab) if last_check else "None")

OPTIONS_DEFAULT_FORMAT = {
    'api_token': '',
    'urls': {
        'idealista': '',
        'subito': '',
        'immobiliare': ''
    },
    'chat_ids': []
}
STATUS_DEFAULT_FORMAT = {
    'idealista': {
        'last_check': {},
        'last_check_time': ''
    },
    'subito': {
        'last_check': {},
        'last_check_time': ''
    },
    'immobiliare': {
        'last_check': {},
        'last_check_time': ''
    }
}
API_TOKEN = load_json_from_file("options.json", OPTIONS_DEFAULT_FORMAT)['api_token']
URLS = load_json_from_file("options.json", OPTIONS_DEFAULT_FORMAT)['urls']

MIN_PRICE = 200
MAX_PRICE = 550

bot = telebot.TeleBot(API_TOKEN)

pid = os.fork()

if pid > 0:
    # Handle '/start' and '/help'
    @bot.message_handler(commands=['help', 'start'])
    def send_welcome(message):
        bot.reply_to(message, """\
Ciao sono BotHouseScraper e ti aggiornerò sulle nuove case!
    """)
        options_dict = load_json_from_file("options.json", OPTIONS_DEFAULT_FORMAT)
        if(message.chat.id not in options_dict['chat_ids']):
            options_dict['chat_ids'].append(message.chat.id)
            write_json_to_file("options.json", options_dict)

    # Handle '/status'
    @bot.message_handler(commands=['status'])
    def send_status(message):
        status_dict = load_json_from_file('status.json', STATUS_DEFAULT_FORMAT)

        idealista_last_room = get_last_room('idealista', status_dict, "    ")
        subito_last_room = get_last_room('subito', status_dict, "    ")
        immobiliare_last_room = get_last_room('immobiliare', status_dict, "    ")
        
        bot.reply_to(message, 
f'''idealista_last_check_time: {status_dict['idealista']['last_check_time']},
idealista_last_room: [
{idealista_last_room}
],

subito_last_check_time: {status_dict['subito']['last_check_time']},
subito_last_room: [
{subito_last_room}
],

immobiliare_last_check_time: {status_dict['immobiliare']['last_check_time']},
immobiliare_last_room: [
{immobiliare_last_room}
]''')

    bot.infinity_polling()
else:
    from selenium import webdriver
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from bs4 import BeautifulSoup
    import urllib.parse
    import random
    import time
    from datetime import datetime, timedelta

    def get_page(url):

        options = webdriver.ChromeOptions()

        options.add_argument('--headless')
        options.add_argument('window-size=1920x1080')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-blink-features=AutomationControlled')

        #Open Browser
        driver = webdriver.Chrome('chromedriver', options=options)
        
        content = False
        while(not content):
            try:
                driver.get(url)
                content = (WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.TAG_NAME, "html"))).get_attribute('outerHTML'))
            except:
                print("Error while getting the page, retry in 30 seconds ...")
                time.sleep(30)
                
        driver.close()
        return BeautifulSoup(content, "html.parser")

    def get_anticaptcha_url(url):
        urlparsed = urllib.parse.urlparse(url)

        netloc = urlparsed.netloc
        path = urlparsed.path
        query = urlparsed.query

        return "https://" + netloc.replace(".", "-") + ".translate.goog" + path + "?" + query + "&_x_tr_sl=it&_x_tr_tl=en&_x_tr_hl=it&_x_tr_pto=op,wapp"

    def get_anticaptcha_page(url):
        return get_page(get_anticaptcha_url(url))

    def get_n_time_ago(time, time_format):
        d = datetime.today()
        if("min" in time):
            d -= timedelta(hours = 0, minutes = int(time.split(" ")[0]))
        else:
            d -= timedelta(hours = int(time.split(" ")[0]), minutes = 0)
        
        return d.strftime(time_format)

    def today_less_hours(hours):
        return (datetime.today() - timedelta(hours=hours))

    def today_less_one_month():
        date = datetime.today()
        month = (date.month - 2) % 12 + 1
        if(date.month == 1):
            return date.replace(month=month, year=date.year-1)
        return date.replace(month=month)

    def date_to_string(date):
        return date.strftime("%d/%m/%Y")

    def get_idealista_publication_info(room_html):
        detail = room_html.find_all("span", {"item-detail"})[-1]
        if("fumare" in detail.text):
            return ["None", "None"]

        hours_from_pub = detail.find("small", {"class": "txt-highlight-red"})
        if(hours_from_pub):
            return [get_n_time_ago(hours_from_pub.text, '%H:%M'), get_n_time_ago(hours_from_pub.text, '%d/%m/%Y')]

        today = int(date_to_string(datetime.today()).split("/")[0])
        day_pub = today - 1
        if("Inserito" not in detail.text):
            day_pub = int(detail.text.split()[0])
        if(today > day_pub):
            return ["None", date_to_string(datetime.today()).replace(str(today), str(day_pub), 1)]

        return ["None", date_to_string(today_less_one_month()).replace(str(today), str(day_pub), 1)]

    def get_subito_publication_info(room_html):
        publication_info = room_html.find("span", {"class": "index-module_date__Fmf-4"})
        try:
            publication_info = publication_info.get_text().split(" ")
            publication_time = publication_info[-1]
            publication_date = "None"
            if(publication_info[0] == "Oggi"):
                publication_date = date_to_string(datetime.today())
            elif(publication_info[0] == "Ieri"):
                publication_date = date_to_string(today_less_hours(24))
            else:
                month = {
                    "gen": 1,
                    "feb": 2,
                    "mar": 3,
                    "apr": 4,
                    "mag": 5,
                    "giu": 6,
                    "lug": 7,
                    "ago": 8,
                    "set": 9,
                    "ott": 10,
                    "nov": 11,
                    "dic": 12
                }

                publication_date = date_to_string(datetime(datetime.today().year, month[publication_info[1]], int(publication_info[0])))

            return [publication_time, publication_date]
        except:
            return ["None", "None"]

    def get_phone_from_image_url(image_url):
        try:
            from PIL import Image
            import requests
            from io import BytesIO

            import pytesseract
            import cv2
            import numpy as np

            response = requests.get(image_url)
            col = Image.open(BytesIO(response.content))
            gray = col.convert('L')
            bw = gray.point(lambda x: 0 if x < 128 else 255, '1')

            # Make Numpy/OpenCV-compatible version
            image = np.array(bw.convert('RGB'))

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            thresh = 255 - cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

            # Blur and perform text extraction
            thresh = cv2.GaussianBlur(thresh, (3, 3), 0)

            div = cv2.divide(gray, thresh, scale=192)  # added

            data = pytesseract.image_to_string(div, config='--psm 11 digits')
            return "".join(filter(lambda x: x.isdigit() or x == '+', data.strip()))
        except:
            return "None"


    def get_immobiliare_info(url):
        room_page = get_anticaptcha_page(url)

        try:
            sex_ideal_tenant = list(filter(lambda x: "genere" in x.text, room_page.select(".im-features__list")))[0].select(".im-features__value")[0].text.strip()
            if(sex_ideal_tenant == "Femmina"):
                return False
        except:
            pass

        info = []
        
        try:
            phone_image = room_page.select(".im-lead__phone > img")
            phone = get_phone_from_image_url(get_anticaptcha_url(phone_image[0]["src"])) if phone_image else "None"
            info.append(phone)
        except:
            info.append("None")

        try:
            room_id = "".join(filter(lambda x: x.isdigit(), urllib.parse.urlparse(url).path))
            date = list(filter(lambda x: room_id in x.text, room_page.select(".im-features__list")))[0].select(".im-features__value")[0].text.split(" - ")[1].strip()
            info.append(date)
        except:
            info.append("None")

        return info

    def get_text_el(el):
        return el.text if el and el.text else "None"

    def dict_dif(dict1, dict2):
        diff = list(set(dict1) - set(dict2))

        return {key: value for key, value in dict1.items() if key in diff}
    
    def sort_rooms_by_time_and_date(rooms_dict):
        return {k: v for k, v in sorted(rooms_dict.items(), reverse=True, key=lambda item: -1 if item[1][3] == "None" or item[1][4] == "None" else time.mktime(datetime.strptime(item[1][3] + "|" + item[1][4], "%H:%M|%d/%m/%Y").timetuple()))}
    
    def sort_rooms_by_date(rooms_dict):
        return {k: v for k, v in sorted(rooms_dict.items(), reverse=True, key=lambda item: -1 if item[1][4] == "None" else time.mktime(datetime.strptime(item[1][4], "%d/%m/%Y").timetuple()))}
    
    def check_price_range(strprice, min_price, max_price):
        try:
            price = int("".join(filter(lambda x: x.isdigit(), strprice)))
            if(f'''{price}''' in strprice):
                return (price >= min_price and price <= max_price)
        except:
            pass

        return True

    def get_rooms_from_idealista():
        # Idealista
        rooms_data = {}

        page = get_anticaptcha_page(URLS['idealista'])
        
        rooms = page.select(".item-multimedia-container:not(.item_contains_branding)")

        last_check = load_json_from_file('status.json', STATUS_DEFAULT_FORMAT)['idealista']['last_check']
        for room in rooms:
            link = room.find("a", {"class": "item-link"})

            room_url = "https://www.idealista.it%s" % urllib.parse.urlparse(link["href"]).path

            if(room_url in last_check):
                rooms_data[room_url] = last_check[room_url]
                continue

            room_name = get_text_el(link)

            room_price = get_text_el(room.find("span", {"class": "item-price"}))
            if(not check_price_range(room_price, MIN_PRICE, MAX_PRICE)):
                continue

            room_phone = get_text_el(room.find("span", {"class": "icon-phone"}))
            
            pub_info = get_idealista_publication_info(room)
            publication_time = pub_info[0]
            publication_date = pub_info[1]

            rooms_data[room_url] = [room_name, room_price, room_phone, publication_time, publication_date]

        now_time = datetime.now().strftime("%d-%m-%Y_%H:%M:%S")
        print("[%s]:" % now_time)
        
        new_houses = dict_dif(rooms_data, last_check)
        print(json.dumps(new_houses, indent = 4) + "\n")

        status_dict = load_json_from_file('status.json', STATUS_DEFAULT_FORMAT)
        status_dict['idealista']['last_check'] = rooms_data
        status_dict['idealista']['last_check_time'] = now_time
        write_json_to_file('status.json', status_dict)
        
        for url in list(reversed(new_houses.keys())):
            send_everyone(bot, room_to_str(new_houses, url))

    def get_rooms_from_subito():
        #Subito
        rooms_data = {}

        page = get_anticaptcha_page(URLS['subito'] + "&gndr=1")
        man_rooms = list(filter(lambda x: not x.select(".PostingTimeAndPlace-module_vetrina-badge__XWWCm"), page.select(".BigCard-module_link__kVqPE")))
        
        page = get_anticaptcha_page(URLS['subito'] + "&gndr=3")
        both_sexes_rooms = list(filter(lambda x: not x.select(".PostingTimeAndPlace-module_vetrina-badge__XWWCm"), page.select(".BigCard-module_link__kVqPE")))

        rooms = both_sexes_rooms + man_rooms

        last_check = load_json_from_file('status.json', STATUS_DEFAULT_FORMAT)['subito']['last_check']
        for room in rooms:
            room_url = "https://www.subito.it%s" % urllib.parse.urlparse(room["href"]).path

            if(room_url in last_check):
                rooms_data[room_url] = last_check[room_url]
                continue

            room_name = get_text_el(room.find("h2", {"class": "BigCard-module_card-title__Cgcnt"}))

            room_price = get_text_el(room.find("p", {"class": "price"}))
            if(not check_price_range(room_price, MIN_PRICE, MAX_PRICE)):
                continue

            room_phone = "None"
            
            pub_info = get_subito_publication_info(room)
            publication_time = pub_info[0]
            publication_date = pub_info[1]

            rooms_data[room_url] = [room_name, room_price, room_phone, publication_time, publication_date]
        rooms_data = sort_rooms_by_time_and_date(rooms_data)

        now_time = datetime.now().strftime("%d-%m-%Y_%H:%M:%S")
        print("[%s]:" % now_time)
        
        new_houses = dict_dif(rooms_data, last_check)
        print(json.dumps(new_houses, indent = 4) + "\n")

        status_dict = load_json_from_file('status.json', STATUS_DEFAULT_FORMAT)
        status_dict['subito']['last_check'] = rooms_data
        status_dict['subito']['last_check_time'] = now_time
        write_json_to_file('status.json', status_dict)
        
        for url in list(reversed(new_houses.keys())):
            send_everyone(bot, room_to_str(new_houses, url))

    def get_rooms_from_immobiliare():
        # Immobiliare
        rooms_data = {}

        page = get_page(URLS['immobiliare'])
        indifferent_roommates_rooms = list(filter(lambda x: not x.select(".nd-figure"), page.select(".nd-mediaObject__content")))
        
        page = get_page(URLS['immobiliare'] + "&sessoInquilini=M")
        male_roommates_rooms = list(filter(lambda x: not x.select(".nd-figure"), page.select(".nd-mediaObject__content")))

        page = get_page(URLS['immobiliare'] + "&sessoInquilini=F")
        female_roommates_rooms = list(filter(lambda x: not x.select(".nd-figure"), page.select(".nd-mediaObject__content")))

        page = get_page(URLS['immobiliare'] + "&sessoInquilini=E")
        male_female_roommates_rooms = list(filter(lambda x: not x.select(".nd-figure"), page.select(".nd-mediaObject__content")))

        rooms = indifferent_roommates_rooms + male_roommates_rooms + female_roommates_rooms + male_female_roommates_rooms
  
        last_check = load_json_from_file('status.json', STATUS_DEFAULT_FORMAT)['immobiliare']['last_check']
        for room in rooms:
            link = room.find("a", {"class": "in-card__title"})
            room_url = link["href"]
            
            if(room_url in last_check):
                rooms_data[room_url] = last_check[room_url]
                continue

            room_name = get_text_el(link)

            room_price = get_text_el(room.find("li", {"class": "in-realEstateListCard__features--main"}))
            if(not check_price_range(room_price, MIN_PRICE, MAX_PRICE)):
                continue
                
            room_info = get_immobiliare_info(room_url)
            if(not room_info):
                continue

            room_phone = room_info[0]
            
            publication_time = "None"
            publication_date = room_info[1]

            rooms_data[room_url] = [room_name, room_price, room_phone, publication_time, publication_date]
        rooms_data = sort_rooms_by_date(rooms_data)

        now_time = datetime.now().strftime("%d-%m-%Y_%H:%M:%S")
        print("[%s]:" % now_time)
        
        new_houses = dict_dif(rooms_data, last_check)
        print(json.dumps(new_houses, indent = 4) + "\n")

        status_dict = load_json_from_file('status.json', STATUS_DEFAULT_FORMAT)
        status_dict['immobiliare']['last_check'] = rooms_data
        status_dict['immobiliare']['last_check_time'] = now_time
        write_json_to_file('status.json', status_dict)
        
        for url in list(reversed(new_houses.keys())):
            send_everyone(bot, room_to_str(new_houses, url))

    while(True):
        get_rooms_from_idealista()
        time.sleep((8 + random.randint(-3, 3)) * 60)

        get_rooms_from_subito()  
        time.sleep((8 + random.randint(-3, 3)) * 60)
        
        get_rooms_from_immobiliare()
        time.sleep((8 + random.randint(-3, 3)) * 60)