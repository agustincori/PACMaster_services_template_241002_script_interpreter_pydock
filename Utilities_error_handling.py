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

def log_and_raise(exception, error_message, id_run=None, context=None, debug=False, warning=False, error=True, use_db=True):
    """
    Logs the provided error message to the API or falls back to local logging, then raises the provided exception.
    Automatically encapsulates the original error message with an additional context.

    Args:
        exception (CustomError): The type of exception to raise.
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
        #log_to_api(id_run, error_message, debug=debug, warning=warning, error=error, use_db=use_db)
    except Exception as e:
        # Fallback to local logging if API logging fails
        logger.error(f"Failed to log to API: {e}")
        logger.error(error_message)
    
    raise exception(error_message)  

def format_error_response(service_name, error_message, id_run=None):
    """
    Formats the JSON error response for easy reading, adding a service name tag.
    
    Args:
        service_name (str): The name of the service returning the error.
        error_message (str): The full upstream error message.
        id_run (dict): Additional run-related information.

    Returns:
        dict: A formatted JSON response.
    """
    # Log error to API
    #log_to_api(id_run, error_message, debug=False, warning=False, error=True, use_db=True)

    # Create a structured error response
    error_response = {
        "service": service_name,
        "error": error_message,
        "id_run": id_run
    }
    return error_response


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
        response = func()

        # Check if the response status matches 200 (default expected status)
        if hasattr(response, 'status_code') and response.status_code not in [200, 201]:
            error_message = f"Request failed with status {response.status_code}: {response.text}"
            log_and_raise(APIError, error_message, context=context)

        return response

    except ValidationError as e:
        log_and_raise(ValidationError, f"Validation Error: {str(e)}", context=context)
    except DatabaseError as e:
        log_and_raise(DatabaseError, f"Database Error: {str(e)}", context=context)
    except requests.Timeout as e:
        log_and_raise(APIError, f"Timeout Error: {str(e)}", context=context)
    except requests.ConnectionError as e:
        log_and_raise(ConnectionError, f"Connection Error: {str(e)}", context=context)
    except requests.HTTPError as e:
        log_and_raise(HTTPError, f"HTTP Error [Status: {e.response.status_code}] | Response: {e.response.text}", context=context)
    except requests.RequestException as e:
        log_and_raise(APIError, f"Request Error: {str(e)}", context=context)
    except ConnectionError as e:
        log_and_raise(ConnectionError, f"Connection Error: {str(e)}", context=context)
    except HTTPError as e:
        log_and_raise(HTTPError, f"HTTP Error [Status: {e.response.status_code}] | Response: {e.response.text}", context=context)
    except CustomError as e:
        log_and_raise(type(e), f"Custom Error: {str(e)}", context=context)
    except Exception as e:
        log_and_raise(APIError, f"Unexpected Error: {str(e)}", context=context)