import pytest

from app.core.security import TokenType, create_access_token, get_password_hash, verify_password, verify_token


@pytest.mark.asyncio
async def test_password_hashing():
    password = "secret_password"
    hashed = get_password_hash(password)

    assert hashed != password
    assert await verify_password(password, hashed) is True
    assert await verify_password("wrong_password", hashed) is False


@pytest.mark.asyncio
async def test_token_creation_and_verify(db, mock_redis):
    # verify_token(token, type, db)

    data = {"sub": "test@example.com", "token_type": "access"}
    token = await create_access_token(data=data)

    verified_data = await verify_token(token, TokenType.ACCESS, db)
    assert verified_data is not None
    assert verified_data.username_or_email == "test@example.com"

    # Test wrong type
    verified_wrong_type = await verify_token(token, TokenType.REFRESH, db)
    assert verified_wrong_type is None
