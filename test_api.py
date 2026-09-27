import hashlib
import sqlite3

from fastapi.testclient import TestClient

from app import create_app


def make_client(tmp_path, **options):
    database_path = options.pop("database_path", tmp_path / "test.sqlite3")
    return TestClient(create_app(database_path, **options))


def create_profile(client, username="sergi"):
    response = client.post("/api/v1/profiles", json={
        "display_name": "Sergi",
        "school": "Goar",
        "username": username,
        "password": "clave-segura-123",
    })
    assert response.status_code == 201
    body = response.json()
    return body, {"Authorization": f"Bearer {body['token']}"}


def test_profile_has_no_email_and_is_stored_in_sqlite(tmp_path):
    with make_client(tmp_path) as client:
        profile, headers = create_profile(client)
        stored = client.get("/api/v1/profile", headers=headers)
        dashboard = client.get("/api/v1/dashboard", headers=headers)

    assert profile["display_name"] == "Sergi"
    assert profile["school"] == "Goar"
    assert profile["balance"] == 150
    assert "email" not in profile
    assert stored.json()["display_name"] == "Sergi"
    assert stored.json()["username"] == "sergi"
    assert stored.json()["password_setup_required"] is False
    assert dashboard.json()["balance"] == 150
    assert dashboard.json()["steps"]["is_demo"] is True


def test_profile_requires_valid_school_and_authorization(tmp_path):
    with make_client(tmp_path) as client:
        invalid_school = client.post("/api/v1/profiles", json={"display_name": "Sergi", "school": "Otro", "username": "sergi", "password": "clave-segura-123"})
        unauthorized = client.get("/api/v1/dashboard")

    assert invalid_school.status_code == 422
    assert unauthorized.status_code == 401


def test_username_login_is_case_insensitive_and_accounts_are_isolated(tmp_path):
    with make_client(tmp_path) as client:
        first, _ = create_profile(client)
        second, _ = create_profile(client, "segon")
        login = client.post("/api/v1/auth/login", json={"username": "SERGI", "password": "clave-segura-123"})
        wrong_password = client.post("/api/v1/auth/login", json={"username": "sergi", "password": "otra-clave-larga"})
        duplicate_username = client.post("/api/v1/profiles", json={"display_name": "Otra", "school": "Goar", "username": "sergi", "password": "clave-segura-123"})

    assert first["id"] != second["id"]
    assert login.status_code == 200
    assert login.json()["profile"]["id"] == first["id"]
    assert wrong_password.status_code == 401
    assert duplicate_username.status_code == 409


def test_password_change_rotates_token_and_preserves_the_account(tmp_path):
    with make_client(tmp_path) as client:
        profile, headers = create_profile(client)
        changed = client.put("/api/v1/account/credentials", json={"username": "sergi.nou", "password": "una-clave-nueva-123", "current_password": "clave-segura-123"}, headers=headers)
        old_session = client.get("/api/v1/profile", headers=headers)
        login = client.post("/api/v1/auth/login", json={"username": "sergi.nou", "password": "una-clave-nueva-123"})

    assert changed.status_code == 200
    assert changed.json()["token"] != profile["token"]
    assert old_session.status_code == 401
    assert login.status_code == 200
    assert login.json()["profile"]["school"] == "Goar"


def test_demo_ecoid_scan_updates_balance_league_and_activity(tmp_path):
    with make_client(tmp_path) as client:
        _, headers = create_profile(client)
        scan = client.post("/api/v1/demo/eco-scan", headers=headers)
        dashboard = client.get("/api/v1/dashboard", headers=headers).json()

    assert scan.status_code == 200
    assert scan.json()["balance"] == 160
    assert dashboard["contribution"] == 10
    assert dashboard["school_points"] == 10
    assert dashboard["activity"][0]["points"] == 10
    assert dashboard["activity"][0]["is_demo"] is True


def test_demo_ecoid_scan_is_forbidden_in_production(tmp_path, monkeypatch):
    monkeypatch.setenv("VILACIRCULA_ENV", "production")
    with make_client(tmp_path) as client:
        _, headers = create_profile(client)
        response = client.post("/api/v1/demo/eco-scan", headers=headers)

    assert response.status_code == 403


def test_reward_redemption_deducts_balance_and_coupon_is_single_use(tmp_path):
    with make_client(tmp_path) as client:
        _, headers = create_profile(client)
        created = client.post("/api/v1/coupons", json={"reward_id": "bread"}, headers=headers)
        code = created.json()["coupon"]["code"]
        active = client.get("/api/v1/coupons", headers=headers)
        first_scan = client.post("/api/v1/coupons/redeem", json={"code": code}, headers=headers)
        duplicate_scan = client.post("/api/v1/coupons/redeem", json={"code": code}, headers=headers)
        after_scan = client.get("/api/v1/coupons", headers=headers)
        balance = client.get("/api/v1/profile", headers=headers).json()["balance"]

    assert created.status_code == 201
    assert created.json()["balance"] == 100
    assert len(active.json()["active"]) == 1
    assert first_scan.status_code == 200
    assert duplicate_scan.status_code == 409
    assert after_scan.json()["active"] == []
    assert len(after_scan.json()["redeemed"]) == 1
    assert balance == 100


