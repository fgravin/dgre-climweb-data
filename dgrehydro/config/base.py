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
    'PG_SERVICE_SCHEMA': os.getenv('PG_SERVICE_SCHEMA', "public"),
    'DATA_RIVERINE_SOURCE_DIR': os.getenv('DATA_RIVERINE_SOURCE_DIR'),
}
