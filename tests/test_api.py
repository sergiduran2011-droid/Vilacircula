import hashlib
import sqlite3
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from app import create_app


def make_client(tmp_path, **options):
    database_path = options.pop("database_path", tmp_path / "test.sqlite3")
    google_client_id = options.pop("google_client_id", "test-google-client-id")
    client = TestClient(create_app(database_path, google_client_id=google_client_id, **options))

    def fake_google_verifier(credential, client_id):
        if credential == "invalid":
            raise ValueError("Invalid Google ID token")
        username = credential.removeprefix("google:")
        return {
            "sub": credential,
            "email": f"{username}@example.com",
            "email_verified": credential != "unverified",
            "name": username.title(),
        }

    client.app.state.google_token_verifier = fake_google_verifier
    return client


def create_profile(client, username="sergi"):
    response = client.post("/api/v1/auth/google", json={
        "credential": f"google:{username}",
        "display_name": "Sergi",
        "school": "Goar",
    })
    assert response.status_code == 200
    result = response.json()
    profile = result["profile"]
    body = {**profile, "profile": profile, "token": result["token"]}
    return body, {"Authorization": f"Bearer {body['token']}"}


def test_serves_pwa_assets(tmp_path):
    with make_client(tmp_path) as client:
        features = client.get("/features.css")
        service_worker = client.get("/sw.js")
        manifest = client.get("/manifest.json")
        icons = [client.get(f"/{icon['src']}") for icon in manifest.json()["icons"]]

    assert features.status_code == 200
    assert "engagement-panel" in features.text
    assert service_worker.status_code == 200
    assert service_worker.headers["service-worker-allowed"] == "/"
    assert manifest.status_code == 200
    assert all(icon.status_code == 200 for icon in icons)


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


def test_dashboard_reports_streaks_and_server_derived_badges(tmp_path):
    database_path = tmp_path / "test.sqlite3"
    with make_client(tmp_path) as client:
        profile, headers = create_profile(client)
        today = datetime.now(ZoneInfo("Europe/Madrid")).date()
        with sqlite3.connect(database_path) as connection:
            for days_ago in (2, 1, 0):
                occurred_at = datetime.combine(
                    today - timedelta(days=days_ago),
                    time(12),
                    tzinfo=ZoneInfo("Europe/Madrid"),
                ).isoformat()
                connection.execute(
                    "INSERT INTO point_events (id, profile_id, description, merchant, points, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (f"event-{days_ago}", profile["id"], "EcoID validado en caja", "Café Marco", 10, occurred_at),
                )
            connection.execute(
                "UPDATE profiles SET contribution = 30 WHERE id = ?",
                (profile["id"],),
            )
        dashboard = client.get("/api/v1/dashboard", headers=headers).json()

    engagement = dashboard["engagement"]
    assert engagement["current_streak"] == 3
    assert engagement["longest_streak"] == 3
    badges = {badge["id"]: badge for badge in engagement["badges"]}
    assert badges["first-steps"]["earned"] is True
    assert badges["streak-3"]["earned"] is True
    assert badges["streak-7"]["earned"] is False
    assert badges["eco-100"]["progress"] == 30


def test_profile_requires_valid_school_and_authorization(tmp_path):
    with make_client(tmp_path) as client:
        invalid_school = client.post("/api/v1/auth/google", json={"credential": "google:invalid-school", "display_name": "Sergi", "school": "Otro"})
        unauthorized = client.get("/api/v1/dashboard")

    assert invalid_school.status_code == 422
    assert unauthorized.status_code == 401


def test_google_login_and_legacy_password_endpoints(tmp_path):
    with make_client(tmp_path) as client:
        first, _ = create_profile(client)
        second, _ = create_profile(client, "segon")
        login = client.post("/api/v1/auth/google", json={"credential": "google:sergi"})
        password_login = client.post("/api/v1/auth/login", json={"username": "sergi", "password": "otra-clave-larga"})
        password_registration = client.post("/api/v1/profiles", json={"display_name": "Otra", "school": "Goar", "username": "otra", "password": "clave-segura-123"})

    assert first["id"] != second["id"]
    assert login.status_code == 200
    assert login.json()["profile"]["id"] == first["id"]
    assert password_login.status_code == 410
    assert password_registration.status_code == 410


def test_google_login_rejects_invalid_and_unverified_id_tokens(tmp_path):
    with make_client(tmp_path) as client:
        invalid = client.post("/api/v1/auth/google", json={"credential": "invalid"})
        unverified = client.post("/api/v1/auth/google", json={"credential": "unverified"})

    assert invalid.status_code == 401
    assert unverified.status_code == 401


