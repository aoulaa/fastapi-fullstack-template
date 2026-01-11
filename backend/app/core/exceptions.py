from fastapi import HTTPException, status


class CustomException(HTTPException):
    def __init__(self, status_code: int, detail: str, headers: dict[str, str] | None = None) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class BadRequestException(CustomException):
    def __init__(self, detail: str = "Bad Request") -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class NotFoundException(CustomException):
    def __init__(self, detail: str = "Not Found") -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ForbiddenException(CustomException):
    def __init__(self, detail: str = "Forbidden") -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class UnauthorizedException(CustomException):
    def __init__(self, detail: str = "Unauthorized") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class UnprocessableEntityException(CustomException):
    def __init__(self, detail: str = "Unprocessable Entity") -> None:
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


class DuplicateValueException(CustomException):
    def __init__(self, detail: str = "Duplicate Value") -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class RateLimitException(CustomException):
    def __init__(self, detail: str = "Rate Limit Exceeded") -> None:
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail)


# Cache Exceptions
class CacheIdentificationInferenceError(Exception):
    def __init__(self, message: str = "Could not infer id for resource being cached.") -> None:
        self.message = message
        super().__init__(self.message)


class InvalidRequestError(Exception):
    def __init__(self, message: str = "Type of request not supported.") -> None:
        self.message = message
        super().__init__(self.message)


class MissingClientError(Exception):
    def __init__(self, message: str = "Client is None.") -> None:
        self.message = message
        super().__init__(self.message)
