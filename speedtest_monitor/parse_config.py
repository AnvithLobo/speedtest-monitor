from configparser import ConfigParser
import os
from pathlib import Path

CONFIG_PATH = (Path(__file__).parent / 'speedtest-monitor.conf').absolute()


def config_parse(config_section):
    config = ConfigParser()
    config.read(CONFIG_PATH)
    return config[config_section]


def get_speedtest_path():
    pass