def test_cashier_is_scoped_to_merchant_and_initial_password_must_change(tmp_path):
    with make_client(tmp_path) as client:
        _, headers = create_profile(client)
        bread = client.post("/api/v1/coupons", json={"reward_id": "bread"}, headers=headers).json()["coupon"]
        coffee = client.post("/api/v1/coupons", json={"reward_id": "coffee"}, headers=headers).json()["coupon"]
        login = client.post("/api/v1/auth/cashier/login", json={"username": "caja.cafe-marco", "password": "Viladecans"})
        cashier_token = login.json()["token"]
        cashier_headers = {"Authorization": f"Bearer {cashier_token}"}
        first_scan_before_change = client.post("/api/v1/cashier/coupons/redeem", json={"code": coffee["code"]}, headers=cashier_headers)
        citizen_token_cannot_open_cashier = client.get("/api/v1/cashier/me", headers=headers)
        changed = client.put("/api/v1/cashier/password", json={"password": "cafe-marco-clave-23"}, headers=cashier_headers)
        rotated_headers = {"Authorization": f"Bearer {changed.json()['token']}"}
        wrong_shop = client.post("/api/v1/cashier/coupons/redeem", json={"code": bread["code"]}, headers=rotated_headers)
        first_scan = client.post("/api/v1/cashier/coupons/redeem", json={"code": coffee["code"]}, headers=rotated_headers)
        duplicate_scan = client.post("/api/v1/cashier/coupons/redeem", json={"code": coffee["code"]}, headers=rotated_headers)

    assert login.status_code == 200
    assert login.json()["must_change_password"] is True
    assert first_scan_before_change.status_code == 403
    assert citizen_token_cannot_open_cashier.status_code == 401
    assert changed.status_code == 200
    assert wrong_shop.status_code == 403
    assert first_scan.status_code == 200
    assert first_scan.json()["merchant"] == "Café Marco"
    assert duplicate_scan.status_code == 409


def test_self_scan_is_disabled_in_production_mode(tmp_path, monkeypatch):
    monkeypatch.setenv("VILACIRCULA_ENV", "production")
    with make_client(tmp_path) as client:
        _, headers = create_profile(client)
        code = client.post("/api/v1/coupons", json={"reward_id": "bread"}, headers=headers).json()["coupon"]["code"]
        response = client.post("/api/v1/coupons/redeem", json={"code": code}, headers=headers)

    assert response.status_code == 403


def test_admin_provisions_cashier_without_exposing_admin_secret(tmp_path, monkeypatch):
    monkeypatch.setenv("VILACIRCULA_ENV", "production")
    with make_client(tmp_path, admin_key="municipal-secret") as client:
        unauthorized = client.post("/api/v1/admin/cashiers", json={"username": "caja.nueva", "merchant_id": "osm-12752947043"})
        created = client.post("/api/v1/admin/cashiers", json={"username": "caja.nueva", "merchant_id": "osm-12752947043"}, headers={"X-Admin-Key": "municipal-secret"})
        cashier_login = client.post("/api/v1/auth/cashier/login", json={"username": "caja.nueva", "password": "Viladecans"})

    assert unauthorized.status_code == 401
    assert created.status_code == 201
    assert cashier_login.status_code == 200
    assert cashier_login.json()["must_change_password"] is True


def test_legacy_profile_and_coupon_migrate_without_losing_balance(tmp_path):
    database = tmp_path / "legacy.sqlite3"
    old_token = "legacy-device-token"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE profiles (id TEXT PRIMARY KEY, display_name TEXT NOT NULL, school TEXT NOT NULL, token_hash TEXT NOT NULL UNIQUE, balance INTEGER NOT NULL, contribution INTEGER NOT NULL, created_at TEXT NOT NULL)")
        connection.execute(
            "INSERT INTO profiles VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("legacy-profile", "Sergi", "Goar", hashlib.sha256(old_token.encode()).hexdigest(), 275, 25, "2026-01-01T00:00:00+00:00"),
        )
        connection.execute("CREATE TABLE coupons (id TEXT PRIMARY KEY, code TEXT NOT NULL UNIQUE, profile_id TEXT NOT NULL REFERENCES profiles(id), reward_id TEXT NOT NULL, name TEXT NOT NULL, store TEXT NOT NULL, cost INTEGER NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, expires_at TEXT NOT NULL, redeemed_at TEXT)")
        connection.execute(
            "INSERT INTO coupons VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)",
            ("legacy-coupon", "VC-LEGACY1", "legacy-profile", "bread", "Vale antiguo", "a.m bakery & coffee", 50, "active", "2026-01-01T00:00:00+00:00", "2027-01-01T00:00:00+00:00"),
        )

    with make_client(tmp_path, database_path=database) as client:
        legacy_headers = {"Authorization": f"Bearer {old_token}"}
        migrated = client.get("/api/v1/profile", headers=legacy_headers)
        wallet = client.get("/api/v1/coupons", headers=legacy_headers)
        credentials = client.put("/api/v1/account/credentials", json={"username": "sergi.legacy", "password": "legacy-password-123"}, headers=legacy_headers)
        revoked_legacy = client.get("/api/v1/profile", headers=legacy_headers)
        new_login = client.post("/api/v1/auth/login", json={"username": "sergi.legacy", "password": "legacy-password-123"})
        new_balance = client.get("/api/v1/profile", headers={"Authorization": f"Bearer {new_login.json()['token']}"})

    assert migrated.status_code == 200
    assert migrated.json()["password_setup_required"] is True
    assert migrated.json()["balance"] == 275
    assert wallet.json()["active"][0]["code"] == "VC-LEGACY1"
    assert credentials.status_code == 200
    assert revoked_legacy.status_code == 401
    assert new_login.status_code == 200
    assert new_balance.json()["balance"] == 275
