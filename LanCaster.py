from bs4 import BeautifulSoup
import csv
import requests
import urllib.request as urllib2
from fbase import get_host, computeMD5hash, sod_location, db_connection
import logging
import time

class LanCaster:
    def __init__(self, url):
        self._url = url

        self._file = "filelist.txt"
        self._db = "db.csv"
        self._host = get_host(url)
        self._cnx = False
        # file1 = open(self._file, "w+")
        # file1.write('')
        # file1.close()

    
    def parse(self, bs):
        
        if (bs):
            # content = self._bs.find("div", {"id": "block-system-main"}).find_all(class_=".field-content")
            content = bs.select_one('#block-system-main .view-content')
            content = content.select('.views-field-title a')
            if (content):
                urllist = []
                for entry in content:
                    urllist.append(self._host + entry.get("href") + "\n")
                
                f = open(self._file, "a+")
                f.writelines(urllist)
                f.close()
    
    def pages(self):
        
        bs = None
        self._req =  requests.get(self._url)
        if (self._req.status_code == 200):            
            bs = BeautifulSoup(self._req.content, 'html.parser')

        if (bs):
            content = bs.select(".pagination .next a")
            if (len(content)):
                next = content[0].get("href")
                # print(next)
                self.parse(bs)
                self._url = self._host + next                
                self.pages()
            else:
                self.parse(bs)
    
    
    def parse_page(self, url):
        try:
            bs = None
            # req =  requests.get(url)
            # print(req.status_code)
            result = urllib2.urlopen(url)
            rcontent = result.read()

            if (rcontent):            
                bs = BeautifulSoup(rcontent, 'html.parser')
                
                if (bs):
                    img_url = bs.select_one("#block-system-main .puppy__images img")
                    img_url = "" if (img_url is None) else img_url.get("src")
                    
                    info = bs.select_one("#block-system-main .puppy__info")                

                    price = info.select_one(".puppy_price_seller .current_price")
                    price = 0 if (price is None) else float(price.text.strip())

                    title = info.select_one(".title h2")
                    title = "" if (title is None) else title.text.strip().lower()

                    age = info.select_one(".age-in-weeks")
                    age = "" if (age is None) else age.text.strip()
                    age = age.split("wks")[0]

                    sex = info.select_one(".field-name-field-sex .field-items .field-item")
                    sex = "" if (sex is None) else sex.text.strip()

                    size = info.select_one(".field-name-field-size .field-items .field-item")
                    size = "" if (size is None) else size.text.strip().lower()

                    location = info.select_one(".field-name-field-dog-location .field-items .field-item")
                    location = "" if (location is None) else location.text.strip()

                    bod = info.select_one(".field-name-field-birth-date .date-display-single")
                    bod = "" if (bod is None) else bod.get("content")
                    bod = bod[:10]

                    date_available = info.select_one(".field-name-field-date-available .date-display-single")
                    date_available = "" if (date_available is None) else date_available.get("content")
                    date_available = date_available[:10]

                    registration  = info.select_one(".field-name-field-registration .field-items .field-item")
                    registration = "" if (registration is None) else registration.text.strip()

                    sex = 1 if sex.lower() == "male" else 0

                    # print(img_url, title, age, sex, size, location, bod, date_available, registration)
                    loc = sod_location(location, 1)
                    state = ""
                    city = ""
                    zip = ""

                    if (loc):
                        city = loc["city"]
                        state = loc["state"]
                        zip = loc["zip"] 
                    
                    line = "'{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}', '{8}', '{9}', '{10}', '{11}', '{12}', '{13}'".format(
                        computeMD5hash(url),
                        url,
                        img_url,
                        title,
                        price,
                        age, 
                        sex,
                        size,
                        city,
                        state,                        
                        zip,
                        bod, 
                        date_available, 
                        registration
                    )
                    
                    # print(line)
                    self.write_text(line + "\n")

        except Exception as e:            
            logging.warning(url)

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
                        "city",
                        "state",
                        "zip",                        
                        "dob", 
                        "date_available", 
                        "registration"
                    ))
        
        # test = "insert into products(`product_id`, `product_url`, `img_url`, `title`, `age`, `sex`, `size`, `location`, `dob`, `date_available`, `registration`, `location`)"
        i = 0
        for url in lines:            
            if (url):
                self.parse_page(url.strip())
                time.sleep(0.1)
            i +=1 
            if i > 3:
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

        
        
        
    

        

    