def test_google_login_requires_server_client_id(tmp_path):
    with make_client(tmp_path, google_client_id="") as client:
        config = client.get("/api/v1/auth/google/config")
        login = client.post("/api/v1/auth/google", json={"credential": "google:sergi"})

    assert config.json()["client_id"] == ""
    assert login.status_code == 503


def test_google_sign_in_links_existing_profile_with_current_credentials(tmp_path):
    with make_client(tmp_path) as client:
        created, _ = create_profile(client)
        headers = {"Authorization": f"Bearer {created['token']}"}
        credentials = client.put(
            "/api/v1/account/credentials",
            json={"username": "sergi.actual", "password": "clave-segura-123"},
            headers=headers,
        )
        with sqlite3.connect(client.app.state.database_path) as connection:
            connection.execute("UPDATE profiles SET google_sub = NULL WHERE id = ?", (created["profile"]["id"],))
        unlinked = client.post("/api/v1/auth/google", json={"credential": "google:sergi-new"})
        wrong_password = client.post("/api/v1/auth/google", json={
            "credential": "google:sergi-new",
            "username": "sergi.actual",
            "password": "incorrecta",
        })
        linked = client.post("/api/v1/auth/google", json={
            "credential": "google:sergi-new",
            "username": "sergi.actual",
            "password": "clave-segura-123",
        })

    assert credentials.status_code == 200
    assert unlinked.json()["link_required"] is True
    assert wrong_password.status_code == 401
    assert linked.status_code == 200
    assert linked.json()["profile"]["id"] == created["profile"]["id"]


def test_password_change_rotates_token_and_preserves_the_account(tmp_path):
    with make_client(tmp_path) as client:
        profile, headers = create_profile(client)
        changed = client.put("/api/v1/account/credentials", json={"username": "sergi.nou", "password": "una-clave-nueva-123", "current_password": "clave-segura-123"}, headers=headers)
        old_session = client.get("/api/v1/profile", headers=headers)
        login = client.post("/api/v1/auth/google", json={"credential": "google:sergi"})

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


def test_cashier_eco_id_award_is_authorized_single_use_and_updates_balance(tmp_path):
    with make_client(tmp_path) as client:
        _, citizen_headers = create_profile(client)
        unauthorized_issue = client.post("/api/v1/eco-id")
        issued = client.post("/api/v1/eco-id", headers=citizen_headers)
        cashier_login = client.post("/api/v1/auth/cashier/login", json={"username": "caja.cafe-marco", "password": "Viladecans"})
        cashier_headers = {"Authorization": f"Bearer {cashier_login.json()['token']}"}
        before_password_change = client.post("/api/v1/cashier/eco-id/scan", json={"code": issued.json()["code"]}, headers=cashier_headers)
        changed = client.put("/api/v1/cashier/password", json={"password": "clave-cajero-segura-23"}, headers=cashier_headers)
        cashier_headers = {"Authorization": f"Bearer {changed.json()['token']}"}
        awarded = client.post("/api/v1/cashier/eco-id/scan", json={"code": issued.json()["code"]}, headers=cashier_headers)
        replayed = client.post("/api/v1/cashier/eco-id/scan", json={"code": issued.json()["code"]}, headers=cashier_headers)
        profile = client.get("/api/v1/profile", headers=citizen_headers)
        citizen_dashboard = client.get("/api/v1/cashier/dashboard", headers=citizen_headers)

    assert issued.status_code == 200
    assert unauthorized_issue.status_code == 401
    assert issued.json()["code"].startswith("VCID-")
    assert before_password_change.status_code == 403
    assert awarded.status_code == 200
    assert awarded.json()["points"] == 10
    assert awarded.json()["balance"] == 160
    assert replayed.status_code == 409
    assert profile.json()["balance"] == 160
    assert citizen_dashboard.status_code == 401


def test_cashier_cannot_redeem_an_expired_eco_id(tmp_path):
    with make_client(tmp_path) as client:
        _, citizen_headers = create_profile(client)
        issued = client.post("/api/v1/eco-id", headers=citizen_headers)
        with sqlite3.connect(client.app.state.database_path) as connection:
            connection.execute("UPDATE eco_id_tokens SET expires_at = ? WHERE code = ?", ("2020-01-01T00:00:00+00:00", issued.json()["code"]))
        login = client.post("/api/v1/auth/cashier/login", json={"username": "caja.cafe-marco", "password": "Viladecans"})
        cashier_headers = {"Authorization": f"Bearer {login.json()['token']}"}
        changed = client.put("/api/v1/cashier/password", json={"password": "clave-cajero-segura-23"}, headers=cashier_headers)
        cashier_headers = {"Authorization": f"Bearer {changed.json()['token']}"}
        response = client.post("/api/v1/cashier/eco-id/scan", json={"code": issued.json()["code"]}, headers=cashier_headers)

    assert response.status_code == 410


