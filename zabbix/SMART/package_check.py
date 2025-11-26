#!/usr/bin/env python3

import sys
import subprocess
import shutil

def check_package(package):
    # Debian/Ubuntu
    if shutil.which("dpkg"):
        return (
            subprocess.call(
                ["dpkg", "-s", package],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            == 0
        )

    # RPM-Дистрибутивы
    if shutil.which("rpm"):
        return (
            subprocess.call(
                ["rpm", "-q", package],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            == 0
        )

    # Arch
    if shutil.which("pacman"):
        return (
            subprocess.call(
                ["pacman", "-Qi", package],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            == 0
        )

    return False


def main():

    if len(sys.argv) != 2:
        print("usage: script <package-name>")
        sys.exit(1)

    package = sys.argv[1]
    
    if(check_package(package) == False):
        print("0")
        sys.exit(1)

    print(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
