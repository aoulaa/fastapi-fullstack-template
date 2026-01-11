from fastapi import status

from app.core.exceptions import (
    BadRequestException,
    CacheIdentificationInferenceError,
    DuplicateValueException,
    ForbiddenException,
    InvalidRequestError,
    MissingClientError,
    NotFoundException,
    RateLimitException,
    UnauthorizedException,
    UnprocessableEntityException,
)


def test_bad_request_exception():
    exc = BadRequestException()
    assert exc.status_code == status.HTTP_400_BAD_REQUEST
    assert exc.detail == "Bad Request"


def test_not_found_exception():
    exc = NotFoundException()
    assert exc.status_code == status.HTTP_404_NOT_FOUND
    assert exc.detail == "Not Found"


def test_forbidden_exception():
    exc = ForbiddenException()
    assert exc.status_code == status.HTTP_403_FORBIDDEN
    assert exc.detail == "Forbidden"


def test_unauthorized_exception():
    exc = UnauthorizedException()
    assert exc.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.detail == "Unauthorized"
    assert exc.headers["WWW-Authenticate"] == "Bearer"


def test_unprocessable_entity_exception():
    exc = UnprocessableEntityException()
    assert exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert exc.detail == "Unprocessable Entity"


def test_duplicate_value_exception():
    exc = DuplicateValueException()
    assert exc.status_code == status.HTTP_409_CONFLICT
    assert exc.detail == "Duplicate Value"


def test_rate_limit_exception():
    exc = RateLimitException()
    assert exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert exc.detail == "Rate Limit Exceeded"


def test_custom_exception_messages():
    exc = BadRequestException(detail="Custom Error")
    assert exc.detail == "Custom Error"


def test_cache_exceptions():
    exc = CacheIdentificationInferenceError()
    assert str(exc) == "Could not infer id for resource being cached."

    exc = InvalidRequestError()
    assert str(exc) == "Type of request not supported."

    exc = MissingClientError()
    assert str(exc) == "Client is None."
