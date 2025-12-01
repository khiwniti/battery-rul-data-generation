"""
Service Client
HTTP client for inter-service communication with ML Pipeline, Digital Twin, and Sensor Simulator
"""
import asyncio
from typing import Optional, Dict, Any
from enum import Enum

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from .config import settings
from .logging import logger


class ServiceType(str, Enum):
    """Internal service types"""
    ML_PIPELINE = "ml_pipeline"
    DIGITAL_TWIN = "digital_twin"
    SENSOR_SIMULATOR = "sensor_simulator"


class ServiceClient:
    """
    Async HTTP client for inter-service communication

    Features:
    - Automatic retries with exponential backoff
    - Circuit breaker pattern (basic implementation)
    - Request/response logging
    - Timeout handling
    """

    def __init__(
        self,
        service_type: ServiceType,
        timeout: float = 10.0,
        max_retries: int = 3,
    ):
        """
        Initialize service client

        Args:
            service_type: Type of service to connect to
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.service_type = service_type
        self.timeout = timeout
        self.max_retries = max_retries

        # Get base URL from settings
        self.base_url = self._get_base_url(service_type)

        # Circuit breaker state
        self._circuit_open = False
        self._failure_count = 0
        self._failure_threshold = 5

        # Create httpx client
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
        )

    def _get_base_url(self, service_type: ServiceType) -> str:
        """Get base URL for service type"""
        urls = {
            ServiceType.ML_PIPELINE: settings.ML_PIPELINE_URL,
            ServiceType.DIGITAL_TWIN: settings.DIGITAL_TWIN_URL,
            ServiceType.SENSOR_SIMULATOR: settings.SENSOR_SIMULATOR_URL,
        }
        return urls[service_type]

    def _check_circuit_breaker(self) -> None:
        """Check if circuit breaker is open"""
        if self._circuit_open:
            logger.warning(
                "Circuit breaker is open",
                service=self.service_type,
                failure_count=self._failure_count,
            )
            raise httpx.HTTPError("Circuit breaker is open")

    def _record_success(self) -> None:
        """Record successful request"""
        if self._failure_count > 0:
            logger.info(
                "Service recovered",
                service=self.service_type,
                previous_failures=self._failure_count,
            )
        self._failure_count = 0
        self._circuit_open = False

    def _record_failure(self) -> None:
        """Record failed request"""
        self._failure_count += 1

        if self._failure_count >= self._failure_threshold:
            self._circuit_open = True
            logger.error(
                "Circuit breaker opened",
                service=self.service_type,
                failure_count=self._failure_count,
            )

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send GET request to service

        Args:
            path: API endpoint path
            params: Query parameters

        Returns:
            JSON response data

        Raises:
            httpx.HTTPError: If request fails
        """
        self._check_circuit_breaker()

        try:
            logger.debug(
                "Service request",
                service=self.service_type,
                method="GET",
                path=path,
                params=params,
            )

            response = await self.client.get(path, params=params)
            response.raise_for_status()

            self._record_success()

            logger.debug(
                "Service response",
                service=self.service_type,
                status_code=response.status_code,
                path=path,
            )

            return response.json()

        except (httpx.TimeoutException, httpx.NetworkError) as e:
            self._record_failure()
            logger.warning(
                "Service request failed (retrying)",
                service=self.service_type,
                path=path,
                error=str(e),
            )
            raise

        except httpx.HTTPStatusError as e:
            self._record_failure()
            logger.error(
                "Service returned error",
                service=self.service_type,
                path=path,
                status_code=e.response.status_code,
                error=e.response.text,
            )
            raise

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send POST request to service

        Args:
            path: API endpoint path
            json: JSON request body
            data: Form data

        Returns:
            JSON response data

        Raises:
            httpx.HTTPError: If request fails
        """
        self._check_circuit_breaker()

        try:
            logger.debug(
                "Service request",
                service=self.service_type,
                method="POST",
                path=path,
            )

            response = await self.client.post(path, json=json, data=data)
            response.raise_for_status()

            self._record_success()

            logger.debug(
                "Service response",
                service=self.service_type,
                status_code=response.status_code,
                path=path,
            )

            return response.json()

        except (httpx.TimeoutException, httpx.NetworkError) as e:
            self._record_failure()
            logger.warning(
                "Service request failed (retrying)",
                service=self.service_type,
                path=path,
                error=str(e),
            )
            raise

        except httpx.HTTPStatusError as e:
            self._record_failure()
            logger.error(
                "Service returned error",
                service=self.service_type,
                path=path,
                status_code=e.response.status_code,
                error=e.response.text,
            )
            raise

    async def health_check(self) -> bool:
        """
        Check if service is healthy

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = await self.client.get("/health", timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.warning(
                "Service health check failed",
                service=self.service_type,
                error=str(e),
            )
            return False

    async def close(self) -> None:
        """Close HTTP client"""
        await self.client.aclose()


# Factory functions for creating service clients
def create_ml_pipeline_client() -> ServiceClient:
    """Create ML Pipeline service client"""
    return ServiceClient(ServiceType.ML_PIPELINE, timeout=30.0)


def create_digital_twin_client() -> ServiceClient:
    """Create Digital Twin service client"""
    return ServiceClient(ServiceType.DIGITAL_TWIN, timeout=15.0)


def create_sensor_simulator_client() -> ServiceClient:
    """Create Sensor Simulator service client"""
    return ServiceClient(ServiceType.SENSOR_SIMULATOR, timeout=10.0)


# Example usage:
# async def get_rul_prediction(battery_id: str):
#     client = create_ml_pipeline_client()
#     try:
#         result = await client.post(
#             "/predict/rul",
#             json={"battery_id": battery_id}
#         )
#         return result
#     finally:
#         await client.close()
