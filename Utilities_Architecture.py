"""
Utilities_Architecture.py

This module provides utility functions to interact with a specific API for logging, user identification, run management, and handling API requests. 

Functions:
    - log_to_api: Sends log messages to the API with metadata for debugging, warning, or error tracking.
    - arq_get_new_id_run: Generates and logs a new run ID for a script based on metadata.
    - arq_update_run_fields: Updates the run status or fields based on provided metadata.
    - arq_user_identify: Identifies and validates a user through an API request, updating the run status.
    - get_data_type: Fetches data types from the API based on category and type IDs.
    - arq_save_outcome_data: Submits outcome data for a run, supporting multiple data types.
    - update_run_fields: Updates run fields such as status or user ID.
    - arq_handle_api_request: Sends API requests with error handling, supporting token and Basic Authentication.
    - ArqRuns class: Manages run creation and updates, including status and metadata handling.
    - ArqValidations class: Handles user validation, token verification, and refresh logic.
    
Each method contains detailed descriptions and argument lists in its individual docstring.
"""

import requests
import os
from datetime import datetime
import time
from Utilities_error_handling import ValidationError,exception_handler_decorator
import Utilities_data_type
import base64
import jwt
import json
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError, DecodeError, InvalidSignatureError, InvalidIssuerError, InvalidAudienceError, InvalidIssuedAtError, MissingRequiredClaimError


# Obtener host y puerto desde variables de entorno
db_manager_HOST = os.getenv('db_manager_HOST', 'localhost')
db_manager_PORT = os.getenv('db_manager_PORT', '20083')
BASE_URL = f'http://{db_manager_HOST}:{db_manager_PORT}'

# Set the secret key from environment variables or use a default value
SECRET_KEY = os.getenv('SECRET_KEY', 'th3_s3cr3t_k3y')


def log_to_api(metadata, log_message, debug=False, warning=False, error=False, use_db=True):
    """
    Sends a log message to the API endpoint with proper error handling.

    Args:
        metadata (dict): Contains metadata, including:
            - id_run (int): The run ID associated with the log message.
            - user (str): Username for authentication.
            - password (str): Password for authentication.
        log_message (str): The log message to send.
        debug (bool, optional): Indicates if the log is a debug message. Defaults to False.
        warning (bool, optional): Indicates if the log is a warning message. Defaults to False.
        error (bool, optional): Indicates if the log is an error message. Defaults to False.
        use_db (bool, optional): Determines whether to send the log to the API or just print it. Defaults to True.

    Returns:
        None
    """
    # Get current timestamp in the desired format
    timestamp = datetime.now().strftime('%H:%M:%S:%f')[:-3]  # '%f' gives microseconds, slicing to get milliseconds
    
    # Prepend timestamp to the log message
    log_message_with_timestamp = f"{timestamp} {log_message}"

    # Extract values from metadata
    id_run = metadata.get('id_run', None)

    if not use_db or id_run is None:
        print(log_message_with_timestamp)  # Print the log message with timestamp
        return

    # Prepare the data for the POST request
    log_data = {
        'service_name': service_name,
        'id_run': id_run,
        'log': log_message_with_timestamp,
        'debug': debug,
        'warning': warning,
        'error': error
    }

    url = f'{BASE_URL}/insert_log'

    try:
        # Use arq_handle_api_request to send the request with proper error handling
        response = arq_handle_api_request(url, payload=log_data, method='POST', metadata=metadata)
        # If the request is successful, print the log message
        print(log_message_with_timestamp)
    except Exception as e:
        log_to_api(metadata, f"Exception in log_to_api: {str(e)}", error=True)
        raise




    
@exception_handler_decorator
def get_data_type(id_category, id_type, id_run=None):
    """
    Retrieves data types based on category and type IDs from a specified endpoint.
    
    This function makes a GET request to the '/get_data_run_types' endpoint, using
    'id_category' and 'id_type' as query parameters. It handles errors gracefully and logs
    important events for debugging and error tracking.
    
    Args:
        id_category (int): The ID of the category to filter the data types.
        id_type (int): The ID of the type to filter the data types.
        id_run (int, optional): The ID of the associated run for logging purposes. Defaults to None.
    
    Returns:
        dict: The response from the server if the request was successful and the server responded with data.
    """
    
    # Define the endpoint URL
    url = f'{BASE_URL}/get_data_run_types'
    
    # Prepare the parameters as a dictionary (for a GET request, these are query parameters)
    params = {
        'id_category': id_category,
        'id_type': id_type,
    }

    # Make a request using the centralized arq_handle_api_request function
    response = arq_handle_api_request(url, payload=params, method='GET', metadata={'id_run': id_run})
    
    return response

