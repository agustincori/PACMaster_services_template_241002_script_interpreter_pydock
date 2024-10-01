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

def log_and_raise(exception_type, error_message, original_exception=None, context=None):
    """
    Logs the provided error message to the API or falls back to local logging, then raises the provided exception.
    Automatically encapsulates the original error message with an additional context.

    Args:
        exception_type (CustomError): The type of exception to raise.
        error_message (str): The error message to log and raise.
        original_exception (Exception, optional): The original exception object to preserve.
        context (str, optional): The context of the service where the error occurred. Defaults to None.
    """
    try:
        # Add context to the error message for upstream tracking
        if context:
            error_message = f"{context} | {error_message}"

        # Attempt to log to API (if applicable)
        # log_to_api(id_run, error_message, debug=debug, warning=warning, error=error, use_db=use_db)
    except Exception as log_exception:
        # Fallback to local logging if API logging fails
        logger.error(f"Failed to log to API: {log_exception}")
        logger.error(error_message)

    # If original_exception exists, raise a new exception with both messages and keep the original exception details
    if original_exception:
        # Preserve both error_message and original exception's details
        raise exception_type(f"{error_message}. Original exception: {str(original_exception)}") from original_exception
    else:
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
        log_and_raise(APIError, f"{context} | {str(e)}", original_exception=e, context=context)
    except HTTPError as e:
        log_and_raise(HTTPError, f"{context} | External Service Error: {str(e)}", original_exception=e, context=context)
    except requests.Timeout as e:
        log_and_raise(APIError, f"{context} | External Service Error: Timeout Error: {str(e)}", original_exception=e, context=context)
    except requests.ConnectionError as e:
        log_and_raise(ConnectionError, f"{context} | External Service Error: Connection Error: {str(e)}", original_exception=e, context=context)
    except requests.HTTPError as e:
        # Now the 'response' attribute should exist and provide the server's response details
        response = getattr(e, 'response', None)
        if response is not None:
            try:
                error_info = response.json()  # Attempt to load the response JSON
                server_error_details = error_info.get('error', "No 'error' field in server response.")
            except ValueError:
                server_error_details = response.text or "No detailed error message from server."
            error_message = f"{context} | External Service Error: {str(e)}. Server response: {server_error_details}"
        else:
            error_message = f"{context} | External Service Error: {str(e)}"
        log_and_raise(HTTPError, error_message, original_exception=e, context=context)
    except requests.RequestException as e:
        log_and_raise(APIError, f"{context} | External Service Error: Request Error: {str(e)}", original_exception=e, context=context)
    except CustomError as e:
        log_and_raise(type(e), f"{context} | {str(e)}", original_exception=e, context=context)
    except Exception as e:
        log_and_raise(APIError, f"{context} | Unexpected Error: {str(e)}", original_exception=e, context=context)




def centralized_exception_handler(e, context=None, metadata=None):
    """
    Centralized exception handling.
    Discriminates types of exceptions and raises the appropriate one.
    """
    id_run = metadata.get('id_run') if metadata else None
    error_message = f"{context} | An error occurred: {str(e)}"

    # Handle different exception types using log_and_raise
    if isinstance(e, ValidationError):
        # Log and raise ValidationError
        log_and_raise(ValidationError, error_message, original_exception=e, context=context)
    elif isinstance(e, ZeroDivisionError):
        # Log and raise a ValidationError for division by zero
        log_and_raise(ValidationError, f"{context} | Division by zero is not allowed", original_exception=e, context=context)
    elif isinstance(e, HTTPError):
        log_and_raise(HTTPError, error_message, original_exception=e, context=context)
    elif isinstance(e, APIError):
        log_and_raise(APIError, error_message, original_exception=e, context=context)
    else:
        # Log and raise general exceptions as APIError or CustomError
        log_and_raise(APIError, error_message, original_exception=e, context=context)

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