def test_eco_id_owner_can_check_scan_status(tmp_path):
    with make_client(tmp_path) as client:
        _, citizen_headers = create_profile(client)
        _, other_citizen_headers = create_profile(client, "laia")
        issued = client.post("/api/v1/eco-id", headers=citizen_headers).json()
        code = issued["code"]
        initial_status = client.get(f"/api/v1/eco-id/{code}/status", headers=citizen_headers)
        foreign_status = client.get(f"/api/v1/eco-id/{code}/status", headers=other_citizen_headers)
        cashier_login = client.post("/api/v1/auth/cashier/login", json={"username": "caja.cafe-marco", "password": "Viladecans"})
        cashier_headers = {"Authorization": f"Bearer {cashier_login.json()['token']}"}
        client.put("/api/v1/cashier/password", json={"password": "clave-cajero-segura-23"}, headers=cashier_headers)
        cashier_login = client.post("/api/v1/auth/cashier/login", json={"username": "caja.cafe-marco", "password": "clave-cajero-segura-23"})
        cashier_headers = {"Authorization": f"Bearer {cashier_login.json()['token']}"}
        scanned = client.post("/api/v1/cashier/eco-id/scan", json={"code": code}, headers=cashier_headers)
        scanned_status = client.get(f"/api/v1/eco-id/{code}/status", headers=citizen_headers)

    assert initial_status.status_code == 200
    assert initial_status.json()["scanned"] is False
    assert foreign_status.status_code == 404
    assert scanned.status_code == 200
    assert scanned_status.status_code == 200
    assert scanned_status.json()["scanned"] is True


def test_cashier_dashboard_reports_only_its_coupon_and_eco_id_activity(tmp_path):
    with make_client(tmp_path) as client:
        _, citizen_headers = create_profile(client)
        eco_id = client.post("/api/v1/eco-id", headers=citizen_headers).json()["code"]
        coupon = client.post("/api/v1/coupons", json={"reward_id": "coffee"}, headers=citizen_headers).json()["coupon"]["code"]
        cashier_login = client.post("/api/v1/auth/cashier/login", json={"username": "caja.cafe-marco", "password": "Viladecans"})
        cashier_headers = {"Authorization": f"Bearer {cashier_login.json()['token']}"}
        changed = client.put("/api/v1/cashier/password", json={"password": "clave-cajero-segura-23"}, headers=cashier_headers)
        cashier_headers = {"Authorization": f"Bearer {changed.json()['token']}"}
        client.post("/api/v1/cashier/eco-id/scan", json={"code": eco_id}, headers=cashier_headers)
        client.post("/api/v1/cashier/coupons/redeem", json={"code": coupon}, headers=cashier_headers)
        dashboard = client.get("/api/v1/cashier/dashboard", headers=cashier_headers)
        other_login = client.post("/api/v1/auth/cashier/login", json={"username": "caja.am-bakery", "password": "Viladecans"})
        other_dashboard = client.get("/api/v1/cashier/dashboard", headers={"Authorization": f"Bearer {other_login.json()['token']}"})

    assert dashboard.status_code == 200
    assert dashboard.json()["merchant"] == "Café Marco"
    assert dashboard.json()["today"] == {"successful_coupons": 1, "failed_coupons": 0, "ecoid_scans": 1}
    assert dashboard.json()["week"] == {"successful_coupons": 1, "ecoid_scans": 1}
    assert len(dashboard.json()["activity_by_day"]) == 1
    assert other_dashboard.json()["today"] == {"successful_coupons": 0, "failed_coupons": 0, "ecoid_scans": 0}


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
        blocked_until_google_linked = client.get("/api/v1/profile", headers=legacy_headers)
        link_status = client.get("/api/v1/auth/google/link-status", headers=legacy_headers)
        new_login = client.post("/api/v1/auth/google/link", json={"credential": "google:sergi"}, headers=legacy_headers)
        wallet = client.get("/api/v1/coupons", headers={"Authorization": f"Bearer {new_login.json()['token']}"})
        revoked_legacy = client.get("/api/v1/profile", headers=legacy_headers)
        new_balance = client.get("/api/v1/profile", headers={"Authorization": f"Bearer {new_login.json()['token']}"})

    assert blocked_until_google_linked.status_code == 403
    assert link_status.json()["link_required"] is True
    assert new_login.status_code == 200
    assert wallet.json()["active"][0]["code"] == "VC-LEGACY1"
    assert revoked_legacy.status_code == 401
    assert new_balance.json()["balance"] == 275


