#!/usr/bin/env python3

import sys
import json
import subprocess


def get_temperature(data):
    return data.get("temperature", {}).get("current", -1)


def get_read_errors(data):
    return (
        data.get("scsi_error_counter_log", {})
        .get("read", {})
        .get("total_uncorrected_errors", -1)
    )


def get_write_errors(data):
    return (
        data.get("scsi_error_counter_log", {})
        .get("write", {})
        .get("total_uncorrected_errors", -1)
    )


def get_verify_errors(data):
    return (
        data.get("scsi_error_counter_log", {})
        .get("verify", {})
        .get("total_uncorrected_errors", -1)
    )


def get_smart_status(data):
    value = data.get("smart_status", {}).get("passed", 0)
    if value == True:
        return 1
    else:
        return 0


def get_critical_warning(data):
    return data.get("nvme_smart_health_information_log", {}).get("critical_warning", -1)

def get_media_errors(data):
    return data.get("nvme_smart_health_information_log", {}).get("media_errors", -1)

def get_num_err_log_entries(data):
    return data.get("nvme_smart_health_information_log", {}).get(
        "num_err_log_entries", -1
    )

def get_unsafe_shutdowns(data):
    return data.get("nvme_smart_health_information_log", {}).get("unsafe_shutdowns", -1)

def get_percentage_used(data):
    return data.get("nvme_smart_health_information_log", {}).get("percentage_used", -1)

def get_model_name(data):
    return data.get("model_name", "unknown")

def find_ata_attribute(data, attr):
    attributes = data.get("ata_smart_attributes", {}).get("table", {})
    
    for attribute in attributes:
        if attribute.get("name", "") != attr:
            continue

        return attribute.get("raw", {}).get("value", -1)

    return -2

def get_ata_temperature(data):
    return find_ata_attribute(data, "Temperature_Celsius")

def get_ata_reallocated(data):
    return find_ata_attribute(data, "Reallocated_Sector_Ct")

def get_ata_pending(data):
    return find_ata_attribute(data, "Current_Pending_Sector")

def get_ata_uncorrectable(data):
    return find_ata_attribute(data, "Offline_Uncorrectable")

# Проверка поддерживается ли S.M.A.R.T. на диске
# Если smartctl явно не выводит поле, описывающее, что S.M.A.R.T. на диске недоступен, значит подразумевается, что он доступен
def check_smart_supported(data):
    smart_supported = data.get("smart_support", {}).get("available", True)
    return bool(smart_supported)

def handle_errors(return_code):
    result = {
            "raw_return_code": return_code,
            "flags": []
            }

    flags = {
            1: "command line parser error",
            2: "device open failed",
            4: "SMART status indicates failure",
            8: "some prefail attributes out of threshold",
            16: "one or more attributes changed",
            32: "some logging errors",
            64: "self-test errors detected",
            128: "bad drive or driver"
            }

    for bit, desc in flags.items():
        if return_code & bit:
            result["flags"].append({
                    "bit": bit,
                    "description": desc
                    })

    return json.dumps(result, indent=2)


def main():

    if len(sys.argv) != 3:
        print("Usage: script <device> <metric>")
        sys.exit(1)

    device = sys.argv[1]
    metric = sys.argv[2].lower()

    METRICS = {
        "temperature": get_temperature,
        "ata_temperature": get_ata_temperature,
        "ata_reallocated": get_ata_reallocated,
        "ata_pending": get_ata_pending,
        "ata_uncorrectable": get_ata_uncorrectable,
        "read_errors": get_read_errors,
        "write_errors": get_write_errors,
        "verify_errors": get_verify_errors,
        "smart_status": get_smart_status,
        "critical_warning": get_critical_warning,
        "media_errors": get_media_errors,
        "num_err_log_entries": get_num_err_log_entries,
        "unsafe_shutdowns": get_unsafe_shutdowns,
        "percentage_used": get_percentage_used,
        "model_name": get_model_name,
    }

    cmd = ["sudo", "/usr/sbin/smartctl", "-aj", f"{device}"]

    if metric.lower() not in METRICS:
        print({'error': f'unsupported metric: {metric}' })
        sys.exit(1)

    # Запуск smartctl
    sp = subprocess.run(cmd, capture_output=True, text=True)

    # Переводим вывод smartctl в json
    try:
        data = json.loads(sp.stdout)
    except json.JSONDecodeError as e:
        print(e)
        sys.exit(1)

    # Проверка поддерживается ли S.M.A.R.T.
    if(check_smart_supported(data) != True):
        print({'error': "S.M.A.R.T not supported on this device!"})
        sys.exit(1)

    return_code = sp.returncode
    ERROR_MASK = 1 | 2 | 32 | 64
    if (return_code & ERROR_MASK) != 0:
        print(handle_errors(return_code))
        sys.exit(return_code)

    value = METRICS[metric](data)
    print(value)


if __name__ == "__main__":
    main()
