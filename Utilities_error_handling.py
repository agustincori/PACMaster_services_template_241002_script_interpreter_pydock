# Utilities_error_handling.py

import logging
import requests

# Set up a centralized logger for cases where DB logging is not possible
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class CustomError(Exception):
    """Base class for custom exceptions"""
    def __init__(self, message, details=None):
        """
        Initializes the CustomError with a message and optional details.

        Args:
            message (str): A description of the error.
            details (str, optional): Additional details about the error. Defaults to None.
        """
        self.message = message
        self.details = details
        super().__init__(f"{message}. Details: {details}")

class ValidationError(CustomError):
    """Exception raised for validation errors"""
    def __init__(self, message="Validation failed", details=None):
        """
        Initializes the ValidationError with a default message or custom message and optional details.

        Args:
            message (str, optional): Custom message for the validation error. Defaults to "Validation failed".
            details (str, optional): Additional details about the validation error. Defaults to None.
        """
        super().__init__(message, details)

class DatabaseError(CustomError):
    """Exception raised for database operation errors"""
    def __init__(self, message="Database operation failed", details=None):
        """
        Initializes the DatabaseError with a message and optional details.

        Args:
            message (str, optional): Custom message for the database error. Defaults to "Database operation failed".
            details (str, optional): Additional details about the database error. Defaults to None.
        """
        super().__init__(message, details)

class APIError(CustomError):
    """Exception raised for API request errors"""
    def __init__(self, message="API request failed", status_code=None, details=None):
        """
        Initializes the APIError with a message, status code, and optional details.

        Args:
            message (str, optional): Custom message for the API error. Defaults to "API request failed".
            status_code (int, optional): The HTTP status code returned by the API.
            details (str, optional): Additional details about the API error. Defaults to None.
        """
        super().__init__(f"{message} [Status Code: {status_code}]", details)
        self.status_code = status_code

class ConnectionError(CustomError):
    """Exception raised for connection errors"""
    def __init__(self, message="Failed to establish a connection", details=None):
        """
        Initializes the ConnectionError with a message and optional details.

        Args:
            message (str, optional): Custom message for the connection error. Defaults to "Failed to establish a connection".
            details (str, optional): Additional details about the connection error. Defaults to None.
        """
        super().__init__(message, details)

class ValidationError(CustomError):
    """Exception raised for validation errors"""
    def __init__(self, message="Validation failed", details=None):
        """
        Initializes the ValidationError with a message and optional details.

        Args:
            message (str, optional): Custom message for the validation error. Defaults to "Validation failed".
            details (str, optional): Additional details about the validation error. Defaults to None.
        """
        super().__init__(message, details)
        
class HTTPError(CustomError):
    """Exception raised for HTTP response errors"""
    def __init__(self, message="HTTP error occurred", status_code=400, details=None):
        """
        Initializes the HTTPError with a status code and optional details.

        Args:
            message (str): Custom message for the HTTP error.
            status_code (int): The HTTP status code (default is 400 for Bad Request).
            details (str, optional): Additional details about the HTTP error.
        """
        super().__init__(f"{message} [Status Code: {status_code}]", details)
        self.status_code = status_code


def format_error_response(service_name, route_name, exception, id_run=None):
    """
    Formats the JSON error response and determines the HTTP status code based on the exception type.

    Args:
        service_name (str): The name of the service returning the error.
        route_name (str): The name of the route or method where the error occurred.
        exception (Exception): The exception object caught.
        id_run (int, optional): The run ID associated with the error.

    Returns:
        tuple: A tuple containing the formatted error response (dict) and the HTTP status code (int).
    """
    # Map exception types to HTTP status codes
    exception_status_code_mapping = {
        ValidationError: 400,  # Bad Request
        APIError: 502,         # Bad Gateway
        ConnectionError: 503,   # Service Unavailable
        HTTPError: 500,        # Internal Server Error
        Exception: 500         # Default to Internal Server Error
    }

    # Helper function to get the closest matching status code based on exception type
    def get_status_code(exception):
        for exc_type, code in exception_status_code_mapping.items():
            if isinstance(exception, exc_type):
                return code
        return 500  # Default to 500 Internal Server Error

    # Get the status code based on the exception type
    status_code = get_status_code(exception)

    # Extract additional details if available
    details = getattr(exception, 'details', None)
    status_code = getattr(exception, 'status_code', status_code)  # Allow exception to override status_code

    # Create the error response
    error_response = {
        "service": service_name,
        "route_name": route_name,
        "error": str(exception),
        "id_run": id_run,
        "status_code": status_code  # Add status code to the error response JSON
    }
    if details is not None:
        error_response["details"] = details

    return error_response, status_code


def centralized_exception_handler(e, context=None, metadata=None):
    """
    Centralized exception handling.
    Discriminates types of exceptions and raises the appropriate one.
    """
    # Base error message
    error_message = f"{context} | An error occurred: {str(e)}"

    # Group exceptions for better organization
    VALIDATION_EXCEPTIONS = (ValidationError, ZeroDivisionError)
    HTTP_EXCEPTIONS = (HTTPError, requests.HTTPError)
    REQUEST_EXCEPTIONS = (requests.Timeout, requests.ConnectionError, requests.RequestException)

    # Handle Validation Errors
    if isinstance(e, VALIDATION_EXCEPTIONS):
        if isinstance(e, ZeroDivisionError):
            error_message = f"{context} | Division by zero is not allowed"
        raise ValidationError(error_message)

    # Handle HTTP Errors
    elif isinstance(e, HTTP_EXCEPTIONS):
        response = getattr(e, 'response', None)
        if response is not None:
            try:
                error_info = response.json()
                server_error_details = error_info.get('error', "No 'error' field in server response.")
            except ValueError:
                server_error_details = response.text or "No detailed error message from server."
            error_message = f"{context} | External Service Error: {str(e)}. Server response: {server_error_details}"
        else:
            error_message = f"{context} | External Service Error: {str(e)}"
        raise HTTPError(error_message)

    # Handle Request Exceptions
    elif isinstance(e, REQUEST_EXCEPTIONS):
        if isinstance(e, requests.Timeout):
            error_message = f"{context} | External Service Error: Timeout Error: {str(e)}"
        elif isinstance(e, requests.ConnectionError):
            error_message = f"{context} | External Service Error: Connection Error: {str(e)}"
        else:  # requests.RequestException
            error_message = f"{context} | External Service Error: Request Error: {str(e)}"
        raise APIError(error_message)

    # Handle API Errors
    elif isinstance(e, APIError):
        raise APIError(error_message)

    # Handle Other Exceptions
    else:
        error_message = f"{context} | Unexpected Error: {str(e)}"
        raise APIError(error_message)


def exception_handler_decorator(func):
    """
    Decorator for centralizing exception handling.
    """
    def wrapper(*args, **kwargs):
        metadata = kwargs.get('metadata', {})
        context = func.__name__
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Call the centralized exception handler
            centralized_exception_handler(e, context=context, metadata=metadata)
    return wrapper