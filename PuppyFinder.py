from bs4 import BeautifulSoup
import requests
import urllib.request as urllib2
import logging
import csv

from fbase import get_host, sod_location, sod_remove_key, sod_get_price, computeMD5hash, db_connection
from pathlib import Path
import time
import datetime


class PuppyFinder:
    def __init__(self, url):
        self._url = url

        self._file = "fpuppyfinder.txt"
        self._db = "db1.csv"
        self._cnx = False

        my_file = Path(self._file)
        if not my_file.is_file():
            file1 = open(self._file, "w+")
            file1.write('')
            file1.close()

        self._host = get_host(url)
        
        # file1 = open(self._file, "w+")
        # file1.write('')
        # file1.close()

    
    def parse(self, bs):
        
        if (bs):
            # content = self._bs.find("div", {"id": "block-system-main"}).find_all(class_=".field-content")
            content = bs.select('.pf-cards-list1 .pf-card-list-wrapper .pf-pseudo-card')
           
            if (content):
                urllist = []
                for entry in content:
                    urllist.append(entry.get("href") + "\n")
                
                f = open(self._file, "a+")
                f.writelines(urllist)
                f.close()
    
    def pages(self):
        try:
            bs = None
            result = urllib2.urlopen(self._url)
            rcontent = result.read()           
            if (rcontent):            
                bs = BeautifulSoup(rcontent, 'html.parser')

            if (bs):                
                content = bs.select(".pager .next a")
                if (len(content)):
                    next = content[0].get("href")
                    # print(next)
                    self.parse(bs)
                    if (self._url != next):
                        self._url =  next
                        self.pages()
                else:
                    self.parse(bs)        
        except:
            logging.warning(self._url)

    
    def sub_parse(self, bs):
        title = ""
        price = ""
        sex = ""
        color = ""
        size = ""
        img_url = ""

        content = bs.select(".pf-content > div.pf-section-mod")
        url = bs.select_one(".pf-details-main-info--litter-item .pf-puppy-media .pf-card-img img")
        img_url = url.get("src").strip()

        if (content and len(content) > 1):
            sub_content = content[1].select(".pf-data-list--main-info > li")
            for item in sub_content:
                text = item.text.strip()
                if (text.find("Nickname:") != -1):
                    title = sod_remove_key(text, "Nickname:")

                if (text.find("Price:") != -1):
                    price = sod_get_price(sod_remove_key(text, "Price:"))

                if (text.find("Gender") != -1):
                    sex = sod_remove_key(text, "Gender")

                if (text.find("Color/ Markings:") != -1):
                    color = sod_remove_key(text, "Color/ Markings:")
                
                if (text.find("Size at Maturity:") != -1):
                    size = sod_remove_key(text, "Size at Maturity:")
        return {
            'title': title,
            'price': price,
            'sex': sex,
            'color': color,
            'size': size,
            "img_url":  img_url
        }
    
    def parse_page(self, url):
        
        bs = None
        # req =  requests.get(url)
        # print(req.status_code)
        result = urllib2.urlopen(url)
        rcontent = result.read()

        title = ""
        price = 0
        sex = ""
        age = ""
        date_available = ""
        shipping = ""
        payment = ""
        color = ""
        size = ""

        if (rcontent):            
            bs = BeautifulSoup(rcontent, 'html.parser')
            
            if (bs):
                img_url = bs.select_one(".pf-details-main-info .pf-card-img img")
                img_url = "" if (img_url is None) else img_url.get("src").strip()
                
                info = bs.select_one(".pf-details-main-info")                
                
                # title = info.select_one(".pf-puppy-info-name h1")
                # title = "" if (title is None) else title.text.strip().lower()

                
                location = info.select_one(".pf-puppy-info-name p")
                location = "" if (location is None) else location.text.strip()

                if (location):
                    location = sod_location(location, 2)

                main_info = info.select(".pf-data-list--main-info > li")
                # .pf-litter-slider-wrapper

                for item in main_info:
                    text = item.text.strip()                    

                    if (text.find("Gender") != -1):
                        sex = sod_remove_key(text, "Gender")
                    
                    if (text.find("Age") != -1):
                        age = sod_remove_key(text, "Age")
                    
                    if (text.find("Availability Date:") != -1):
                        date_available = sod_remove_key(text, "Availability Date:")
                    
                    if (text.find("Color/ Markings:") != -1):
                        color = sod_remove_key(text, "Color/ Markings:")
                    
                    if (text.find("Size at Maturity:") != -1):
                        size = sod_remove_key(text, "Size at Maturity:").lower()

                    if (text.find("Shipping Area:") != -1):
                        shipping = sod_remove_key(text, "Shipping Area:")

                    if (text.find("Payment Method:") != -1):
                        payment = sod_remove_key(text, "Payment Method:")

                    if (text.find("Nickname:") != -1):
                        title = sod_remove_key(text, "Nickname:")

                    if (text.find("Price:") != -1):
                        price = sod_get_price(sod_remove_key(text, "Price:"))

                
                city = ""
                state = ""
                

                if (location):
                    city = location["city"]
                    state = location["state"]                
                
                sex = sex.lower()

                if sex == "male":
                    sex = 1
                elif sex == "female":
                    sex = 0
                else:
                    sex = 2
                
                age = age.lower()
                if (age.find("months") >= 0):
                    age = age.split("months")
                    age = int(age[0].strip()) * 4

                else:
                    age = age.split("weeks")
                    age = int(age[0].strip())

                date_available =  datetime.datetime.strptime(date_available, "%m/%d/%Y").strftime("%Y-%m-%d")


                if price == 0:
                    sub_carousel = []
                    carousel = bs.select_one(".pf-content > div.pf-section-mod .pf-litter-slider-wrapper .pf-cards-wrapper")
                    if (carousel):
                        sub_carousel = carousel.select("a.pf-card")

                    res = self.sub_parse(bs)
                    # print(res)
                    title = res["title"]
                    price = res["price"]
                    sex = res["sex"]
                    color = res["color"]
                    size = res["size"]
                    img_url = res["img_url"]
                                    
                    line = "'{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}', '{8}', '{9}', '{10}', '{11}', '{12}', '{13}'".format(
                            computeMD5hash(url),
                            url,
                            img_url,
                            title,
                            price,
                            age, 
                            sex,
                            size,
                            color,
                            city,
                            state,                        
                            date_available,
                            payment,
                            shipping
                        )
                        
                    # print(line)
                    self.write_text(line + "\n")
                    
                    for c in sub_carousel:
                        s_url = c.get("href")
                        if (s_url):
                            result = urllib2.urlopen(s_url)
                            rcontent = result.read()

                            if (rcontent):            
                                bs = BeautifulSoup(rcontent, 'html.parser')

                                if (bs):
                                    res = self.sub_parse(bs)
                                    # print(res)
                                    title = res["title"]
                                    price = res["price"]
                                    sex = res["sex"]
                                    color = res["color"]
                                    size = res["size"]
                                    img_url = res["img_url"]

                                    line = "'{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}', '{8}', '{9}', '{10}', '{11}', '{12}', '{13}'".format(
                                            computeMD5hash(s_url),
                                            s_url,
                                            img_url,
                                            title,
                                            price,
                                            age, 
                                            sex,
                                            size,
                                            color,
                                            city,
                                            state,                        
                                            date_available,
                                            payment,
                                            shipping
                                        )
                                        
                                    # print(line)
                                    self.write_text(line + "\n")
                                    
                        time.sleep(0.1)

                    return

                if not title:
                    title = bs.select_one("span.pf-litter-img-label").text.strip()
                # price = "" if (main_info[0] is None) else main_info[0].text.strip()

                # sex = "" if (main_info[2] is None) else main_info[2].text.strip()

                # age = "" if (main_info[3] is None) else main_info[3].text.strip()

                
                # date_available = "" if (main_info[4] is None) else main_info[4].text.strip()

                # shipping = "" if (main_info[5] is None) else main_info[5].text.strip()
                
                # print(img_url, title, age, sex,  price, city, state, color, date_available, shipping, payment)
                line = "'{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}', '{8}', '{9}', '{10}', '{11}', '{12}', '{13}'".format(
                        computeMD5hash(url),
                        url,
                        img_url,
                        title,
                        price,
                        age, 
                        sex,
                        size,
                        color,
                        city,
                        state,                        
                        date_available,
                        payment,
                        shipping
                    )
                    
                # print(line)
                self.write_text(line + "\n")
                
    
    def write_text(self, line, truncate = 0):
        if (truncate > 0):
            open(self._db, "w").close()
            return
        
        with open(self._db, 'a+') as f:
            f.write(line)

    def read_all(self):
        f = open(self._file, 'r+')
        lines = [line for line in f.readlines()]
        f.close()
        i = 0

        self.write_text("", 1)
        self.write_text("`{0}`, `{1}`, `{2}`, `{3}`, `{4}`, `{5}`, `{6}`, `{7}`, `{8}`, `{9}`, `{10}`, `{11}`, `{12}`, `{13}`\n".format(
                        "product_id",
                        "product_url",
                        "img_url",
                        "title",
                        "price",
                        "age",                        
                        "sex",
                        "size",
                        "color",
                        "city",
                        "state",
                        "date_available", 
                        "payment",
                        "shipping"
                    ))

        for url in lines:            
            if (url):
                try:
                    self.parse_page(url.strip())
                    i += 1
                except:
                    logging.warning(url.strip())
            
            if i > 2:
                break
    
    def update_db(self):
        sql = "INSERT INTO products({0}) VALUES"
        elements = []
        delete_items = []
        price_table = []

        with open(self._db) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            line_count = 0
            for row in csv_reader:
                if (line_count == 0):
                    sql = sql.format(",".join(row))
                    line_count += 1
                else:
                    elements.append("(" + ",".join(row) + ")")
                    delete_items.append(row[0])
                    price_table.append("({0}, {1})".format(row[0], row[4]))
        
        delete_sql = "DELETE FROM products WHERE product_id in ({0})".format(",".join(delete_items))        
        insert_sql = sql + ",".join(elements)
        insert_price_sql  = "INSERT INTO price_history(`product_id`, `price`) VALUES" + ",".join(price_table)

        # print(delete_sql)
        # print(insert_sql)
        # print(insert_price_sql)
        open(self._file, "w").close()
        
        try:
            if not self._cnx:
                self._cnx = db_connection()
            
            if self._cnx:
                cursor = self._cnx.cursor()
                if (len(delete_items) > 0):
                    cursor.execute(delete_sql)                    
                    self._cnx.commit()                    
                
                if (len(elements) > 0):
                    cursor.execute(insert_sql)
                    self._cnx.commit()

                if (len(price_table) > 0):
                    cursor.execute(insert_price_sql)
                    self._cnx.commit()
                
                self._cnx.close()

        except Exception as e:
            self._cnx.rollback()
            print(e)
