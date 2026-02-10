#!/usr/bin/env python3

import os
import json
import re
import urllib3
import requests
import sys
import redis

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# нужно вынести эти параметры в конфиг файл
TOKEN = ""
SECRET = ""
REDIS_ADDRESS = ""
REDIS_PORT = ""
REDIS_PASSWORD = ""

PROP_FILE=""
HEADERS = {"Authorization": f'PVEAPIToken={TOKEN}={SECRET}'}

PROPERTIES = {}
VMIDS = []
STORAGES = []

ALL_BACKUPS = {}
LAST_BACKUPS = {}

def initialize_data(prop_file):
    try:
        if not os.path.exists(prop_file):
            print(f"Файд {prop_file} не найден")
            sys.exit(1)

        with open(prop_file, 'r') as file:
            global PROPERTIES
            PROPERTIES = json.load(file)

        for vm in PROPERTIES["VM"]:
            if vm not in VMIDS:
                VMIDS.append(vm)

        for storage in PROPERTIES["STORAGES"]:
            if storage not in STORAGES:
                STORAGES.append(storage)

            if storage not in ALL_BACKUPS:
                ALL_BACKUPS[storage] = {}

            if storage not in LAST_BACKUPS:
                LAST_BACKUPS[storage] = {}


    except json.JSONDecodeError as json_error:
        print(f"Ошибка при чтении файла {prop_file}: {json_error}")
        sys.exit(1)
    except Exception as err:
        print(f"Ошибка: {err}")
        sys.exit(1)

def extract_date(volid):
    pattern = r'(\d{4}_\d{2}_\d{2})'
    match = re.search(pattern, volid)
    if match:
        return match.group(1).replace('_', '-')

    return "extract_date_error"

def extract_name(vmid):
    
    for obj in PROPERTIES["VM"]:
        if str(vmid) != obj:
            continue

        vm = PROPERTIES["VM"][obj]
        name = vm.get("name", "none")

        return name

    return "extract_name_error"


def filter_data(storage, content):
    DATA = content.get("data", [])

    for obj in DATA:
        vmid = obj.get("vmid", "-1")
        volid = obj.get("volid", "-1")

        if str(vmid) not in VMIDS:
            continue

        name = extract_name(vmid)
        date = extract_date(volid)


        if name not in ALL_BACKUPS[storage]:
            ALL_BACKUPS[storage][name] = []


        ALL_BACKUPS[storage][name].append(date)
        LAST_BACKUPS[storage][name] = date

def load_data():
    for name in STORAGES:
        obj = PROPERTIES["STORAGES"][name]

        node = obj.get("node", "-1")
        address = obj.get("address", "-1")
        port = obj.get("port", "-1")
        storage = obj.get("storage", "-1")

        if port != "":
            address += ":"

        URL = f"https://{address}{port}/api2/json/nodes/{node}/storage/{storage}/content?content=backup"
        RESPONSE = requests.get(URL, headers=HEADERS, verify=False)
        content = RESPONSE.json()

        filter_data(name, content)

def syntax_error():
    print(USAGE)
    sys.exit(2)


def main():
    
    initialize_data(PROP_FILE)
    load_data()

    data_all = json.dumps(ALL_BACKUPS, indent=2)
    data_last = json.dumps(LAST_BACKUPS, indent=2)

    r = redis.Redis(host=REDIS_ADDRESS, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)

    #r.publish('backups_pve_all', data_all)
    r.publish('backups_pve_last', data_last)

    #print(data_last)
    
if __name__ == "__main__":
    main()