def arq_save_outcome_data(metadata, id_category, id_type, v_integer=None, v_float=None, v_string=None, v_boolean=None, v_timestamp=None, v_jsonb=None):
    """
    Submits outcome data for a given run ID directly to the new architecture, accommodating various types of outcome data including a JSONB field.

    Parameters:
    - id_category (int): The category ID for the outcome.
    - id_type (int): The type ID for the outcome.
    - v_integer (int, optional): An integer value associated with the outcome.
    - v_float (float, optional): A floating-point value associated with the outcome.
    - v_string (str, optional): A string value associated with the outcome.
    - v_boolean (bool, optional): A boolean value associated with the outcome.
    - v_timestamp (datetime, optional): A timestamp associated with the outcome. Defaults to None.
    - v_jsonb (dict, optional): A JSONB field containing additional data.

    Returns:
    - bool: True if the outcome was successfully saved, False otherwise.
    """
    # Prepare the outcome data based on provided arguments
    outcome_data = {
        'id_run': metadata.get('id_run'),
        'id_category': id_category,
        'id_type': id_type,
        'v_integer': v_integer,
        'v_floatpoint': v_float,
        'v_string': v_string,
        'v_boolean': v_boolean,
        'v_timestamp': v_timestamp,
        'v_jsonb': v_jsonb,  # Add jsonb field
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # Use current time
        'service_name': service_data.get('service_name')  
    }

    # Filter out None values so they default to NULL in the database
    filtered_data = {k: v for k, v in outcome_data.items() if v is not None}

    # Log the values being saved for better transparency in debugging
    log_message = f"Attempting to save outcome: {filtered_data}"

    url = f"{BASE_URL}/post_outcome_run"

    try:
        # Use arq_handle_api_request to send the API request
        response = arq_handle_api_request(url, payload=filtered_data, metadata=metadata)
        log_to_api(metadata, f"Outcome saved successfully. timestamp: {response.get('timestamp')}", error=False,debug=True)

        print("Outcome saved successfully.")  # Adjust this to appropriate logging
        return True
    except Exception as e:
        # Log the exception using log_to_api before re-raising it
        log_to_api(metadata, f"Exception in arq_user_identify: {str(e)}", error=True)
        raise


@exception_handler_decorator
def arq_handle_api_request(url, payload=None, metadata=None, method='POST'):
    """
    Sends an API request with error handling, token authentication, or Basic Authentication (user/password).

    Args:
        url (str): The URL of the API endpoint to which the request is sent.
        payload (dict, optional): The data to be sent in the request body (for POST) or as query parameters (for GET). Defaults to None.
        metadata (dict, optional): Contains 'token_access' for Bearer token authentication, or 'user' and 'password' for Basic Authentication. Defaults to None.
        method (str): The HTTP method to use for the request ('POST' or 'GET'). Defaults to 'POST'.

    Returns:
        dict: The parsed JSON response from the API if the request is successful.

    Raises:
        APIError: If the response status code is not 200 or if a network error occurs.
    """
    headers = {}
    payload = payload or {}  # Ensure payload is not None

    # Token Authentication: Add token_access to headers as Bearer token
    if metadata and 'token_access' in metadata and metadata['token_access'] is not None:
        headers['Authorization'] = f"Bearer {metadata['token_access']}"

    # Basic Authentication: Add Authorization header
    elif metadata and 'user' in metadata and 'password' in metadata:
        auth_string = f"{metadata['user']}:{metadata['password']}"
        auth_header = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
        headers['Authorization'] = f'Basic {auth_header}'

    # Make the actual request based on method type
    if method.upper() == 'POST':
        response = requests.post(url, json=payload, headers=headers)
    elif method.upper() == 'GET':
        response = requests.get(url, params=payload, headers=headers)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")

    # Raise an HTTP error for bad responses
    response.raise_for_status()

    # Return the parsed JSON response
    return response.json()


