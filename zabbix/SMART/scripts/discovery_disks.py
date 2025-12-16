#!/usr/bin/env python3

import subprocess
import sys
import json

def support_smart(disk):
    cmd = ["sudo","/usr/sbin/smartctl","-aj",f"{disk}"]
    sp = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(sp.stdout)
    supported = data.get("smart_support", {}).get("available", True)
    return bool(supported)

usage = 'Usage: script <DISK TYPE>(sas, sata, nvme)'
if (len(sys.argv) != 2):
    print(usage)
    sys.exit(1)

disk_type = sys.argv[1].lower()

if(disk_type not in ['sas','sata','nvme']):
    print(usage)
    sys.exit(2)

cmd_lsblk = ["/bin/lsblk", "-dn", "-o", "NAME,TYPE,TRAN"]
cmd_grep = ["grep", f"{disk_type}"]

sp_smartctl = subprocess.Popen(cmd_lsblk, stdout=subprocess.PIPE, text=True)
sp_grep = subprocess.run(cmd_grep, stdin=sp_smartctl.stdout, capture_output=True, text=True)

sp_smartctl.stdout.close()

HEADERS = {
        'sas':  '{#SAS_DISK}',
        'sata': '{#SATA_DISK}',
        'nvme': '{#NVME_DISK}'
        }

devices = sp_grep.stdout.strip().split('\n')
result = {'data': []}

devices = [device for device in devices if device]
# Фильтрация дисков, не поддерживающих S.M.A.R.T.
# Формирование json файла для отправки в zabbix
for device in devices:
    device = device.split()

    dname = "/dev/" + device[0]
    dtype = device[1]
    dtran = device[2]
    
    if (dtype != 'disk' or dtran != f'{disk_type}'):
        continue

    if not support_smart(dname):
        continue

    result['data'].append({
        HEADERS[disk_type]: dname
        })


print(json.dumps(result, indent=2))
