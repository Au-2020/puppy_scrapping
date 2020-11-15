import json
import os
from pathlib import Path
from urllib.parse import urlparse
import urllib.request as urllib2
import hashlib
import mysql.connector

def computeMD5hash(my_string):
    m = hashlib.md5()
    m.update(my_string.encode('utf-8'))
    return m.hexdigest()
    
def load_json():
    
    with open("config.json", "r") as f:
        data = json.loads(f.read().strip())        
    
    return data

def get_host(url):
    parsed_uri = urlparse(url)
    result =  '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
    return result

def sod_location(txt, type = 1):
    if (type == 1):
        arr = txt.split(",")
        
        if (len(arr) > 1):
            city = arr[0].strip()
            state_zip = arr[1].strip().split(" ")
            
            res = dict()
            res["city"] = city
            res["state"] = state_zip[0].strip()
            res["zip"] = state_zip[1].strip()

            return res
    
    if (type ==2):
        arr = txt.split(",")
        
        if (len(arr) > 2):
            city = arr[0].split("in ")[1]
            res = dict()
            res["city"] = city.strip()
            res["state"] = arr[1].strip()
            res["zip"] = arr[2].strip()
            return res

    return False

def sod_get_value(txt, replace=""):
    txt.replace(replace, "")
    # if (replace == "price")

def sod_get_price(txt):
    return float(txt.replace("$", "").replace(",", "").replace("*", "").strip())

def sod_remove_key(text="", replace=""):
    text = text.replace("'", "\''")
    return text.replace(replace, "").replace("\n", "").strip().lower()

def db_connection():
    data = load_json()
    
    cnx = mysql.connector.connect(
        host=data["db_config"]["host"],
        port=data["db_config"]["port"],
        user=data["db_config"]["user"],
        password=data["db_config"]["password"],
        database=data["db_config"]["database"]
    )

    return cnx
