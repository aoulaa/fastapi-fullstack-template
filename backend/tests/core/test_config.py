from app.core.config import AppSettings, DatabaseSettings, RedisSettings


def test_app_settings():
    settings = AppSettings(APP_NAME="Test App")
    assert settings.APP_NAME == "Test App"


def test_database_settings_uri():
    settings = DatabaseSettings(
        POSTGRES_USER="user",
        POSTGRES_PASSWORD="password",
        POSTGRES_SERVER="db_server",
        POSTGRES_PORT=5432,
        POSTGRES_DB="test_db",
    )
    expected_uri = "user:password@db_server:5432/test_db"
    assert settings.POSTGRES_URI == expected_uri


def test_redis_settings_url():
    settings = RedisSettings(REDIS_HOST="redis_host", REDIS_PORT=6379)
    assert settings.REDIS_URL == "redis://redis_host:6379"
