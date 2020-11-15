from bs4 import BeautifulSoup
import requests
import urllib.request as urllib2
import logging
import os
# from selenium.remote.webdriver import WebDriver
import selenium
from selenium import webdriver
import time
import csv
from fbase import get_host, sod_location, sod_remove_key, sod_get_price, computeMD5hash, db_connection
from pathlib import Path
import time
import datetime

class PuppySpot:
    def __init__(self, url):
        self._url = url

        self._file = "puppyspot.txt"
        self._db = "db2.csv"
        self._cnx = False


        my_file = Path(self._file)
        if not my_file.is_file():
            file1 = open(self._file, "w+")
            file1.write('')
            file1.close()

        self._host = get_host(url)
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        self._driver = webdriver.Chrome(options=options, executable_path=os.path.join(os.path.dirname(__file__), "server/chromedriver.exe"))


        # file1 = open(self._file, "w+")
        # file1.write('')
        # file1.close()

    
    def parse(self):
        
        if (self._driver):
            urllist = []

            contents = self._driver.find_elements_by_css_selector(".js-puppy-list-container .puppies-for-sale-card")
            for content in contents:
                href = content.find_element_by_tag_name("a").get_attribute("href")                
                if (href):
                    urllist.append(href + "\n")
            
            if (urllist):
                f = open(self._file, "a+")
                f.writelines(urllist)
                f.close()
    
    def pages(self):
        try:            
            # print(self._url)
            # result = urllib2.urlopen(self._url)
            
            # rcontent = result.read()
            window_name = self._driver.window_handles[0]
            if (self._url.find("page=") > 0):            
                # self._driver.execute_script("window.open('');")
                self._driver.execute_script("window.open('" + self._url + "', '__blank__');")
                
                self._driver.switch_to.window(self._driver.window_handles[-1])
                
                # self._driver.close()
            else:
                self._driver.get(self._url)

            next = self._driver.find_elements_by_css_selector(".js-puppy-pagination-container li")[-1]         
            # print(next)
            className = next.get_attribute("class").strip()
            
            if className != "":
                self.parse()
                # self._driver.close()
            else:
                page_num = next.find_element_by_tag_name("a").get_attribute("data-page").strip()
                index = self._url.find("?page=")            
                url = self._url[:index] + "?page=" + page_num if (index > 0) else self._url + "?page=" + page_num
                self._url = url
                self.parse()
                # self._driver.close()
                self.pages()

            # self._driver.close()
            
            # if (rcontent):            
            #     bs = BeautifulSoup(rcontent, 'html.parser')
            
            # if (bs):
            #     content = bs.select_one(".pagination-pagebar li:last-child")                
            #     if (not content and content.get('class') != ''):
            #         next = content[0].get("href")
            #         print(next)
            #         # self.parse(bs)
            #         # if (self._url != next):
            #         #     self._url =  next
            #         #     self.pages()
            #     else:
            #         self.parse(bs)        
        except Exception as e:            
            logging.warning(self._url)
            logging.warning(e)
    
    # def sub_parse(self, bs):
    #     title = ""
    #     price = ""
    #     sex = ""
    #     color = ""
    #     size = ""

    #     content = bs.select(".pf-content > div.pf-section-mod")
    #     if (content and len(content) > 1):
    #         sub_content = content[1].select(".pf-data-list--main-info > li")
    #         for item in sub_content:
    #             text = item.text.strip()
    #             if (text.find("Nickname:") != -1):
    #                 title = sod_remove_key(text, "Nickname:")

    #             if (text.find("Price:") != -1):
    #                 price = sod_get_price(sod_remove_key(text, "Price:"))

    #             if (text.find("Gender") != -1):
    #                 sex = sod_remove_key(text, "Gender")

    #             if (text.find("Color/ Markings:") != -1):
    #                 color = sod_remove_key(text, "Color/ Markings:")
                
    #             if (text.find("Size at Maturity:") != -1):
    #                 size = sod_remove_key(text, "Size at Maturity:")
    #     return {
    #         'title': title,
    #         'price': price,
    #         'sex': sex,
    #         'color': color,
    #         'size': size
    #     }
    
    def parse_page(self, url):
       
        # req =  requests.get(url)
        # print(req.status_code)
        # result = urllib2.urlopen(url)
        # rcontent = result.read()
        try:
            self._driver.execute_script("window.open('" + url + "');")                
            self._driver.switch_to.window(self._driver.window_handles[-1])
        except:
            self._driver.get(url)

        
        
        title = ""
        price = ""
        sex = ""
        age = 0
        date_available = ""
        shipping = ""
        dob = ""
        color = ""
        registry = ""
        size = ""

        try:
            title = self._driver.find_element_by_css_selector(".js-puppy-page-nav.puppy-profile__nav")
            if (title):
                title = title.text.strip()

            rcontent = self._driver.find_element_by_css_selector(".puppy-profile__content")
            img_wrap =self._driver.find_element_by_css_selector(".gallery__content ").find_element_by_tag_name("img")

            img_url = img_wrap.get_attribute("src")

            if (rcontent):            
                sex_age = rcontent.find_element_by_css_selector(".puppy-profile__details-gender-and-age").text.strip()
                sex_age = sex_age.split("•")
                sex = 1 if sex_age[0].lower().strip() == "male" else 0
                age = sex_age[1].strip() if len(sex_age) > 1 else ""
                age = age.replace("weeks", "").strip()

                price = rcontent.find_element_by_css_selector(".puppy-profile__details-price").text.strip().replace("$", "")            
                details = rcontent.find_element_by_css_selector(".puppy-profile__sub-details")
                
                size = rcontent.find_element_by_css_selector(".fast-facts__container__breedsize .bold").text.strip().lower()

                if (details):
                    ptags = details.find_elements_by_tag_name("p")

                    for item in ptags:
                        text = item.text.strip()
                        if text.find("DOB") >= 0:
                            dob = text.replace("DOB", "").strip()
                            dob_date = datetime.datetime.strptime(dob, "%B %d, %Y").strftime("%Y-%m-%d")

                        if text.find("Color")>=0:     
                            color = text.replace("Color", "").strip()
                        
                        if text.find("Registry") >=0:
                            registry = text.replace("Registry", "").strip()

                    

                    # price = "" if (main_info[0] is None) else main_info[0].text.strip()

                    # sex = "" if (main_info[2] is None) else main_info[2].text.strip()

                    # age = "" if (main_info[3] is None) else main_info[3].text.strip()

                    
                    # date_available = "" if (main_info[4] is None) else main_info[4].text.strip()

                    # shipping = "" if (main_info[5] is None) else main_info[5].text.strip()
            #gallery__content 

                    line = "'{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}', '{8}', '{9}', '{10}'\n".format(
                            computeMD5hash(url),
                            url,
                            img_url,
                            title,
                            price,
                            age, 
                            sex,
                            size,                        
                            color,
                            dob_date,                        
                            registry
                        )
                    
                    self.write_text(line)
                # print(img_url, title, sex, age,  price, registry, dob_date, color, size)
        except Exception as e:            
            logging.warning(url)
            print(e)

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
        self.write_text("`{0}`, `{1}`, `{2}`, `{3}`, `{4}`, `{5}`, `{6}`, `{7}`, `{8}`, `{9}`, `{10}`\n".format(
                        "product_id",
                        "product_url",
                        "img_url",
                        "title",
                        "price",
                        "age",                        
                        "sex",
                        "size",
                        "color",
                        "dob",
                        "registration"  
                    ))


        i = 0

        for url in lines:            
            if (url):
                self.parse_page(url.strip())
                time.sleep(1)
                i += 1

            if (i > 2):
                break
        
        self.close()

    def close(self):
        if self._driver:
            self._driver.close()

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
        self._driver.quit()

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