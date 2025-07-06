import logging

from dgrehydro import db
from sqlalchemy.sql import text


def create_pg_functions():
    logging.info("[DBSETUP]: Creating pg function")

    with open('./dgre_riverine_flood.sql', 'r') as file:
        sql = file.read()

    db.session.execute(text(sql))
    db.session.commit()

    logging.info("[DBSETUP]: Done Creating pg function")
