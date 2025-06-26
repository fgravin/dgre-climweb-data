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
flask --app=dgregydro setup_schema
flask --app=dgregydro db upgrade
```

### Commands
- ingest reverine floods
- update reverine floods
- ingest flash floods

```bash
flask --app=dgregydro ingest_reverine_floods
flask --app=dgregydro update_reverine_floods 200384 2025-05-25 2025-05-25 40

flask --app=dgregydro ingest_flash_floods
```

