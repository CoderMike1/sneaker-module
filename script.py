import time
import os
import html
import json
import random
from bs4 import BeautifulSoup
import requests
from concurrent.futures import ThreadPoolExecutor
from colorama import Fore,init
from datetime import datetime
import pandas as pd
from tools import log, phone_prefix,USER_AGENT,change_console_title,SITE,bae_sizes,mens_sizes,big_foot_sizes,sizes
from discord_webhook import DiscordWebhook,DiscordEmbed
import pyfiglet
init()
carted = success =failed =tasks =0

class Program:
    def __init__(self,num):
        self.num = num +1
        self.session = requests.Session()

        tasks_data = pd.read_csv(f"tasks.csv", na_filter=False, dtype=str).iloc[num]

        self.link = tasks_data['Link']
        self.size = tasks_data['Size']
        self.quantity = "1" if tasks_data['Quantity'] == "" else tasks_data['Quantity']
        self.delay = "5" if tasks_data['Delay'] == "" else tasks_data['Delay']
        self.proxy_file_name = None if tasks_data['Proxy'] == "" else tasks_data['Proxy']

        self.email = tasks_data['Email']
        self.first_name = tasks_data['First Name']
        self.surname = tasks_data['Last Name']
        self.street = tasks_data['Street']
        self.house_number = tasks_data['House Number']
        self.apartment_number = tasks_data['Apartment Number']
        self.city = tasks_data['City']
        self.zip_code = tasks_data['Zip Code']

        self.country = tasks_data['Country'].upper()
        self.phone_number = tasks_data['Phone Number']

        self.webhookURL = tasks_data["Discord Webhook URL"]

        if self.zip_code.find("-") == -1 and self.zip_code.find(" ") ==-1 and self.country.upper() == "CZ":
            self.zip_code = f"{self.zip_code[:3]} {self.zip_code[3:]}"

        if self.zip_code.find("-") == -1 and self.country.upper() =="PL":
            self.zip_code = f"{self.zip_code[:2]}-{self.zip_code[2:]}"

        self.countryData = {
            "AT": {"domain": "www.breuninger.com/at", "delivery_option": 'STANDARD_POST_AT',
                   "prefix": phone_prefix['AT'], "country_code": "AUT"},
            "BE": {"domain": "www.breuninger.com/be/en", "delivery_option": "STANDARD_DHL",
                   "prefix": phone_prefix['BE'], "country_code": "BEL"},
            "CH": {"domain": "www.breuninger.com/ch", "delivery_option": "STANDARD_POST_CH",
                   "prefix": phone_prefix['CH'], "country_code": "CHE"},
            "CZ": {"domain": "www.breuninger.com/cz", "delivery_option": "STANDARD_DHL", "prefix": phone_prefix['CZ'],
                   "country_code": "CZE"},
            "DE": {"domain": "www.breuninger.com/de", "delivery_option": "STANDARD_DHL", "prefix": phone_prefix['DE'],
                   "country_code": "DEU"},
            "ES": {"domain": "www.breuninger.com/es/en", "delivery_option": "STANDARD_DHL",
                   "prefix": phone_prefix['ES'], "country_code": "ESP"},
            "IT": {"domain": "www.breuninger.com/it/en", "delivery_option": "STANDARD_DHL",
                   "prefix": phone_prefix['IT'], "country_code": "ITA"},
            "NL": {"domain": "www.breuninger.com/nl/en", "delivery_option": "STANDARD_DHL",
                   "prefix": phone_prefix['NL'], "country_code": "NLD"},
            "PL": {"domain": "www.breuninger.com/pl", "delivery_option": "STANDARD_INPOST",
                   "prefix": phone_prefix['PL'], "country_code": "POL"}
        }

        self.headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "upgrade-insecure-requests": "1",
            "user-agent": USER_AGENT
        }
        if self.proxy_file_name != None:
            self.proxy = self.proxy_file_name
            ok = self.proxy.split(":")
            pierwszy = ok[0]
            drugi = ok[1]
            trzeci = ok[2]
            czwarty = ok[3]

            self.proxies = {
                "http": "http://" + trzeci + ":" + czwarty + "@" + pierwszy + ":" + drugi,
                "https": "http://" + trzeci + ":" + czwarty + "@" + pierwszy + ":" + drugi,
            }
        else:
            self.proxies = None
            self.proxy = None

    def run(self):
        return self.add_to_cart()
    def add_to_cart(self):
        global failed
        global carted
        global tasks
        global success
        while True:
            log(f"[1/6][TASK {str(self.num)}]Loading product page...",
                Fore.MAGENTA, SITE)
            try:
                r = self.session.get(self.link,headers=self.headers,proxies=self.proxies)
            except requests.exceptions:
                log(f"[1/6][TASK {str(self.num)}]Proxy error while connecting to the site, retring in 3 seconds...[01]",
                    Fore.RED, SITE)
                time.sleep(3)
            else:
                if r.status_code != 200:
                    log(f"[1/6][TASK {str(self.num)}]Wrong site status, retrying in 3 seconds...[01]",
                        Fore.RED, SITE)
                    time.sleep(3)
                else:
                    soup = BeautifulSoup(r.text, "html.parser")
                    data_vertr = soup.find("script", {"id": "entsProductData"})
                    data_encoded_vertr = html.unescape(data_vertr.string)
                    data_json_vertr = json.loads(data_encoded_vertr)
                    data = soup.find("script", {"id": "brtn-product-data"})
                    try:
                        data_json = json.loads(data.string)
                    except AttributeError or TypeError or KeyError:
                        log(f"[1/6][TASK {str(self.num)}]Attribute error, retrying...",
                            Fore.RED, SITE)
                        time.sleep(3)
                    else:
                        try:
                            sizes_list = data_json["colors"][1]["sizes"]
                        except IndexError:
                            try:
                                sizes_list = data_json["colors"][0]["sizes"]
                            except IndexError:
                                log(f"[1/6][TASK {str(self.num)}]Product OOS, retrying...",
                                    Fore.RED, SITE)
                                return self.add_to_cart()
                            else:
                                pass
                        finally:
                            data6 = {}
                            data = []
                            data2 = []
                            data3 = []
                            for x in sizes_list:
                                size_string = x["size"].replace(",", ".")
                                data3.append(size_string)
                                stock = x["stock"]
                                if stock > 0:
                                    nummer = x["articleId"]
                                    for y in data_json_vertr["artikel"]:
                                        if y == nummer:
                                            vertriebsinfoId = data_json_vertr["artikel"][y]["vertriebsinfoId"]
                                    # vertriebsinfoId = x["salesId"]
                                    data2.append(size_string)
                                    data6.update(
                                        {size_string: {"nummer": nummer, "to_drugie": vertriebsinfoId, "quantity": stock}})
                                    zip = {size_string: nummer}
                                    wybor = zip.get(self.size)
                                    if wybor != None:
                                        self.size_string = self.size
                                        break
                            if self.size.find("-") != -1:
                                first = self.size.split("-")[0]
                                second = self.size.split("-")[1]
                                try:
                                    for y in sizes[sizes.index(first):sizes.index(second) + 3]:
                                        tr = data6.get(y)
                                        if tr != None:
                                            data.append(y)
                                except ValueError:
                                    log(f"[1/6][TASK {str(self.num)}]{first} or {second} aren't indexed in size range, make sure that you don't put size in formats (ex. 40.0 or 40_0 or 40_23 or 40.23) , correct formats are (ex. 40 or 40.5 or 40 2/3 ) , if you use correct format, please contact do DEV",
                                        Fore.RED, SITE)
                                    time.sleep(50)
                                    sys.exit(0)
                                data2 = data
                            if self.size.find(';') != -1:
                                listt = self.size.split(';')
                                for y in listt:
                                    tr = data6.get(y)
                                    if tr != None:
                                        data.append(y)
                                data2 = data

                            if self.size.lower() == 'bae':
                                for y in bae_sizes:
                                    tr = data6.get(y)
                                    if tr != None:
                                        data.append(y)
                                data2 = data

                            if self.size.lower() == 'mens':
                                for y in mens_sizes:
                                    tr = data6.get(y)
                                    if tr != None:
                                        data.append(y)
                                data2 = data
                            if self.size.lower() == 'big foot':
                                for y in big_foot_sizes:
                                    tr = data6.get(y)
                                    if tr != None:
                                        data.append(y)

                                data2 = data
                            if data2 == [] and data == []:
                                if self.size.lower() == 'mens' \
                                        or self.size.lower() == "bae" or self.size.lower() == "big foot":
                                    log(f"[1/6][TASK {str(self.num)}]{self.size} sizes OOS, retrying in {self.delay} seconds...",
                                        Fore.RED, SITE)
                                else:
                                    if self.size.find(';') != -1:
                                        log(f"[1/6][TASK {str(self.num)}]Selected sizes OOS, retrying in {self.delay} seconds...",
                                            Fore.RED, SITE)
                                    else:
                                        log(f"[1/6][TASK {str(self.num)}]Product OOS, retrying in {self.delay} seconds...",
                                            Fore.RED, SITE)


                                time.sleep(int(self.delay))
                            else:
                                if self.size != '' and wybor == None and data3.count(self.size) != 0:
                                    log(f"[1/6][TASK {str(self.num)}]Specific size OOS, retrying in {self.delay} seconds...",
                                        Fore.RED, SITE)
                                    time.sleep(int(self.delay))
                                else:
                                    if self.size == '' or wybor == None:
                                        try:
                                            zakres = len(data2)
                                            wyboor = random.randint(0, int(zakres))
                                            self.size_string = data2[int(wyboor)]
                                        except IndexError or UnboundLocalError:
                                            return self.add_to_cart()

                                    self.real_qt = data6[self.size_string]["quantity"] if data6[self.size_string][
                                                                                              "quantity"] < int(
                                        self.quantity) else int(self.quantity)

                                    atc_body = {"nummer": data6[self.size_string]["nummer"],
                                                "vertriebsinfoId": data6[self.size_string]["to_drugie"],
                                                "anzahl": self.real_qt,
                                                "groessenBerater": {"supported": True, "bereitsVerwendet": False}}
                                    atc_headers = {
                                        "accept": "*/*",
                                        "content-type": "application/vnd.position+json",
                                        "x-requested-with": "XMLHttpRequest",
                                        "user-agent": USER_AGENT
                                    }
                                    log(f"[1/6][TASK {str(self.num)}]Adding size {self.size_string} to the cart...",
                                        Fore.MAGENTA, SITE)
                                    try:
                                        p = self.session.post(
                                            f"https://{self.countryData[self.country]['domain']}/kauf/addToCart",
                                            json=atc_body, headers=atc_headers, proxies=self.proxies)
                                    except requests.exceptions.ProxyError or requests.exceptions.SSLError or requests.exceptions.ConnectionError or requests.exceptions.HTTPError or requests.exceptions.ConnectTimeout:
                                        log(f"[1/6][TASK {str(self.num)}]Proxy error while connecting to the site, retring in 3 seconds...[01]",
                                            Fore.RED, SITE)
                                        time.sleep(3)
                                    else:
                                        if p.status_code != 201:
                                            log(f"[1/6][TASK {str(self.num)}]Wrong site status, retrying in 3 seconds...[01]",
                                                Fore.RED, SITE)
                                            time.sleep(3)
                                        else:
                                            carted +=1
                                            change_console_title(SITE, tasks, failed, success, carted)
                                            self.product_name = soup.find("meta", {"property": "og:title"})[
                                                "content"].upper()
                                            self.product_image = soup.find("meta", {"property": "og:image"})["content"]
                                            self.product_price = json.loads(p.text)["minicart"]["total"]
                                            return self.cart_step()

    def cart_step(self):
        global failed
        global carted
        global tasks
        global success
        while True:
            log(f"[2/6][TASK {str(self.num)}]Filling address information...",
                Fore.MAGENTA, SITE)
            cart_data = {
                "anrede": "Frau",
                "titel": "",
                "vorname": self.first_name,
                "nachname": self.surname,
                "adresszeile1": self.street,
                "adresszusatz": self.house_number+"/"+self.apartment_number,
                "plz": self.zip_code,
                "ort": self.city,
                "landiso3": self.countryData[self.country]['country_code'],
                "_droptext": "",
                "email": self.email,
                "telefon": self.phone_number,
                "geburtsdatum": ""
            }

            cart_headers = {
                "content-type": "application/x-www-form-urlencoded",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7   ",
                "user-agent": USER_AGENT
            }
            try:
                p = self.session.post(f"https://{self.countryData[self.country]['domain']}/kauf/contact",
                                      headers=cart_headers, data=cart_data, proxies=self.proxies)
            except requests.exceptions.ProxyError or requests.exceptions.SSLError or requests.exceptions.ConnectionError or requests.exceptions.HTTPError or requests.exceptions.ConnectTimeout:
                log(f"[2/6][TASK {str(self.num)}]Proxy error while connecting to the site, retring in 3 seconds...[01]",
                    Fore.RED, SITE)
                time.sleep(3)
            else:
                if p.url == f"https://{self.countryData[self.country]['domain']}/kauf/cart":
                    log(f"[2/6][TASK {str(self.num)}]Product OOS, retrying...",
                        Fore.RED, SITE)
                    carted -= 1
                    failed += 1
                    change_console_title(SITE, tasks, failed, success, carted)
                    return self.add_to_cart()
                else:
                    if p.status_code != 200:
                        log(f"[2/6][TASK {str(self.num)}]Wrong site status, retrying in 3 seconds...[01]",
                            Fore.RED, SITE)
                    else:
                        return self.delivery_step()

    def delivery_step(self):
        global failed
        global carted
        global tasks
        global success
        while True:
            log(f"[3/6][TASK {str(self.num)}]Filling delivery information...",
                Fore.MAGENTA, SITE)
            delivery_body = {
                "versandOption": self.countryData[self.country]['delivery_option'],
                "lieferorttyp": ""
            }
            delivery_headers = {
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                'content-type': "application/x-www-form-urlencoded",
                "user-agent": USER_AGENT
            }
            try:
                p = self.session.post(f"https://{self.countryData[self.country]['domain']}/kauf/delivery",
                                      data=delivery_body, headers=delivery_headers, proxies=self.proxies)
            except requests.exceptions.ProxyError or requests.exceptions.SSLError or requests.exceptions.ConnectionError or requests.exceptions.HTTPError or requests.exceptions.ConnectTimeout:
                log(f"[3/6][TASK {str(self.num)}]Proxy error while connecting to the site, retring in 3 seconds...[01]",
                    Fore.RED, SITE)
                time.sleep(3)
            else:
                if p.url == f"https://{self.countryData[self.country]['domain']}/kauf/cart":
                    log(f"[3/6][TASK {str(self.num)}]Product OOS, retrying...",
                        Fore.RED, SITE)
                    carted -= 1
                    failed += 1
                    change_console_title(SITE, tasks, failed, success, carted)
                    return self.add_to_cart()
                else:
                    if p.status_code != 200:
                        log(f"[3/6][TASK {str(self.num)}]Wrong site status, retrying in 3 seconds...[01]",
                            Fore.RED, SITE)
                        time.sleep(3)
                    else:
                        return self.payment_step()
    def payment_step(self):
        global failed
        global carted
        global tasks
        global success
        while True:
            log(f"[4/6][TASK {str(self.num)}]Filling payment information...",
                Fore.MAGENTA, SITE)
            payment_body = {
                "zahlart": "paypal"
            }
            payment_headers = {
                "content-type": "application/x-www-form-urlencoded",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "user-agent": USER_AGENT
            }
            try:
                p = self.session.post(f"https://{self.countryData[self.country]['domain']}/kauf/paymentMethod",
                                      data=payment_body, headers=payment_headers, proxies=self.proxies)
            except requests.exceptions.ProxyError or requests.exceptions.SSLError or requests.exceptions.ConnectionError or requests.exceptions.HTTPError or requests.exceptions.ConnectTimeout:
                log(f"[5/6][TASK {str(self.num)}]Proxy error while connecting to the site, retring in 3 seconds...[01]",
                    Fore.RED, SITE)
                time.sleep(3)
            else:
                if p.url == f"https://{self.countryData[self.country]['domain']}/kauf/cart":
                    log(f"[4/6][TASK {str(self.num)}]Product OOS, retrying...",
                        Fore.RED, SITE)
                    carted -= 1
                    failed += 1
                    change_console_title(SITE, tasks, failed, success, carted)
                    return self.add_to_cart()
                else:
                    if p.status_code != 200:
                        log(f"[4/6][TASK {str(self.num)}]Wrong site status, retrying in 3 seconds...[01]",
                            Fore.RED, SITE)
                        if self.proxy != None:
                            self.proxies = self.rotating_proxy()
                        time.sleep(3)
                    else:
                        return self.summary_step()
    def summary_step(self):
        global failed
        global carted
        global tasks
        global success
        while True:
            log(f"[5/6][TASK {str(self.num)}]Finalizing the order...",
                Fore.MAGENTA, SITE)
            try:
                r = self.session.get(f"https://{self.countryData[self.country]['domain']}/kauf/lastCheck",
                                     headers=self.headers, proxies=self.proxies)
            except requests.exceptions.ProxyError or requests.exceptions.SSLError or requests.exceptions.ConnectionError or requests.exceptions.HTTPError or requests.exceptions.ConnectTimeout:
                log(f"[5/6][TASK {str(self.num)}]Proxy error while connecting to the site, retring in 3 seconds...[01]",
                    Fore.RED, SITE)
                if self.proxy != None:
                    self.proxies = self.rotating_proxy()
                time.sleep(3)
            else:
                if r.url == f"https://{self.countryData[self.country]['domain']}/kauf/cart":
                    log(f"[5/6][TASK {str(self.num)}]Product OOS, retrying...",
                        Fore.RED, SITE)
                    carted -= 1
                    failed += 1
                    change_console_title(SITE, tasks, failed, success, carted)
                    return self.add_to_cart()
                else:
                    if r.status_code != 200:
                        log(f"[5/6][TASK {str(self.num)}]Wrong site status, retrying in 3 seconds...[01]",
                            Fore.RED, SITE)
                        if self.proxy != None:
                            self.proxies = self.rotating_proxy()
                        time.sleep(3)
                    else:
                        soup = BeautifulSoup(r.text, "html.parser")
                        data = soup.find("script", {"id": "warenkorbJson"})
                        data_json = json.loads(data.string)
                        lieferzeitenJson = data_json["lieferzeitenJson"]

                        summary_body = {
                            "lieferzeitenJson": lieferzeitenJson,
                            "agb": True,
                            "zahlart": "",
                            "geschenkkarte": "",
                            "geburtsdatum": ""
                        }
                        summary_headers = {
                            'content-type': "application/x-www-form-urlencoded",
                            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                            "user-agent": USER_AGENT
                        }
                        try:
                            p = self.session.post(f"https://{self.countryData[self.country]['domain']}/kauf/paypal",
                                                  data=summary_body, headers=summary_headers)
                        except requests.exceptions.ProxyError:
                            log(f"[5/6][TASK {str(self.num)}]Proxy error while connecting to the site, retring in 3 seconds...[01]",
                                Fore.RED, SITE)
                            if self.proxy != None:
                                self.proxies = self.rotating_proxy()
                            time.sleep(3)
                        else:
                            self.p21 = datetime.today()
                            if p.url == f"https://{self.countryData[self.country]['domain']}/kauf/cart" or p.url.find(
                                    "www.paypal.com") == -1:
                                log(f"[5/6][TASK {str(self.num)}]Product OOS, retrying...",
                                    Fore.RED, SITE)
                                carted -= 1
                                failed += 1
                                change_console_title(SITE, tasks, failed, success, carted)
                                return self.add_to_cart()
                            else:
                                log(f"[6/6][TASK {str(self.num)}]The product was purchased! Check the webhook...",
                                    Fore.GREEN, SITE)
                                carted -= 1
                                success += 1
                                change_console_title(SITE, tasks, failed, success, carted)
                                self.payment_link = p.url
                                return self.send_webhook()
    def send_webhook(self):
        if self.webhookURL != "":
            webhook = DiscordWebhook(url=self.webhookURL, rate_limit_retry=True)
            embed = DiscordEmbed(title=self.product_name, color='c852f3',
                                 url=self.link)
            embed.set_thumbnail(
                url=self.product_image)
            embed.set_author(name="THE PRODUCT WAS PURCHASED!")
            embed.add_embed_field(name="Email:", value=f"||{self.email}||")
            embed.add_embed_field(name="Size:", value=f"{self.size_string} EU")
            embed.add_embed_field(name="Total Price:",
                                  value=f"{self.product_price}")
            embed.add_embed_field(name="Quantity:", value=self.real_qt, inline=False)
            embed.add_embed_field(name="Payment Link:", value='[Click here](' + self.payment_link + ')')
            embed.add_embed_field(name="Proxy:", value=f"||{self.proxy}||", inline=False)
            embed.add_embed_field(name="Store:", value=f"||Breuninger {self.country}||")
            embed.set_timestamp()
            embed.set_footer(text=f"Module made by CoderMike1")
            webhook.add_embed(embed)
            response = webhook.execute()
        else:
            log(f"[6/6][TASK {str(self.num)}]Checkout link : {self.payment_link}",
                Fore.GREEN, SITE)

        time.sleep(3600)
        sys.exit(0)


