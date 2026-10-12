# AgriWaste2Wealth

AgriWaste2Wealth is a FastAPI application with a static HTML/CSS/JavaScript frontend. It provides role-based APIs for listings, buyer requirements, orders, matching, baseline residue estimates, and consent-based research records.

## Run locally

1. Create and activate a Python virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and set a random `SECRET_KEY`.
4. Start the application with `uvicorn app.main:app --reload`.
5. Open `http://localhost:8000`.

The default local database is SQLite (`agriwaste.db`). Synthetic demo records are seeded locally unless `SEED_DEMO_DATA=false` is set.

## Deploy on Vercel

1. Push this repository to GitHub and import it into Vercel.
2. In Vercel project settings, configure environment variables for **Production** and **Preview**:
   - `SECRET_KEY`: a long, randomly generated secret.
   - `DATABASE_URL`: PostgreSQL connection URL, for example `postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require`.
   - `ALLOWED_ORIGINS`: the deployed app origin, e.g. `https://your-project.vercel.app`.
   - `UPLOAD_DIR`: `/tmp/agriwaste-uploads`.
   - `SEED_DEMO_DATA`: `false`.
3. Deploy. The root page and API are routed through the Vercel Python function; API routes are available under `/api`.
4. Check `/api/health` after deployment.

`DATABASE_URL` must use durable managed PostgreSQL on Vercel. Do not use the local SQLite database in a serverless deployment: function filesystems are not durable. The `/tmp` upload directory is also temporary. For persistent uploads and research export files, integrate an object-storage provider before using those features in production.

## GitHub safety and deployment status

- `.env`, local SQLite databases, uploads, caches, and Vercel local state are ignored by Git.
- Never add credentials, production data, or generated database files to the repository.
- This repository configuration does not by itself create a GitHub repository or connect a Vercel account. Import the GitHub repository into Vercel and add the environment variables above.
- This project is not represented as production-ready. Review security, configure durable file storage, and run functional/integration tests in the deployed environment before production use.

The estimator is a documented rules-based baseline, not a trained model. Synthetic data is for demonstration only.
