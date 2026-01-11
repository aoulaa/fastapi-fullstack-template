from datetime import datetime

from app.core.schemas import PersistentDeletion, TimestampSchema, UUIDSchema


def test_uuid_schema_defaults():
    schema = UUIDSchema()
    assert schema.uuid is not None


def test_timestamp_schema_defaults():
    schema = TimestampSchema()
    assert schema.created_at is not None
    assert schema.updated_at is None


def test_timestamp_schema_serialization():
    dt = datetime(2023, 1, 1, 12, 0, 0)
    schema = TimestampSchema(created_at=dt, updated_at=dt)

    # Dump to dict using model_dump usually keeps datetime objects unless serialized
    # field_serializer works on model_dump if configured? Or model_dump_json?
    # Pydantic v2 field_serializer runs on both, but depends on mode.

    data = schema.model_dump(mode="json")
    assert data["created_at"] == "2023-01-01T12:00:00"
    assert data["updated_at"] == "2023-01-01T12:00:00"


def test_persistent_deletion_defaults():
    schema = PersistentDeletion()
    assert schema.is_deleted is False
    assert schema.deleted_at is None


def test_persistent_deletion_serialization():
    dt = datetime(2023, 1, 1, 12, 0, 0)
    schema = PersistentDeletion(deleted_at=dt, is_deleted=True)

    data = schema.model_dump(mode="json")
    assert data["deleted_at"] == "2023-01-01T12:00:00"
    assert data["is_deleted"] is True