def run_tasks():
    global tasks
    print()
    tasks_amount = len(pd.read_csv(f"tasks.csv", na_filter=False, dtype=str))
    tasks = tasks_amount
    change_console_title(SITE, tasks, failed, success, carted)
    with ThreadPoolExecutor(max_workers=tasks) as executor:
        for i in range(tasks_amount):
            executor.submit(Program(i).run)

    print()
    print()
    log(f"All tasks completed.",
        Fore.GREEN, SITE)
    time.sleep(600)

if __name__ == "__main__":
    while True:
        ascii_art = pyfiglet.figlet_format(f"Breuninger Module", font="larry3d", width=210, justify="left").rstrip()
        print(f"{Fore.BLUE}{ascii_art}{Fore.RESET}")
        print()
        print(f"{Fore.YELLOW}Created by CoderMike1")
        print()
        print(f"{Fore.GREEN}Choose option:")
        print(f"{Fore.WHITE}1.Run tasks")
        print(f"{Fore.RED}2.Quit")

        choice = input("")

        if choice == "1":
            run_tasks()
        elif choice == "2":
            print("Exiting in 3 seconds...")
            time.sleep(3)
            sys.exit(0)
        else:
            print("unknown command...")
            time.sleep(1)
            os.system('cls' if os.name == 'nt' else 'clear')