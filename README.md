# VilaCircula

VilaCircula is a progressive web app (PWA) for a local rewards programme in Viladecans. Residents can manage an account, earn points, and use rewards. Participating merchants use a cashier workspace to validate coupons and award points by scanning one-time EcoID codes.

## Live deployment

- **Frontend:** [GitHub Pages](https://sergiduran2011-droid.github.io/Vilacircula/)
- **API:** [Render](https://vilacircula-api.onrender.com)
- **Database:** PostgreSQL on Supabase
- **Health check:** [/api/v1/health](https://vilacircula-api.onrender.com/api/v1/health)

The frontend is static and does not contain database credentials. Account, coupon, and point operations are handled by the FastAPI backend.

## Features

- Resident registration, login, profile, point balance, activity, rewards, and coupons.
- A cashier workspace with daily and weekly activity, a seven-day chart, recent validations, QR scanning, and manual code entry.
- Coupon validation scoped to the cashier's merchant. A successful redemption is recorded once and moves the coupon out of the active wallet.
- Server-issued EcoID QR codes that expire after 45 seconds and can be used once. An authorized cashier scan awards 10 points to the associated account.
- An administration dashboard for aggregate operational metrics and cashier provisioning.

## Run locally

Requirements: Python 3.13 or newer and pip.

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

Open <http://127.0.0.1:8001>. Without a database URL, the app uses `data/vilacircula.sqlite3` and initializes its schema and sample merchant catalogue on startup.

## Configuration

For local development, create a `.env` file or export environment variables in your shell. Do not commit `.env` or put server secrets in frontend files.

| Variable | Purpose |
| --- | --- |
| `VILACIRCULA_ENV` | Set to `development` locally or `production` on the hosted API. |
| `VILACIRCULA_DATABASE_URL` | Optional database URL. Use a PostgreSQL URL for Supabase; otherwise the local SQLite database is used. `DATABASE_URL` is also accepted. |
| `VILACIRCULA_ALLOWED_ORIGINS` | Comma-separated browser origins permitted by CORS. The deployed site origin is `https://sergiduran2011-droid.github.io` (do not include the `/Vilacircula/` path). |
| `VILACIRCULA_ADMIN_KEY` | Secret required for municipal admin endpoints. Keep it on the server. |
| `VILACIRCULA_INITIAL_CASHIER_PASSWORD` | Initial password for seeded cashier accounts. Set a strong temporary value and change it after first login. |
| `VILACIRCULA_ALLOW_SELF_REDEEM` | Enables resident self-redemption. Keep this `0` in production so merchants validate coupons. |
| `VILACIRCULA_MERCHANT_KEY` | Optional merchant integration secret. |
| `HOST`, `PORT` | Bind address and port. Defaults are `0.0.0.0` and `8000` in the production entry point. |

For a local PostgreSQL database, for example:

```env
VILACIRCULA_ENV=development
VILACIRCULA_DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/vilacircula
VILACIRCULA_ALLOWED_ORIGINS=http://localhost:8001
VILACIRCULA_ALLOW_SELF_REDEEM=1
```

The hosted deployment uses Supabase PostgreSQL through its connection pooler. Set the full connection string as `VILACIRCULA_DATABASE_URL` in Render's environment settings; never publish it. For a production deployment, also set `VILACIRCULA_ENV=production`, `VILACIRCULA_ALLOW_SELF_REDEEM=0`, and the exact frontend origin in `VILACIRCULA_ALLOWED_ORIGINS`.

## Cashier accounts

The development seed creates these sample accounts:

| Username | Merchant |
| --- | --- |
| `caja.cafe-marco` | Café Marco |
| `caja.am-bakery` | a.m bakery & coffee |
| `caja.papeleria-demo` | Sample stationery shop |
| `caja.moda-demo` | Sample circular fashion shop |

In development, the default initial password is `Viladecans`. In production, configure `VILACIRCULA_INITIAL_CASHIER_PASSWORD` in Render. Cashier accounts must change their initial password before validating coupons or EcoID codes. Never use the development password on a public deployment.

## Run tests

```sh
python -m pytest -q
```

The API tests cover account isolation, cashier permissions, coupon redemption, one-time EcoID issuance and scanning, expiration, and cashier dashboard metrics.

## Docker

```sh
docker build -t vilacircula .
docker run --rm -p 8000:8000 --env-file .env vilacircula
```

Or run the app with Docker Compose:

```sh
docker compose up --build
```

## Production notes

- Render runs FastAPI; GitHub Pages only serves the static frontend.
- Supabase stores application data in PostgreSQL. Database and admin secrets belong only in Render's environment settings.
- Use HTTPS and restrict CORS to the deployed frontend origin.
- Demo merchants, sample rewards, and step challenges are illustrative. Step tracking and real merchant offer fulfilment are not integrated.
- The self-service demo point-award endpoint is disabled when `VILACIRCULA_ENV=production`; points should be awarded by an authenticated cashier scanning a valid EcoID.

Check the live `/api/v1/health` endpoint after a deployment to confirm the active environment, database backend, and CORS origins.