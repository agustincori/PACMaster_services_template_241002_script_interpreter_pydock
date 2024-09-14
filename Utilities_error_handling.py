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

def log_and_raise(exception_type, error_message, id_run=None, context=None, debug=False, warning=False, error=True, use_db=True):
    """
    Logs the provided error message to the API or falls back to local logging, then raises the provided exception.
    Automatically encapsulates the original error message with an additional context.

    Args:
        exception_type (CustomError): The type of exception to raise.
        error_message (str): The error message to log and raise.
        id_run (int, optional): The ID of the associated run. Defaults to None.
        context (str, optional): The context of the service where the error occurred. Defaults to None.
        debug (bool, optional): Whether the log should be treated as a debug log. Defaults to False.
        warning (bool, optional): Whether the log should be treated as a warning. Defaults to False.
        error (bool, optional): Whether the log should be treated as an error. Defaults to True.
        use_db (bool, optional): Whether the log should be saved to the database. Defaults to True.
    """
    try:
        # Add context to the error message for upstream tracking
        if context:
            error_message = f"{context} | {error_message}"

        # Attempt to log to API
        # log_to_api(id_run, error_message, debug=debug, warning=warning, error=error, use_db=use_db)
    except Exception as e:
        # Fallback to local logging if API logging fails
        logger.error(f"Failed to log to API: {e}")
        logger.error(error_message)

    # Raise the exception, preserving the original exception's details if possible
    raise exception_type(error_message)


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
        Exception: 500         # Internal Server Error for any other exceptions
    }

    # Get the status code based on the exception type
    status_code = exception_status_code_mapping.get(type(exception), 500)

    # Extract additional details if available
    details = getattr(exception, 'details', None)
    status_code = getattr(exception, 'status_code', status_code)

    # Create the error response
    error_response = {
        "service": service_name,
        "route_name": route_name,
        "error": str(exception),
        "id_run": id_run,
        "details": details
    }

    return error_response, status_code



def handle_exceptions(func, context=None, id_run=None):
    """
    Generic error handling wrapper that catches various exceptions, logs them, and raises the appropriate custom exception.

    Args:
        func (callable): The function or callable to execute.
        context (str, optional): Additional context to provide in the error message. Defaults to None.
        id_run (int, optional): ID of the associated run for logging purposes. Defaults to None.

    Returns:
        The result of the function call if successful.

    Raises:
        CustomError: Depending on the type of exception encountered (APIError, ValidationError, DatabaseError, etc.).
    """
    try:
        return func()

    except APIError as e:
        log_and_raise(APIError, f"{context} | {str(e)}", id_run=id_run, context=context)
    except HTTPError as e:
        log_and_raise(HTTPError, f"{context} | {str(e)}", id_run=id_run, context=context)
    except requests.Timeout as e:
        log_and_raise(APIError, f"{context} | Timeout Error: {str(e)}", id_run=id_run, context=context)
    except requests.ConnectionError as e:
        log_and_raise(ConnectionError, f"{context} | Connection Error: {str(e)}", id_run=id_run, context=context)
    except requests.RequestException as e:
        log_and_raise(APIError, f"{context} | Request Error: {str(e)}", id_run=id_run, context=context)
    except CustomError as e:
        log_and_raise(type(e), f"{context} | {str(e)}", id_run=id_run, context=context)
    except Exception as e:
        log_and_raise(APIError, f"{context} | Unexpected Error: {str(e)}", id_run=id_run, context=context)
