"""
Error Handlers Middleware
Centralized exception handling for FastAPI
"""
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from ...core.logging import logger


def setup_error_handlers(app: FastAPI) -> None:
    """
    Register error handlers for the FastAPI application

    Args:
        app: FastAPI application instance
    """

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """
        Handle Pydantic validation errors

        Returns 422 Unprocessable Entity with detailed error info
        """
        logger.warning(
            "Validation error",
            path=request.url.path,
            errors=exc.errors(),
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "validation_error",
                "message": "Request validation failed",
                "details": exc.errors(),
            },
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(
        request: Request, exc: SQLAlchemyError
    ) -> JSONResponse:
        """
        Handle database errors

        Returns 500 Internal Server Error for database issues
        """
        logger.error(
            "Database error",
            path=request.url.path,
            error=str(exc),
            exc_info=True,
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "database_error",
                "message": "A database error occurred",
                # Don't expose internal error details in production
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(
        request: Request, exc: ValueError
    ) -> JSONResponse:
        """
        Handle ValueError (business logic errors)

        Returns 400 Bad Request
        """
        logger.warning(
            "Value error",
            path=request.url.path,
            error=str(exc),
        )

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "value_error",
                "message": str(exc),
            },
        )

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        Handle 404 Not Found errors

        Returns standardized 404 response
        """
        logger.info(
            "Resource not found",
            path=request.url.path,
        )

        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "not_found",
                "message": f"Resource not found: {request.url.path}",
            },
        )

    @app.exception_handler(500)
    async def internal_server_error_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """
        Handle 500 Internal Server Error

        Returns standardized 500 response
        """
        logger.error(
            "Internal server error",
            path=request.url.path,
            error=str(exc),
            exc_info=True,
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_server_error",
                "message": "An internal server error occurred",
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """
        Handle all other unhandled exceptions

        Returns 500 Internal Server Error
        """
        logger.error(
            "Unhandled exception",
            path=request.url.path,
            exception_type=type(exc).__name__,
            error=str(exc),
            exc_info=True,
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "unexpected_error",
                "message": "An unexpected error occurred",
            },
        )
