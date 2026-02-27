#!/usr/bin/env python3

import os
import json
import sys
import subprocess
import redis
from datetime import date, timedelta

# ВЫНЕСТИ В КОНФИГ!!!!
REDIS_ADDRESS = ""
REDIS_PORT = ""
REDIS_PASSWORD = ""

borg_data_file = "" 
DATA = "none"
RESULT = {}

def load_data():
    try:
        if not os.path.exists(borg_data_file):
            print("Файл с описанием репозиториев не найден.")
            print(f"Путь к файлу: {borg_data_file}")
            sys.exit(1)

        with open(borg_data_file, 'r') as file:
            global DATA
            DATA = json.load(file)

    except json.JSONDecodeError as json_error:
        print(f'Ошибка при чтении json-файла: {json_error}')
    except Exception as e:
        print(f"Ошибка: {e}")

# Получает дату последней резервной копии для архива
def get_archive_last(repository, archive):
    cmd_list = ["borg", "list", "--glob-archives", f'{archive}*', "--last", "1", "--format", "{time:%Y-%m-%d}", repository]
    sp_list = subprocess.run(cmd_list, capture_output=True, text=True)
    
    return sp_list


# Добавление в JSON файл результат проверки
def append_to_result(repository, archive, stdout):
    global RESULT
    
    if repository not in RESULT:
        RESULT[repository] = []

    RESULT[repository].append({

        "archive": archive,
        "returncode": stdout.returncode,
        "last_date": stdout.stdout,
        "error": stdout.stderr
        })


def main():

    load_data()
    repositories = DATA.get("repositories", [])

    for repo_name in repositories:
        repo = repositories[repo_name]
        path = repo.get("path", "/NONE")
        for archive in repo.get("archives", []):
            stdout = get_archive_last(path, archive)
            append_to_result(repo_name, archive, stdout)


    jsonr = json.dumps(RESULT, indent=2)

    r = redis.Redis(host=REDIS_PASSWORD, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)
    r.publish('backups_borg', jsonr)
    #print(jsonr)

if __name__ == "__main__":
    main()

