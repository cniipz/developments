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


def main():

    if len(sys.argv) != 3:
        print("Usage: script <device> <metric>")
        sys.exit(1)

    device = sys.argv[1]
    metric = sys.argv[2].lower()

    METRICS = {
        "temperature": get_temperature,
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
        print(-2)
        sys.exit(1)

    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        data = json.loads(output)
    except Exception as e:
        print(-10)
        sys.exit(1)

    value = METRICS[metric](data)
    print(value)


if __name__ == "__main__":
    main()