class ArqRuns:
    @staticmethod
    def get_new_id_run(metadata):
        """
        Generates a new run ID by sending a request to the /create_new_run API endpoint with the script ID,
        user ID, optional parent run ID, and optional father service ID. The method dynamically determines the table name
        based on the provided service_name.

        The method logs both the operation's initiation and its outcome (success or failure).
        If successful, it returns the new run ID; otherwise, it logs the error and returns the error details.

        Args:
            metadata (dict): A dictionary containing the necessary data to create the run ID, including:
                - id_script (int): The unique identifier for the script whose run ID is being created.
                - id_user (int): The unique identifier for the user.
                - id_father_service (int, optional): The identifier of the father service.
                - id_father_run (str, optional): The run ID of the parent operation, if applicable.
                - user (str): The username for authentication.
                - password (str): The password for authentication.

        Returns:
            dict: The new run ID if the creation was successful; otherwise, a dictionary with error details.

        Raises:
            ValueError: If required arguments are not provided.
        """

        payload = {
            'service_name': service_name,
            'id_script': metadata.get('id_script'),
            'id_user': metadata.get('id_user'),
            'father_service_id': metadata.get('id_father_service'),
            'id_run_father': metadata.get('id_father_run'),
            'service_name': service_data.get('service_name'),  # Assuming service_name is in metadata
        }

        url = f"{BASE_URL}/create_new_run"

        try:
            # Use arq_handle_api_request to send the API request
            new_run_response = arq_handle_api_request(url, payload=payload, metadata=metadata, method='POST')

            # Process the response
            new_run_id = new_run_response.get('id_run')
            log_to_api(metadata, f"New run ID created: {new_run_id} for script ID: {metadata.get('id_script')} in service {service_name}. Executed in {new_run_response.get('execution_time_ms')} ms.", debug=True)
            return {'id_run': new_run_id}

        except Exception as e:
            log_to_api(metadata, f"Exception in get_new_id_run: {str(e)}", error=True)
            raise

    @staticmethod
    def update_run_fields(metadata, status=None, milestone_msg=None):
        """
        Updates the run status and optionally user information by making a POST request to the /update_run_status endpoint.

        Args:
            metadata (dict): A dictionary containing the necessary data to update the run, including:
                - id_run (int): The run ID to update.
                - user (str): Username for authentication.
                - password (str): Password for authentication.
                - script_start_time (float): Start time of the script.
            status (int, optional): The new status value to set. If None, the current status will be fetched and incremented by 1.
            milestone_msg (str, optional): A custom milestone message to log. Defaults to None.
            id_user (int, optional): The user ID to update. Defaults to None.

        Returns:
            dict: The response from the API.

        Raises:
            Exception: If the API call fails.
        """
        try:
            # If status is None, fetch the current run data and increment the status by 1
            if status is None:
                run_details = ArqRuns.get_run(metadata)  # Fetch the current run details
                current_status = run_details.get('status')

                if current_status is None:
                    raise ValueError(f"Run with id_run {metadata.get('id_run')} does not have a valid 'status'.")

                # Increment the status by 1
                status = current_status + 1

            # Build the payload for updating the run
            payload = {
                'id_run': metadata.get('id_run'),
                'service_name': service_data.get('service_name'),  # Assuming service_name is in metadata
                'status': status
            }

            if metadata['id_user'] is not None:
                payload['id_user'] = metadata['id_user']

            # Construct the URL for the update request
            url = f"{BASE_URL}/update_run_status"

            # Send the POST request to update the run status
            response = arq_handle_api_request(url, payload=payload,metadata=metadata, method='POST')

            # Calculate the time taken to execute the script
            executed_time_ms = int((time.time() - metadata.get("script_start_time")) * 1000)

            # Log the update operation
            if milestone_msg is None:
                milestone_msg = "This status update has been"
                debug = True
            else:
                debug = False

            log_to_api(metadata, f"Run status has been updated to: {status}", debug=True)
            log_to_api(metadata, f"{milestone_msg} executed in {executed_time_ms}ms since script started.", debug=debug)

            # Save the outcome data (if needed)
            arq_save_outcome_data(metadata=metadata, id_category=1, id_type=0, v_string=f"status={status}, {milestone_msg}", v_integer=executed_time_ms)

            # Return the response from the update request
            return response

        except Exception as e:
            log_to_api(metadata, f"Exception in update_run_fields: {str(e)}", error=True)
            raise

    @staticmethod
    def get_run(metadata):
        """
        Retrieves run information for the specified run ID by making a POST request to the /get_run endpoint.

        Args:
            metadata (dict): A dictionary containing the necessary data to retrieve the run, including:
                - id_run (int): The run ID to retrieve.
                - service_name (str): The name of the service for the run.
                - user (str): Username for authentication.
                - password (str): Password for authentication.

        Returns:
            dict: The run details returned from the API.

        Raises:
            Exception: If the API call fails.
        """
        try:
            # Extract necessary information from metadata
            service_name = service_data.get('service_name')
            id_run = metadata.get('id_run')

            if not service_name or not id_run:
                raise ValueError("Both 'service_name' and 'id_run' must be provided in metadata.")

            payload = {
                'service_name': service_name,
                'id_run': id_run
            }

            # Construct the URL for the API call
            url = f"{BASE_URL}/get_run"

            # Send the payload as a POST request to the API
            run_details = arq_handle_api_request(url, payload=payload, metadata=metadata, method='POST')

            return run_details

        except Exception as e:
            log_to_api(metadata, f"Exception in get_run: {str(e)}", error=True)
            raise


