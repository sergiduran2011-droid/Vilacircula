from db import PostgresConnection, is_postgres_url


class FakeConnection:
    def __init__(self):
        self.statements = []

    def execute(self, statement, parameters=()):
        self.statements.append((statement, parameters))
        return statement


def test_postgres_url_variants_are_recognized():
    assert is_postgres_url("postgresql://db.example/app")
    assert is_postgres_url("postgresql+psycopg://db.example/app")
    assert is_postgres_url("postgres://db.example/app")
    assert not is_postgres_url("sqlite:///app.db")


def test_postgres_connection_adapts_sqlite_placeholders_and_transactions():
    native = FakeConnection()
    connection = PostgresConnection(native)

    connection.execute("UPDATE profiles SET balance = ? WHERE id = ?", (50, "profile-id"))
    connection.execute("BEGIN IMMEDIATE")
    connection.commit()
    connection.execute("BEGIN IMMEDIATE")
    connection.rollback()

    assert native.statements == [
        ("UPDATE profiles SET balance = %s WHERE id = %s", (50, "profile-id")),
        ("BEGIN", ()),
        ("COMMIT", ()),
        ("BEGIN", ()),
        ("ROLLBACK", ()),
    ]


def test_postgres_executescript_runs_each_statement():
    native = FakeConnection()
    connection = PostgresConnection(native)

    connection.executescript("CREATE TABLE one (id TEXT); CREATE INDEX one_idx ON one(id);")

    assert [statement for statement, _ in native.statements] == [
        "CREATE TABLE one (id TEXT)",
        " CREATE INDEX one_idx ON one(id)",
    ]


def test_postgres_integrity_errors_map_to_existing_api_handler():
    class UniqueViolation(Exception):
        sqlstate = "23505"

    class FailingConnection:
        def execute(self, statement, parameters=()):
            raise UniqueViolation("duplicate key")

    connection = PostgresConnection(FailingConnection())

    try:
        connection.execute("INSERT INTO profiles (username) VALUES (?)", ("sergi",))
    except Exception as error:
        assert error.__class__.__name__ == "IntegrityError"
    else:
        raise AssertionError("Expected an integrity error")