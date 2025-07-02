## Development setup
Copy `.env.sample` to `.env` and fill in the required values.

### Set up the environment

```bash
python3.11 -m venv .venv
poetry install
source .venv/bin/activate
```

### Start the database
```bash
flask --app=dgrehydro setup_schema
flask --app=dgrehydro db upgrade
```

### Commands
- ingest reverine floods
- update reverine floods
- ingest flash floods

```bash
flask --app=dgrehydro ingest_riverine
flask --app=dgrehydro update_riverine 200384 2025-05-25 2025-05-25 40

flask --app=dgregydro ingest_flash_floods
```