def test_logout_invalidates_session(tmp_path):
    with make_client(tmp_path) as client:
        _, headers = create_profile(client)
        logout = client.post("/api/v1/auth/logout", headers=headers)
        after_logout = client.get("/api/v1/profile", headers=headers)

    assert logout.status_code == 204
    assert after_logout.status_code == 401


def test_admin_analytics_are_available_for_operations(tmp_path, monkeypatch):
    monkeypatch.setenv("VILACIRCULA_ENV", "production")
    with make_client(tmp_path, admin_key="municipal-secret") as client:
        _, headers = create_profile(client)
        coffee_reward = client.post("/api/v1/coupons", json={"reward_id": "coffee"}, headers=headers).json()["coupon"]
        provision = client.post(
            "/api/v1/admin/cashiers",
            json={"username": "caja.analytics", "merchant_id": "osm-12752947043"},
            headers={"X-Admin-Key": "municipal-secret"},
        )
        assert provision.status_code == 201
        cashier_login = client.post("/api/v1/auth/cashier/login", json={"username": "caja.analytics", "password": "Viladecans"})
        assert cashier_login.status_code == 200
        cashier_headers = {"Authorization": f"Bearer {cashier_login.json()['token']}"}
        password_change = client.put("/api/v1/cashier/password", json={"password": "analytics-password-123"}, headers=cashier_headers)
        rotated_headers = {"Authorization": f"Bearer {password_change.json()['token']}"}
        redeem = client.post("/api/v1/cashier/coupons/redeem", json={"code": coffee_reward["code"]}, headers=rotated_headers)
        assert redeem.status_code == 200
        response = client.get("/api/v1/admin/analytics", headers={"X-Admin-Key": "municipal-secret"})

    assert response.status_code == 200
    assert response.json()["summary"]["total_profiles"] >= 1
    assert response.json()["summary"]["total_validations"] >= 1
    assert response.json()["summary"]["production"] is True


def test_expired_session_is_rejected(tmp_path):
    with make_client(tmp_path) as client:
        _, headers = create_profile(client)
        token = headers["Authorization"].split(" ", 1)[1]
        with sqlite3.connect(client.app.state.database_path) as connection:
            connection.execute("UPDATE auth_sessions SET expires_at = ? WHERE token_hash = ?", ("2020-01-01T00:00:00+00:00", hashlib.sha256(token.encode()).hexdigest()))
        response = client.get("/api/v1/profile", headers=headers)

    assert response.status_code == 401
    assert response.json()["detail"] == "La sesión ha caducado. Inicia sesión otra vez."


def test_cashier_permission_failure_is_explicit(tmp_path):
    with make_client(tmp_path) as client:
        _, headers = create_profile(client)
        bread = client.post("/api/v1/coupons", json={"reward_id": "bread"}, headers=headers).json()["coupon"]
        client.post("/api/v1/coupons", json={"reward_id": "coffee"}, headers=headers)
        login = client.post("/api/v1/auth/cashier/login", json={"username": "caja.cafe-marco", "password": "Viladecans"})
        password_change = client.put("/api/v1/cashier/password", json={"password": "cafe-marco-clave-23"}, headers={"Authorization": f"Bearer {login.json()['token']}"})
        cashier_headers = {"Authorization": f"Bearer {password_change.json()['token']}"}
        wrong_merchant = client.post("/api/v1/cashier/coupons/redeem", json={"code": bread["code"]}, headers=cashier_headers)

    assert wrong_merchant.status_code == 403
    assert wrong_merchant.json()["detail"] == "Este cupón pertenece a otro comercio."


def test_invalid_qr_code_is_rejected(tmp_path):
    with make_client(tmp_path) as client:
        create_profile(client)
        cashier_login = client.post("/api/v1/auth/cashier/login", json={"username": "caja.cafe-marco", "password": "Viladecans"})
        cashier_headers = {"Authorization": f"Bearer {cashier_login.json()['token']}"}
        response = client.post("/api/v1/cashier/coupons/redeem", json={"code": "INVALID-QR"}, headers=cashier_headers)

    assert response.status_code == 422


def test_admin_can_review_audit_log_and_security_headers_are_present(tmp_path, monkeypatch):
    monkeypatch.setenv("VILACIRCULA_ENV", "production")
    with make_client(tmp_path, admin_key="municipal-secret") as client:
        _, headers = create_profile(client)
        _ = client.post("/api/v1/auth/google", json={"credential": "google:sergi"})
        health = client.get("/api/v1/health")
        audit = client.get("/api/v1/admin/audit", headers={"X-Admin-Key": "municipal-secret"})

    assert health.headers.get("x-frame-options") == "DENY"
    assert health.headers.get("x-content-type-options") == "nosniff"
    assert audit.status_code == 200
    assert isinstance(audit.json()["items"], list)