class ArqValidations:
    @staticmethod
    def validate_auth(metadata):
        """
        Validates the user based on provided credentials or token.
        
        Args:
            metadata (dict): A dictionary containing 'user', 'password', 'token_access', and 'token_refresh'.
        
        Returns:
            dict: Updated metadata with 'id_user' if valid.
                  Example: { "user": "example", "password": "password", "token_access": "abcde12345", "id_user": 123 }
                  
        Raises:
            ValidationError: If credentials or token are invalid.
        """
        token_access = metadata.get('token_access')
        token_refresh = metadata.get('token_refresh')

        if token_access:
            try:
                # Validate the token
                id_user = ArqValidations.validate_token(token_access)
                
                # Update metadata with id_user and return
                metadata['id_user'] = id_user
                return metadata
            except ValidationError as e:
                # If token is expired or invalid, fall back to user identification
                if "expired" in str(e):
                    try:
                        # Attempt to refresh the token using the refresh_token method
                        metadata = ArqValidations.refresh_token(metadata)
                        
                        # Validate the refreshed token
                        id_user = ArqValidations.validate_token(metadata['token_access'])
                        metadata['id_user'] = id_user
                        return metadata
                    except ValidationError as refresh_error:
                        # If token refresh fails, raise an expired token exception
                        raise ValidationError("The token has expired and could not be refreshed.")
                else:
                    raise e
        else:
            re_authenticate = False  # Define the re_authenticate boolean
            if re_authenticate:
                # If re_authenticate is True, proceed with username and password authentication
                result = ArqValidations.user_identify(metadata)
                metadata.update(result)
                return metadata
            else:
                # If re_authenticate is False, raise an error for no token provided
                raise ValidationError("No token provided")

    @staticmethod
    def validate_token(token):
        """
        Validate the token. If it's valid, return the user ID. 
        Otherwise, raise an exception with details about the failure.
        
        Args:
            token (str): The JWT token to validate.

        Returns:
            int: The user ID if the token is valid.
            
        Raises:
            ValidationError: If the token is expired or invalid, with specific details.
        """
        try:
            # Attempt to decode the token using the secret key and expected algorithm
            decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            return decoded.get("id_user")  # Assuming 'id_user' is the correct key here
        
        except ExpiredSignatureError:
            raise ValidationError("Token has expired")
        
        except InvalidSignatureError:
            raise ValidationError("Token signature is invalid")
        
        except InvalidIssuerError:
            raise ValidationError("Token has an invalid issuer")
        
        except InvalidAudienceError:
            raise ValidationError("Token has an invalid audience")
        
        except InvalidIssuedAtError:
            raise ValidationError("Token's 'issued at' time is invalid (in the future)")
        
        except MissingRequiredClaimError as e:
            raise ValidationError(f"Token is missing a required claim: {str(e)}")
        
        except DecodeError:
            raise ValidationError("Token is malformed and could not be decoded")
        
        except InvalidTokenError:
            raise ValidationError("Token is invalid for an unspecified reason")
        
    @staticmethod
    def refresh_token(metadata):
        """
        Refreshes the access token using the refresh token.
        
        Args:
            metadata (dict): A dictionary containing 'token_access' and 'token_refresh'.
        
        Returns:
            dict: Updated metadata with a new 'token_access' and the same 'token_refresh'.
            
        Raises:
            ValidationError: If the refresh token is invalid or expired.
        """
        # Get user manager host and port from environment variables
        user_manager_host = os.getenv('user_manager_host', 'localhost')
        user_manager_port = os.getenv('user_manager_port', 20070)
        url = f"http://{user_manager_host}:{user_manager_port}/refresh_token"

        try:
            # Call the refresh_token API using the refresh token
            response_data = arq_handle_api_request(url, metadata=metadata, method='POST')

            # Extract new access token from the response
            token_access = response_data.get('token_access', None)
            token_refresh = response_data.get('token_refresh', None)

            # Ensure we have both tokens in the response
            if token_access is None or token_refresh is None:
                raise ValidationError("Token refresh failed: Missing tokens in the API response")

            # Update metadata with new token_access and return
            metadata['token_access'] = token_access
            metadata['token_refresh'] = token_refresh
            return metadata

        except Exception as e:
            raise ValidationError(f"Error refreshing token: {str(e)}")

    @staticmethod
    def user_identify(metadata):
        """
        Method to identify the user based on username and password by calling the user validation API.
        Args:
            user (str): The username for authentication.
            pswrd (str): The password for authentication.
        Returns:
            dict: The updated metadata with 'id_user', 'token_acces', and 'token_refresh' if valid.
                  Example: { "id_user": 123, "token_acces": "abcde12345", "token_refresh": "refresh_token_value" }
        Raises:
            APIError: If the request fails due to connection issues, timeouts, or bad responses.
            ValidationError: If 'id_user' or 'token' is missing in the response.
        """
        # Get user manager host and port from environment variables
        user_manager_host = os.getenv('user_manager_host', 'localhost')
        user_manager_port = os.getenv('user_manager_port', 20070)
        url = f"http://{user_manager_host}:{user_manager_port}/get_token"

        try:
            # Call arq_handle_api_request with POST method and metadata for Basic Auth
            response_data = arq_handle_api_request(url, metadata=metadata, method='POST')

            # Extract id_user and token from the response
            id_user = response_data.get('id_user', None)
            token_access = response_data.get('token_access', None)
            token_refresh = response_data.get('token_refresh', None)
            # Check if id_user or token exists in the response
            if id_user is None or token_access is None or token_refresh is None:
                raise ValidationError("User ID or token not found in the API response")
            
            # Add id_user, token_acces, and token_refresh to metadata
            metadata['id_user'] = id_user
            metadata['token_access'] = token_access
            metadata['token_refresh'] = token_refresh
            return metadata

        except Exception as e:
            raise



# URL to get the services
get_services_url = f'{BASE_URL}/get_services'

# Make the request to get the services data
try:
    service_arch = arq_handle_api_request(url=get_services_url, method='GET')
    print("Service architecture obtained successfully.")
except Exception as e:
    print(f"Error obtaining services: {e}")
    service_arch = {}

# Validate and use service_arch
if service_arch:
    print("Contents of service_arch:")
    print(json.dumps(service_arch, indent=2))
else:
    print("Could not obtain the service architecture.")

# Get environment variables or set default values
service_name = os.getenv('SERVICE_NAME', '241002_script_interpreter_pydock')
id_service = int(os.getenv('ID_SERVICE', 0))
service_data = {
    'service_name': service_name,
    'id_service': id_service,
    'service_arch': service_arch  # Añadir el diccionario service_arch
}

