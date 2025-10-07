import os

from dotenv import load_dotenv

load_dotenv()

from dgrehydro import app

# This is only used when running locally. When running live, Gunicorn runs the application.
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=8001,
        debug=os.getenv('DEBUG') == 'True',
        threaded=True
    )
