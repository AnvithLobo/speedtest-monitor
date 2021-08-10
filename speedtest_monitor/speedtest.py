import os
import socket
import sys
from pathlib import Path
import json
from parse_config import get_speedtest_path
from database import add_record

SPEEDTEST_PATH = get_speedtest_path()


def get_lock(process_name):
    """
    Create a Lock file and prevent new speedtests from running while the current one is in progress.
    :param process_name:
    :return:
    """
    # Without holding a reference to our socket somewhere it gets garbage
    # collected when the function exits
    get_lock._lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

    try:
        get_lock._lock_socket.bind('\0' + process_name)
    except socket.error:
        print('\n\n **lock exists** \n\n')
        sys.exit()


def speedtest(server_id: int):
    data = json.loads(os.popen(f"{SPEEDTEST_PATH} --accept-license -f json -s {server_id}").read())
    print(data)
    if data.get("level") == "error":
        print(f"Error : ServerID: {server_id} \t Message: {data.get('message')}")
        return None
    elif data.get('error'):
        print(f"Error : ServerID: {server_id} \t Message: {data.get('error')}")
        return None
    else:
        return data


def main():
    get_lock("speedtestmonitor")
    servers = {
        'Spectra Bangalore':  24233,
        'Spectra Chennai': 11562,
        'Spectra Delhi': 15002,
        'Spectra Mumbai': 8978,
        'ACT Fibernet Bangalore': 7379,
        'ACT Fibernet New Delhi': 9214,
        'Singapore Viewqwest 10G': 2054,
        'M1 Limited - Singapore 10G': 7311,
        'LeaseWeb - NL': 3587,
        'NovoServe - NL': 8997,
        'YISP B.V. - NL': 24477,
        'Comcast - USA': 1774,
        'LeaseWeb - USA': 3586,
        'TELUS - Vancouver, BC': 3049,
        'M247 Ltd - London': 26434,
        'Clouvider Ltd - London': 35057,
        'Clouvider Ltd - New York, NY': 35055,
        'Clouvider Ltd - Frankfurt, GER': 35692,
        'Kari East Asia-wide Network Project - Tokyo': 43481,
        '3HK - Tsing Yi, Hong kong': 37267,
        'RETN - Stockholm': 32926,
        'Jio - Bangalore': 10195,
        'Jio - Chennai': 9690,
        'Jio - Mumbai': 24161,

    }
    for server_name, server_id in servers.items():
        print(f"Running Test for {server_name}")
        data = speedtest(server_id=server_id)
        if data:
            if data.get('type') == 'result':
                add_record(data)
                print("\n")
            else:
                print(f"ERROR: Server_name: {server_name}, \t f{data['message']}")


if __name__ == '__main__':
    main()
