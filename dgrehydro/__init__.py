import logging
import sys

from flask import Flask
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from healthcheck import HealthCheck

from dgrehydro.config import SETTINGS
from dgrehydro.routes import endpoints

logging.basicConfig(
    level=SETTINGS.get('logging', {}).get('level'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y%m%d-%H:%M%p',
)

# Flask App
app = Flask(__name__, template_folder=SETTINGS.get("TEMPLATE_DIR"))
auth = HTTPBasicAuth()
CORS(app)

logger = logging.getLogger(__name__)
logger.setLevel(SETTINGS.get('logging', {}).get('level'))
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)

app.config['SQLALCHEMY_DATABASE_URI'] = SETTINGS.get('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

health = HealthCheck(app, "/healthcheck")


def db_available():
    db.session.execute('SELECT 1')
    return True, "dbworks"


health.add_check(db_available)
import dgrehydro.routes.server

app.register_blueprint(endpoints, url_prefix='/api/v1')

from dgrehydro import commands

app.cli.add_command(commands.setup_schema)
app.cli.add_command(commands.create_pg_functions)
app.cli.add_command(commands.load_geometries)
app.cli.add_command(commands.ingest_riverine)
app.cli.add_command(commands.ingest_flashflood)
app.cli.add_command(commands.update_riverine)
