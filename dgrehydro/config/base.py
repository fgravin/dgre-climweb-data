import configparser
import logging
import os

log_level = logging.getLevelName(os.getenv('LOG', "INFO"))

config = configparser.ConfigParser()
try:
    config.read('secrets.ini')
except Exception as e:
    logging.error(f"Error reading secrets.ini: {e}")
    raise

SETTINGS = {
    'logging': {
        'level': log_level
    },
    'service': {
        'port': os.getenv('PORT')
    },
    'secrets': {
      'waffgs_http' : {
        "url": config['waffgs_http']['url'],
        "user": config['waffgs_http']['user'],
        "password": config['waffgs_http']['password'],
      },
      'fanfar_ftp' : {
        "url": config['fanfar_ftp']['url'],
        "user": config['fanfar_ftp']['user'],
        "password": config['fanfar_ftp']['password'],
        "path": config['fanfar_ftp']['path']
      },
      'anam_ftp' : {
        "url": config['anam_ftp']['url'],
        "user": config['anam_ftp']['user'],
        "password": config['anam_ftp']['password'],
        "path": config['anam_ftp']['path']
      }
    },
    'STATIC_DATA_DIR': './dgrehydro/_static_data/',
    'SQLALCHEMY_DATABASE_URI': os.getenv('SQLALCHEMY_DATABASE_URI'),
    'DATA_CRITICAL_POINT_SOURCE_DIR': os.getenv('DATA_CRITICAL_POINT_SOURCE_DIR', './data/critpoint/'),
    'DATA_DIR': os.getenv('DATA_DIR'),
}
