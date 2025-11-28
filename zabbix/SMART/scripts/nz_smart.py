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

    try:
        sp = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(sp.stdout)
        return_code = sp.returncode

        if return_code != 0:
            print(handle_errors(return_code))
            sys.exit(return_code)

    except Exception as e:
        print(e)
        sys.exit(1)

    value = METRICS[metric](data)
    print(value)


if __name__ == "__main__":
    main()
