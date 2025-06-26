import logging
import sys

from flask import Flask
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from dgrehydro.config import SETTINGS

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

from dgrehydro import commands

app.cli.add_command(commands.setup_schema)
app.cli.add_command(commands.ingest_riverine)
app.cli.add_command(commands.ingest_flash)
app.cli.add_command(commands.update_riverine)
