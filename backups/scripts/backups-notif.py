import redis
import json
import requests
import matplotlib.pyplot as plt
import io
from datetime import datetime

REDIS_ADDRESS = ""
REDIS_PORT = ""
REDIS_PASSWORD = ""

r = redis.Redis(host=REDIS_ADDRESS, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)
pubsub = r.pubsub()
pubsub.subscribe('backups_borg')
pubsub.subscribe('backups_pve_all')
pubsub.subscribe('backups_pve_last')

TELEGRAM_TOKEN = ""
CHAT_ID = ""


def send_text_to_telegram(message):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    )

def send_photos_to_telegram(caption, photos):

    media = []
    files = {}

    for i, image in enumerate(photos):
        photo_name = f'photo{i}'
        files[photo_name] = image
        
        media.append({
            'type': 'photo',
            'media': f'attach://{photo_name}',
            'caption': f'{caption}' if i == 0 else ''
            })

    requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMediaGroup",
            data={'chat_id': CHAT_ID, 'media': json.dumps(media)},
            files=files
            )

def format_borg(data):
    images = []
    fig, ax = plt.subplots(figsize=(10,8))
    ax.axis('off')

    table_data = []
    row_heights = []
    colors = []

    repo_column_color = "#e6f2ff"
    table_autofontsize = False
    table_fontsize = 14
    title_background_color = "#40466e"

    for repo, archives in data.items():
        num_rows = len(archives)

        for archive in archives:
            background_color = 'white'
            status_color = ''
            status = ''
            name = archive['archive']
            date = archive['last_date']
            returncode = archive['returncode']
            err = archive['error']

            if returncode == 2:
                status_color = 'yellow'
                status = 'Бекапится'
            elif returncode == 0 and date == '':
                status_color = 'red'
                status = 'Архив не найден'
            elif returncode == 0 and date != '':
                status_color = 'green'
                status = 'OK'
            else:
                status_color = 'red'
                status = err

                
            table_data.append([repo, name, date, status])
            row_heights.append(1)
            colors.append([repo_column_color, background_color, background_color, status_color])

    table = ax.table(
            cellText=table_data,
            colLabels=['Репо', 'Архив', 'Дата', 'Статус'],
            cellLoc='center',
            loc='center',
            colWidths=[0.15, 0.3, 0.3, 0.25],
            bbox=[0, 0, 1, 1]
            )

    table.auto_set_font_size(table_autofontsize)
    table.set_fontsize(table_fontsize)

    for i in range(4):
        table[(0, i)].set_facecolor(title_background_color)
        table[(0, i)].set_text_props(weight='bold', color='white')
        
    for i, color_row in enumerate(colors):
        for j, color in enumerate(color_row):
            table[(i+1, j)].set_facecolor(color)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    buf.seek(0)
    plt.close()
    images.append(buf)

    return images


def format_pve_last(data):
    images = []

    vm_column_color = "#e6f2ff"
    table_autofontsize = False
    table_fontsize = 14
    title_background_color = "#40466e"

    for storage, vms in data.items():
        background_color = 'white'
        table_data = []
        row_heights = []
        colors = []

        fig, ax = plt.subplots(figsize=(10,8))
        ax.axis('off')

        ax.text(0.5, 0.95, storage, ha='center', va='top', fontsize=20, fontweight='bold', transform=ax.transAxes)

        for vm_name, date in vms.items():
            
            table_data.append([vm_name, date])
            row_heights.append(1)
            colors.append([vm_column_color, background_color])

        table = ax.table(
                cellText=table_data,
                colLabels=['ВМ', 'Дата'],
                cellLoc='center',
                loc='center',
                colWidths=[0.7, 0.3],
                bbox=[0, 0, 1, 0.9]
                )

        table.auto_set_font_size(table_autofontsize)
        table.set_fontsize(table_fontsize)

        for i in range(2):
            table[(0, i)].set_facecolor(title_background_color)
            table[(0, i)].set_text_props(weight='bold', color='white')

        for i, color_row in enumerate(colors):
            for j, color in enumerate(color_row):
                table[(i+1, j)].set_facecolor(color)
                
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=300)
        buf.seek(0)
        plt.close()
        images.append(buf)

    return images
 
def send(data):
    send_to_telegram(data)

for message in pubsub.listen():
    if message['type'] != 'message':
        continue
    channel = message['channel']
    raw_data = json.loads(message['data'])
    data = ""
    caption = f"Отчёт за {datetime.now().date()} | "
    
    match channel:
        case 'backups_borg':
            data = format_borg(raw_data)
            caption += "Borg-репозитории"
        #case 'backups_pve_all':
        #    data = format_pve_all(raw_data)
        case 'backups_pve_last':
            data = format_pve_last(raw_data)
            caption += "Вируальные машины"


    send_photos_to_telegram(caption, data)
