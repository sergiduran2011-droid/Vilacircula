# VilaCircula

VilaCircula is a progressive web app (PWA) for a local rewards programme in Viladecans. Residents can manage an account, earn points, and use rewards. Participating merchants use a cashier workspace to validate coupons and award points by scanning one-time EcoID codes.

## Live deployment

- **PWA:** [Open VilaCircula](https://sergiduran2011-droid.github.io/Vilacircula/)
- **API:** [Render](https://vilacircula-api.onrender.com)
- **Database:** PostgreSQL on Supabase
- **Health check:** [/api/v1/health](https://vilacircula-api.onrender.com/api/v1/health)

The frontend is static and does not contain database credentials. Account, coupon, and point operations are handled by the FastAPI backend.

## Features

- Resident registration, login, profile, point balance, activity, rewards, and coupons.
- A Viladecans merchant map with category filters, optional distance sorting after the resident grants location permission, OpenStreetMap source links, and directions for mapped locations.
- Server-derived achievement badges and current/longest-day activity streaks based on recorded point events.
- A school leaderboard with each school's accumulated points and the signed-in resident's rank within their school; it does not publish other residents' names.
- Automatic account roles: adults use a personal impact dashboard, students under 18 join a school with its registration code, and configured administrator emails unlock the municipal panel.
- CO₂ estimates use 10,000 steps/kg, 6 g per verified ECO purchase, and 7.5 km of EcoRuta/kg. A cashier-validated EcoID is the currently recorded ECO action.
- The balance shows the fixed EcoPoint conversion of 30 points per euro.
- An opt-in browser accelerometer estimates daily steps while VilaCircula is open; reaching 5,000 steps awards 30 EcoPunts once per day.
- A cashier workspace with daily and weekly activity, a seven-day chart, recent validations, QR scanning, and manual code entry.
- Cashiers can publish, pause, and reactivate their own offers with a benefit, EcoPunts cost, and short description; active offers appear in the resident catalog.
- A resident wallet with active/redeemed coupon history and scannable coupon QR codes. In production, the merchant's authenticated cashier validates the QR; residents cannot mark their own coupons as redeemed.
- Coupon validation scoped to the cashier's merchant. A successful redemption is recorded once and moves the coupon out of the active wallet.
- Server-issued EcoID QR codes that expire after 45 seconds and can be used once. An authorized cashier scan awards 10 points to the associated account and confirms the scan in the resident's open EcoID screen through authenticated server events.
- An administration dashboard for aggregate operational metrics and cashier provisioning.
- PWA installation from the first sign-in screen and the first-login welcome card, with browser-native installation where available and device-specific instructions otherwise.
- Catalan is the default interface language; a persistent language selector switches the PWA and legal pages to Spanish.
- Keyboard skip navigation, visible focus states, accessible merchant-logo names, QR descriptions, and friendly network/scanner errors.

### Install VilaCircula

On a first visit, choose **Añadir aplicación** on the sign-in screen or welcome card. Supported browsers open their native install prompt; on iPhone or iPad, open the site in Safari and use **Compartir → Añadir a pantalla de inicio**. Installation must be confirmed in the browser and cannot be triggered automatically. The service worker caches the app shell for repeat visits and offline access to cached frontend resources.

### Independent marketing landing page

The self-contained website in [`landing-page/`](./landing-page/) is separate from the PWA. To use it elsewhere, copy the entire folder to a static web host and publish its `index.html`; it has no app/API login links or runtime dependency on this repository. Its styling and interactions are in `style.css` and `script.js`. The existing PWA remains at the repository root and is unchanged.

### Merchant map and location

The directory shows merchant records supplied by the API, lets residents filter by category, and plots records that have coordinates on the Viladecans map. The **near me** control asks the browser for location permission, calculates distances on the device, reorders the directory, and recenters the map. The coordinates are not sent to the API. Residents can open directions for a mapped merchant or follow its source link.

OpenStreetMap data confirms a mapped place and its coordinates, not a partnership with VilaCircula or the availability of an offer. Entries explicitly marked as examples are illustrative and are not participating businesses. The current sample rewards and merchant offers are not verified for redemption at a real shop.

### Badges and activity streaks

The API builds the resident's progress summary from server-recorded point events; changing browser state cannot award a badge or increase a streak. Activity is grouped by calendar day in the `Europe/Madrid` time zone. The app shows both the current consecutive-day streak and the longest streak recorded for the account. The current streak remains active if there was a point event today or yesterday.

The current streak counts consecutive calendar days with at least one server-recorded point event. It stays active if the most recent event was today or yesterday, and resets after a full day without an event. The longest streak is derived from the full event history; the 3-day and 7-day badges use that longest streak.

The current badge milestones are:

| Badge | Requirement |
| --- | --- |
| First steps | Earn at least 1 contribution point. |
| Eco 100 | Earn 100 contribution points. |
| Eco 500 | Earn 500 contribution points. |
| Constancy | Record point-earning activity on 3 consecutive days. |
| Unstoppable | Record point-earning activity on 7 consecutive days. |

The interface displays earned badges and progress toward the remaining milestones. Streaks are based on points already recorded by the API; this feature does not add weekly challenges or a way for residents to award themselves points. The separate step counter is an opt-in device-motion estimate.

### School leaderboard

The leaderboard aggregates contribution points by school and shows the signed-in resident's position among profiles in their own school. It does not expose other residents' names or individual activity. Totals depend on the profiles and point events present in the configured database; development/demo data should not be treated as official school results.

### Automatic roles and environmental impact

Roles are assigned by the API and are not selectable in the interface. New accounts must provide a date of birth. People aged 18 or older receive a general profile and see their personal EcoPoint and CO₂ impact instead of the school league. Under-18 accounts need a valid school code; the code determines the school and grants access to the league. The verified Google email is checked against the server-side administrator allowlist; only those accounts see the municipal panel and may call its endpoints. Existing accounts keep their school-based student access when upgraded.

Configure `VILACIRCULA_ADMIN_EMAILS` as a comma-separated list of administrator emails and `VILACIRCULA_SCHOOL_CODES` as a JSON object mapping school names to their exclusive codes. Keep both values on the API server. The configured school names must match `Goar`, `Torre-roja`, `Josep Mestres`, `Miramar`, `Olímpia`, or `Sales`.

The CO₂ estimate is `steps / 10,000 + verified ECO purchases × 0.006 + EcoRuta kilometres / 7.5` kilograms. The steps term uses the opt-in browser sensor estimate; only EcoID scans validated by a cashier count as verified ECO purchases. EcoRuta distance is not yet connected and contributes zero until that source is integrated. The municipal panel reports the same conversion factors and the CO₂ total supported by recorded actions.

EcoPoints use a fixed display conversion of `30 EcoPoints = 1 €`; the euro estimate beside the balance is calculated from the current point balance using that rate.

### Daily step counter

The home dashboard can request access to the device-motion sensor and estimate steps while the PWA is open in a supported browser over HTTPS. The estimate is synchronized to the API by local calendar day in `Europe/Madrid`; the API rejects backward or implausibly fast increases and awards 30 EcoPunts once after 5,000 steps. Only the estimated daily total is sent to and stored by the API; raw motion samples remain on the device. Browser motion access is not a health-platform reading and does not continue while the browser suspends the app, so the count may differ from a phone's health app and is not guaranteed to include background steps. Sensor access is optional and requires the user's permission.

### Coupon wallet and QR validation

When a resident redeems an available reward, the API checks their balance, deducts the reward cost, and creates a single-use coupon in the wallet. Active coupons display a QR code and expiry; redeemed coupons move into the wallet's history. While an active coupon is open, the app checks whether the merchant has validated it and updates the view when its status changes.

An authenticated cashier can create an offer by describing what the resident receives, its EcoPunts cost, and a short description. Offers are published to the resident catalog immediately. The owning merchant can pause or reactivate offers; coupons already issued remain valid and retain the original offer details.

In production, the resident presents the coupon QR at the shop. An authenticated cashier scans it; the API checks that the cashier belongs to the coupon's merchant and prevents a second redemption. Resident self-redemption is disabled in production. The cashier's EcoID scanner is a separate flow: a resident displays a short-lived, single-use EcoID QR and an authorized cashier scan awards 10 points. While the QR is open, the resident app receives an authenticated server-sent event when it is scanned; if that connection drops, it retries with backoff and checks status periodically. Returning to the app or regaining internet also triggers an immediate check. The QR panel shows connection, retry, expiry, and session-error states.

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
| `VILACIRCULA_ADMIN_KEY` | Server-side fallback credential for municipal operations. Keep it on the server; normal admin access uses a configured Google email. |
| `VILACIRCULA_ADMIN_EMAILS` | Comma-separated allowlist of verified Google emails assigned the admin role. |
| `VILACIRCULA_SCHOOL_CODES` | JSON object mapping school names to exclusive student registration codes. Store only on the API server. |
| `VILACIRCULA_INITIAL_CASHIER_PASSWORD` | Initial password for seeded cashier accounts. Set a strong temporary value and change it after first login. |
| `VILACIRCULA_ALLOW_SELF_REDEEM` | Enables resident self-redemption. Keep this `0` in production so merchants validate coupons. |
| `VILACIRCULA_MERCHANT_KEY` | Optional merchant integration secret. |
| `VILACIRCULA_GOOGLE_CLIENT_ID` | Google OAuth web client ID used for resident sign-in. Configure the same ID in the web app and backend environment. |
| `HOST`, `PORT` | Bind address and port. Defaults are `0.0.0.0` and `8000` in the production entry point. |

### Google sign-in

Create a **Web application** OAuth client in Google Cloud Console and add the frontend origins under **Authorized JavaScript origins** (for the hosted app: `https://sergiduran2011-droid.github.io`; locally: `http://localhost:8001`). Set its client ID as `VILACIRCULA_GOOGLE_CLIENT_ID` in the API environment (Render) and in local development. No Google client secret is used by the frontend.

Residents with an existing VilaCircula account can sign in with Google once and verify their current username and password to link it. New registrations also ask for a date of birth; under-18 users need their school's configured code. Existing sessions also offer a way to link the current profile. Google ID tokens are verified by the API before a session is issued. Schema upgrades preserve existing profiles and balances.

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

The API tests cover account isolation, cashier permissions, coupon redemption, one-time EcoID issuance and scanning, expiration, server-derived badges and streaks, and cashier dashboard metrics.

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
- Example merchants and sample rewards are illustrative. Real merchant partnerships and offer fulfilment are not integrated. Weekly challenges and step tracking have not been added.
- The self-service demo point-award endpoint is disabled when `VILACIRCULA_ENV=production`; points should be awarded by an authenticated cashier scanning a valid EcoID.

Check the live `/api/v1/health` endpoint after a deployment to confirm the active environment, database backend, and CORS origins.