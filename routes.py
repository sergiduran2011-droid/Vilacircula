from __future__ import annotations

import sqlite3
import uuid
from contextlib import closing
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles

from auth import normalize_username, token_digest, verify_password, hash_password, timestamp, log_security_event
from models import ProfileCreate, ProfileUpdate, LoginPayload, CredentialsUpdate, PasswordUpdate, CashierProvision, RewardRedeem, CouponScan, SCHOOLS, REWARDS, MERCHANTS


def build_routes(app: FastAPI, *, connect, current_profile, current_cashier, admin_secret_key, production, self_redeem_enabled, db_path, allowed_origins, default_allowed_origins):
    bearer = HTTPBearer(auto_error=False)
    dummy_password_hash = hash_password("__dummy__")

    def issue_session(subject_type: str, subject_id: str, connection: sqlite3.Connection) -> str:
        token = uuid.uuid4().hex + uuid.uuid4().hex
        now = datetime.now(UTC)
        profile_id = subject_id if subject_type == "citizen" else None
        cashier_id = subject_id if subject_type == "cashier" else None
        connection.execute(
            "INSERT INTO auth_sessions (token_hash, subject_type, profile_id, cashier_id, created_at, expires_at) VALUES (?, ?, ?, ?, ?, ?)",
            (token_digest(token), subject_type, profile_id, cashier_id, now.isoformat(), (now + timedelta(days=30)).isoformat()),
        )
        return token

    def public_profile(profile: sqlite3.Row) -> dict[str, object]:
        return {
            "id": profile["id"],
            "display_name": profile["display_name"],
            "school": profile["school"],
            "username": profile["username"],
            "balance": profile["balance"],
            "contribution": profile["contribution"],
            "password_setup_required": profile["password_hash"] is None,
            "is_demo": True,
        }

    def public_coupon(row: sqlite3.Row) -> dict[str, object]:
        return {
            "code": row["code"],
            "name": row["name"],
            "store": row["store"],
            "cost": row["cost"],
            "merchant_id": row["merchant_id"],
            "expiry": datetime.fromisoformat(row["expires_at"]).strftime("%-d %b"),
            "status": row["status"],
            "redeemed_at": row["redeemed_at"],
        }

    def public_coupon_from_dict(coupon: dict[str, object]) -> dict[str, object]:
        expiry = datetime.fromisoformat(str(coupon["expires_at"])).strftime("%-d %b")
        return {
            "code": coupon["code"],
            "name": coupon["name"],
            "store": coupon["store"],
            "cost": coupon["cost"],
            "expiry": expiry,
            "status": coupon["status"],
            "redeemed_at": coupon["redeemed_at"],
        }

    def record_login_failure(username: str, client_ip: str) -> None:
        now = datetime.now(UTC)
        with closing(connect()) as connection:
            attempt = connection.execute(
                "SELECT failed_count, window_started_at FROM login_attempts WHERE username = ? AND client_ip = ?",
                (username, client_ip),
            ).fetchone()
            if attempt is None or datetime.fromisoformat(attempt["window_started_at"]) < now - timedelta(minutes=15):
                connection.execute(
                    "INSERT INTO login_attempts (username, client_ip, failed_count, window_started_at, locked_until) VALUES (?, ?, 1, ?, NULL) ON CONFLICT(username, client_ip) DO UPDATE SET failed_count = 1, window_started_at = excluded.window_started_at, locked_until = NULL",
                    (username, client_ip, now.isoformat()),
                )
                return
            failed_count = attempt["failed_count"] + 1
            locked_until = (now + timedelta(minutes=15)).isoformat() if failed_count >= 8 else None
            connection.execute(
                "UPDATE login_attempts SET failed_count = ?, locked_until = ? WHERE username = ? AND client_ip = ?",
                (failed_count, locked_until, username, client_ip),
            )

    def login_is_locked(username: str, client_ip: str) -> bool:
        with closing(connect()) as connection:
            attempt = connection.execute(
                "SELECT locked_until FROM login_attempts WHERE username = ? AND client_ip = ?",
                (username, client_ip),
            ).fetchone()
        return bool(attempt and attempt["locked_until"] and datetime.fromisoformat(attempt["locked_until"]) > datetime.now(UTC))

    def clear_login_failures(username: str, client_ip: str) -> None:
        with closing(connect()) as connection:
            connection.execute("DELETE FROM login_attempts WHERE username = ? AND client_ip = ?", (username, client_ip))

    def coupon_by_code(code: str, merchant_id: str | None = None, cashier_id: str | None = None) -> dict[str, object]:
        with closing(connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            coupon = connection.execute("SELECT * FROM coupons WHERE code = ?", (code,)).fetchone()
            if coupon is None:
                connection.rollback()
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cupón no encontrado.")
            if coupon["status"] != "active":
                connection.rollback()
                log_security_event("coupon_error", event_type="already_redeemed", code=code, merchant_id=merchant_id, cashier_id=cashier_id)
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este cupón ya fue canjeado.")
            if datetime.fromisoformat(coupon["expires_at"]) <= datetime.now(UTC):
                connection.rollback()
                log_security_event("coupon_error", event_type="expired_coupon", code=code, merchant_id=merchant_id)
                raise HTTPException(status_code=status.HTTP_410_GONE, detail="Este cupón ha caducado.")
            if merchant_id is not None and coupon["merchant_id"] != merchant_id:
                connection.rollback()
                log_security_event("coupon_error", event_type="merchant_mismatch", code=code, expected_merchant_id=merchant_id, actual_merchant_id=coupon["merchant_id"], cashier_id=cashier_id)
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Este cupón pertenece a otro comercio.")
            redeemed_at = timestamp()
            cursor = connection.execute(
                "UPDATE coupons SET status = 'redeemed', redeemed_at = ?, redeemed_by = ? WHERE id = ? AND status = 'active' AND expires_at > ?",
                (redeemed_at, cashier_id, coupon["id"], redeemed_at),
            )
            if cursor.rowcount != 1:
                connection.rollback()
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este cupón ya fue canjeado.")
            connection.commit()
            redeemed = dict(coupon)
            redeemed["status"] = "redeemed"
            redeemed["redeemed_at"] = redeemed_at
            redeemed["redeemed_by"] = cashier_id
            return redeemed

    @app.get("/api/v1/health")
    def health() -> dict[str, object]:
        return {
            "status": "ok",
            "mode": "production" if production else "demo",
            "persistent_database": str(db_path.name),
            "production": production,
            "self_redeem_enabled": self_redeem_enabled,
            "allowed_origins": allowed_origins,
        }

    @app.post("/api/v1/profiles", status_code=status.HTTP_201_CREATED)
    def create_profile(payload: ProfileCreate) -> dict[str, object]:
        display_name = payload.display_name.strip()
        school = payload.school.strip()
        username = normalize_username(payload.username)
        if not display_name:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Escribe tu nombre o apodo.")
        if school not in SCHOOLS:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Selecciona un instituto de Viladecans.")
        profile_id = str(uuid.uuid4())
        with closing(connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    "INSERT INTO profiles (id, display_name, school, token_hash, balance, contribution, created_at, username, password_hash) VALUES (?, ?, ?, ?, 150, 0, ?, ?, ?)",
                    (profile_id, display_name, school, token_digest(uuid.uuid4().hex), timestamp(), username, hash_password(payload.password)),
                )
                token = issue_session("citizen", profile_id, connection)
                connection.commit()
            except sqlite3.IntegrityError as error:
                connection.rollback()
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ese nombre de usuario ya está ocupado.") from error
        return {
            "id": profile_id,
            "display_name": display_name,
            "school": school,
            "username": username,
            "balance": 150,
            "contribution": 0,
            "token": token,
            "is_demo": True,
        }

    @app.post("/api/v1/auth/login")
    def login(payload: LoginPayload, request: Request) -> dict[str, object]:
        username = normalize_username(payload.username)
        client_ip = request.client.host if request.client else "unknown"
        if login_is_locked(username, client_ip):
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Demasiados intentos. Prueba de nuevo en 15 minutos.")
        with closing(connect()) as connection:
            profile = connection.execute("SELECT * FROM profiles WHERE username = ?", (username,)).fetchone()
        password_hash = profile["password_hash"] if profile else None
        password_valid = verify_password(payload.password, password_hash or dummy_password_hash)
        if profile is None or not password_hash or not password_valid:
            record_login_failure(username, client_ip)
            log_security_event("auth_error", event_type="login_failed", username=username, client_ip=client_ip)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario o contraseña incorrectos.")
        clear_login_failures(username, client_ip)
        with closing(connect()) as connection:
            token = issue_session("citizen", profile["id"], connection)
        return {"token": token, "profile": public_profile(profile)}

    @app.post("/api/v1/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
    def logout(profile: sqlite3.Row = Depends(current_profile), credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> None:
        with closing(connect()) as connection:
            connection.execute("DELETE FROM auth_sessions WHERE token_hash = ?", (token_digest(credentials.credentials),))

    @app.put("/api/v1/account/credentials")
    def update_credentials(payload: CredentialsUpdate, profile: sqlite3.Row = Depends(current_profile)) -> dict[str, object]:
        username = normalize_username(payload.username)
        if profile["password_hash"] and (not payload.current_password or not verify_password(payload.current_password, profile["password_hash"])):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="La contraseña actual no es correcta.")
        with closing(connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    "UPDATE profiles SET username = ?, password_hash = ? WHERE id = ?",
                    (username, hash_password(payload.password), profile["id"]),
                )
                connection.execute("DELETE FROM auth_sessions WHERE profile_id = ?", (profile["id"],))
                token = issue_session("citizen", profile["id"], connection)
                connection.commit()
            except sqlite3.IntegrityError as error:
                connection.rollback()
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ese nombre de usuario ya está ocupado.") from error
        return {"token": token, "username": username}

    @app.get("/api/v1/profile")
    def get_profile(profile: sqlite3.Row = Depends(current_profile)) -> dict[str, object]:
        return public_profile(profile)

    @app.put("/api/v1/profile")
    def update_profile(payload: ProfileUpdate, profile: sqlite3.Row = Depends(current_profile)) -> dict[str, object]:
        display_name = payload.display_name.strip()
        school = payload.school.strip()
        if not display_name or school not in SCHOOLS:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Revisa el nombre y el instituto seleccionados.")
        with closing(connect()) as connection:
            connection.execute("UPDATE profiles SET display_name = ?, school = ? WHERE id = ?", (display_name, school, profile["id"]))
        return {"id": profile["id"], "display_name": display_name, "school": school}

    @app.post("/api/v1/auth/cashier/login")
    def cashier_login(payload: LoginPayload, request: Request) -> dict[str, object]:
        username = normalize_username(payload.username)
        client_ip = request.client.host if request.client else "unknown"
        if login_is_locked(username, client_ip):
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Demasiados intentos. Prueba de nuevo en 15 minutos.")
        with closing(connect()) as connection:
            cashier = connection.execute("SELECT * FROM cashier_users WHERE username = ? AND active = 1", (username,)).fetchone()
        password_hash = cashier["password_hash"] if cashier else None
        password_valid = verify_password(payload.password, password_hash or dummy_password_hash)
        if cashier is None or not password_hash or not password_valid:
            record_login_failure(username, client_ip)
            log_security_event("auth_error", event_type="cashier_login_failed", username=username, client_ip=client_ip)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario o contraseña de caja incorrectos.")
        clear_login_failures(username, client_ip)
        with closing(connect()) as connection:
            token = issue_session("cashier", cashier["id"], connection)
            merchant = connection.execute("SELECT id, name, is_demo FROM merchants WHERE id = ?", (cashier["merchant_id"],)).fetchone()
        return {"token": token, "username": username, "must_change_password": bool(cashier["must_change_password"]), "merchant": {"id": merchant["id"], "name": merchant["name"], "is_demo": bool(merchant["is_demo"])}}

    @app.get("/api/v1/cashier/me")
    def cashier_me(cashier: sqlite3.Row = Depends(current_cashier)) -> dict[str, object]:
        return {"username": cashier["username"], "merchant_id": cashier["merchant_id"], "merchant_name": cashier["merchant_name"], "must_change_password": bool(cashier["must_change_password"]), "is_demo": bool(cashier["merchant_is_demo"]) }

    @app.put("/api/v1/cashier/password")
    def cashier_change_password(payload: PasswordUpdate, cashier: sqlite3.Row = Depends(current_cashier), credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> dict[str, str]:
        if not cashier["must_change_password"] and (not payload.current_password or not verify_password(payload.current_password, cashier["password_hash"])):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="La contraseña actual no es correcta.")
        with closing(connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "UPDATE cashier_users SET password_hash = ?, must_change_password = 0 WHERE id = ?",
                (hash_password(payload.password), cashier["id"]),
            )
            connection.execute("DELETE FROM auth_sessions WHERE cashier_id = ?", (cashier["id"],))
            token = issue_session("cashier", cashier["id"], connection)
            connection.commit()
        return {"token": token, "username": cashier["username"]}

    @app.post("/api/v1/auth/cashier/logout", status_code=status.HTTP_204_NO_CONTENT)
    def cashier_logout(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> None:
        if credentials is None:
            return
        with closing(connect()) as connection:
            connection.execute("DELETE FROM auth_sessions WHERE token_hash = ? AND subject_type = 'cashier'", (token_digest(credentials.credentials),))

    @app.get("/api/v1/dashboard")
    def dashboard(profile: sqlite3.Row = Depends(current_profile)) -> dict[str, object]:
        with closing(connect()) as connection:
            schools = connection.execute(
                "SELECT school, SUM(contribution) AS points FROM profiles GROUP BY school ORDER BY points DESC, school ASC"
            ).fetchall()
            events = connection.execute(
                "SELECT description, merchant, points, created_at FROM point_events WHERE profile_id = ? ORDER BY created_at DESC LIMIT 8",
                (profile["id"],),
            ).fetchall()
            personal_rank = connection.execute(
                "SELECT COUNT(*) + 1 AS rank FROM profiles WHERE school = ? AND contribution > ?",
                (profile["school"], profile["contribution"]),
            ).fetchone()["rank"]
        board = [{"school": row["school"], "points": row["points"], "is_demo": True} for row in schools]
        own_rank = next((index for index, row in enumerate(board, 1) if row["school"] == profile["school"]), 1)
        return {"balance": profile["balance"], "contribution": profile["contribution"], "steps": {"count": 0, "goal": 8000, "source": "Sincronización pendiente", "is_demo": True}, "school": profile["school"], "school_rank": own_rank, "personal_rank": personal_rank, "school_points": next((row["points"] for row in board if row["school"] == profile["school"]), 0), "league": board, "activity": [{"description": row["description"], "merchant": row["merchant"], "points": row["points"], "created_at": row["created_at"], "is_demo": True} for row in events], "is_demo": True}

    @app.post("/api/v1/demo/eco-scan")
    def demo_eco_scan(profile: sqlite3.Row = Depends(current_profile)) -> dict[str, object]:
        if production:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Los puntos solo los puede conceder una caja de comercio autorizada.")
        created_at = timestamp()
        with closing(connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("UPDATE profiles SET balance = balance + 10, contribution = contribution + 10 WHERE id = ?", (profile["id"],))
            connection.execute("INSERT INTO point_events (id, profile_id, description, merchant, points, created_at) VALUES (?, ?, ?, ?, ?, ?)", (str(uuid.uuid4()), profile["id"], "Escaneo de caja simulado", "Comercio de demostración", 10, created_at))
            connection.commit()
            updated = connection.execute("SELECT balance, contribution FROM profiles WHERE id = ?", (profile["id"],)).fetchone()
        return {"balance": updated["balance"], "contribution": updated["contribution"], "points": 10, "is_demo": True}

    @app.get("/api/v1/merchants")
    def merchants() -> dict[str, object]:
        with closing(connect()) as connection:
            rows = connection.execute("SELECT * FROM merchants ORDER BY is_demo ASC, name ASC").fetchall()
        items = [{**dict(row), "is_demo": bool(row["is_demo"])} for row in rows]
        return {"items": items, "source": "OpenStreetMap", "is_demo": True}

    @app.get("/api/v1/rewards")
    def rewards() -> dict[str, object]:
        return {"items": list(REWARDS), "is_demo": True}

    @app.get("/api/v1/coupons")
    def coupons(profile: sqlite3.Row = Depends(current_profile)) -> dict[str, object]:
        with closing(connect()) as connection:
            rows = connection.execute("SELECT * FROM coupons WHERE profile_id = ? ORDER BY created_at DESC", (profile["id"],)).fetchall()
        items = [public_coupon(row) for row in rows]
        return {"active": [item for item in items if item["status"] == "active"], "redeemed": [item for item in items if item["status"] == "redeemed"]}

    @app.post("/api/v1/coupons", status_code=status.HTTP_201_CREATED)
    def create_coupon(payload: RewardRedeem, profile: sqlite3.Row = Depends(current_profile)) -> dict[str, object]:
        reward = next((item for item in REWARDS if item["id"] == payload.reward_id), None)
        if reward is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recompensa no encontrada.")
        code = f"VC-{uuid.uuid4().hex.upper()[:16]}"
        coupon_id = str(uuid.uuid4())
        created = datetime.now(UTC)
        expires = created + timedelta(days=45)
        with closing(connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            updated = connection.execute("UPDATE profiles SET balance = balance - ? WHERE id = ? AND balance >= ?", (reward["cost"], profile["id"], reward["cost"]))
            if updated.rowcount != 1:
                connection.rollback()
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No tienes saldo suficiente para este vale.")
            connection.execute(
                "INSERT INTO coupons (id, code, profile_id, merchant_id, reward_id, name, store, cost, status, created_at, expires_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)",
                (coupon_id, code, profile["id"], reward["merchant_id"], reward["id"], reward["name"], reward["store"], reward["cost"], created.isoformat(), expires.isoformat()),
            )
            connection.commit()
            coupon = connection.execute("SELECT * FROM coupons WHERE id = ?", (coupon_id,)).fetchone()
            balance = connection.execute("SELECT balance FROM profiles WHERE id = ?", (profile["id"],)).fetchone()["balance"]
        return {"coupon": public_coupon(coupon), "balance": balance}

    @app.post("/api/v1/coupons/redeem")
    def self_redeem_coupon(payload: CouponScan, profile: sqlite3.Row = Depends(current_profile)) -> dict[str, object]:
        if not self_redeem_enabled:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="El canje debe confirmarlo el comercio desde su caja.")
        with closing(connect()) as connection:
            owns_coupon = connection.execute("SELECT 1 FROM coupons WHERE profile_id = ? AND code = ?", (profile["id"], payload.code)).fetchone()
        if owns_coupon is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ese cupón no pertenece a este monedero.")
        coupon = coupon_by_code(payload.code)
        return {"coupon": public_coupon_from_dict(coupon), "status": "redeemed", "is_demo": True}

    @app.post("/api/v1/merchant/coupons/redeem")
    @app.post("/api/v1/cashier/coupons/redeem")
    def merchant_redeem_coupon(payload: CouponScan, cashier: sqlite3.Row = Depends(current_cashier)) -> dict[str, object]:
        if cashier["must_change_password"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cambia la contraseña inicial antes de escanear cupones.")
        coupon = coupon_by_code(payload.code, cashier["merchant_id"], cashier["id"])
        return {"coupon": public_coupon_from_dict(coupon), "status": "redeemed", "merchant": cashier["merchant_name"], "is_demo": bool(cashier["merchant_is_demo"]) }

    @app.post("/api/v1/admin/cashiers", status_code=status.HTTP_201_CREATED)
    def provision_cashier(payload: CashierProvision, admin_secret: Annotated[str | None, Header(alias="X-Admin-Key")] = None) -> dict[str, object]:
        if not admin_secret_key or not __import__("secrets").compare_digest(admin_secret or "", admin_secret_key):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credencial municipal no válida.")
        username = normalize_username(payload.username)
        with closing(connect()) as connection:
            merchant = connection.execute("SELECT id, name FROM merchants WHERE id = ?", (payload.merchant_id,)).fetchone()
            if merchant is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comercio no encontrado.")
            cashier_id = str(uuid.uuid4())
            try:
                connection.execute(
                    "INSERT INTO cashier_users (id, username, password_hash, merchant_id, must_change_password, active, created_at) VALUES (?, ?, ?, ?, 1, 1, ?)",
                    (cashier_id, username, hash_password("Viladecans"), merchant["id"], timestamp()),
                )
            except sqlite3.IntegrityError as error:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ese usuario de caja ya existe.") from error
        return {"id": cashier_id, "username": username, "merchant": merchant["name"], "must_change_password": True}

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse("/Users/sergiduran/Code/vilacircula/index.html")

    @app.get("/sw.js", include_in_schema=False)
    def service_worker() -> FileResponse:
        return FileResponse("/Users/sergiduran/Code/vilacircula/sw.js", media_type="application/javascript", headers={"Service-Worker-Allowed": "/"})

    for asset in ("index.html", "manifest.json", "viladecans.js", "viladecans.css", "api-client.js", "api-client.css", "cashier.css"):
        app.add_api_route(f"/{asset}", lambda asset=asset: FileResponse(f"/Users/sergiduran/Code/vilacircula/{asset}"), methods=["GET"], include_in_schema=False)

    app.mount("/icons", StaticFiles(directory="/Users/sergiduran/Code/vilacircula/icons"), name="icons")
    return app
