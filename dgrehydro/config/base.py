import logging
import os

log_level = logging.getLevelName(os.getenv('LOG', "INFO"))

SETTINGS = {
    'logging': {
        'level': log_level
    },
    'service': {
        'port': os.getenv('PORT')
    },
    'SQLALCHEMY_DATABASE_URI': os.getenv('SQLALCHEMY_DATABASE_URI'),
    'DATA_RIVERINE_SOURCE_DIR': os.getenv('DATA_RIVERINE_SOURCE_DIR'),
    'DATA_FLASHFLOOD_SOURCE_DIR': os.getenv('DATA_FLASHFLOOD_SOURCE_DIR'),
    'GEOMETRIES_DATA_DIR': os.getenv('GEOMETRIES_DATA_DIR'),
    'DATA_DIR': os.getenv('DATA_DIR'),
}
