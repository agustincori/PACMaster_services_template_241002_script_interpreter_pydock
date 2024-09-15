"""
Utilities_Architecture.py

This module contains utility functions to interact with a specific API for logging, user identification, managing run outcomes, and handling API requests.

Functions:
    log_to_api(metadata, log_message, debug=False, warning=False, error=False, use_db=True):
        Sends a log message to the API with an associated run ID and log type indicators.

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

    get_new_runid(metadata):
        Generates a new run ID for a script and logs the operation.

        Args:
            metadata (dict): Contains the necessary data to create a new run ID, including:
                - id_script (int): The unique identifier for the script whose run ID is being created.
                - id_user (int): The unique identifier for the user.
                - id_father_service (int, optional): The identifier of the father service.
                - id_father_run (str, optional): The run ID of the parent operation, if applicable.
                - user (str): Username for authentication.
                - password (str): Password for authentication.

    update_run_status(metadata, status=None):
        Updates the run status using the provided metadata and optional status value.

        Args:
            metadata (dict): Contains the necessary data to update the run status, including:
                - id_run (int): The run ID to update.
                - user (str): Username for authentication.
                - password (str): Password for authentication.
            status (int, optional): The new status value to set. Defaults to None.

    user_identify(metadata):
        Identifies the user by calling the user validation API and updates the run status accordingly.

        Args:
            metadata (dict): Contains necessary information to identify the user and update run status, including:
                - user (str): The username for authentication.
                - password (str): The password for authentication.
                - id_run (int): The run ID for logging and updating the run.

    get_data_type(id_category, id_type, id_run=None):
        Fetches data types from the API based on category and type IDs.

        Args:
            id_category (int): The ID of the category to filter the data types.
            id_type (int): The ID of the type to filter the data types.
            id_run (int, optional): The ID of the associated run for logging purposes. Defaults to None.

    save_outcome_data(new_run_id, id_category, id_type, v_integer=None, v_float=None, v_string=None, v_boolean=None, v_timestamp=None, v_jsonb=None):
        Submits outcome data for a given run ID.

        Args:
            new_run_id (int): The new run ID for which to save the outcome.
            id_category (int): The category ID for the outcome.
            id_type (int): The type ID for the outcome.
            v_integer (int, optional): An integer value associated with the outcome.
            v_float (float, optional): A floating-point value associated with the outcome.
            v_string (str, optional): A string value associated with the outcome.
            v_boolean (bool, optional): A boolean value associated with the outcome.
            v_timestamp (datetime, optional): A timestamp associated with the outcome. Defaults to None.
            v_jsonb (dict, optional): A JSONB field containing additional data.

    update_run_fields(id_run, id_user=None, status=None):
        Updates fields of a run, such as user ID and status.

        Args:
            id_run (int): The ID of the run to update.
            id_user (int, optional): The user ID to update. Defaults to None.
            status (int, optional): The status to update. Defaults to None.

    handle_api_request(url, payload=None, method='POST', id_run=None):
        Sends an API request with error handling and logging.

        Args:
            url (str): The URL of the API endpoint to which the request is sent.
            payload (dict, optional): The data to be sent in the request body (for POST) or as query parameters (for GET). Defaults to None.
            method (str, optional): The HTTP method to use for the request ('POST' or 'GET'). Defaults to 'POST'.
            id_run (int, optional): The ID of the associated run for logging purposes. Defaults to None.
"""

import requests
import os
from datetime import datetime
import time
from Utilities_error_handling import log_and_raise,handle_exceptions,APIError,HTTPError,ValidationError

# Obtener host y puerto desde variables de entorno
db_manager_HOST = os.getenv('db_manager_HOST', 'localhost')
db_manager_PORT = os.getenv('db_manager_PORT', '20083')
BASE_URL = f'http://{db_manager_HOST}:{db_manager_PORT}'

# Get environment variables or set default values
service_name = os.getenv('SERVICE_NAME', '240813_service_sum_pydock')
id_service = int(os.getenv('ID_SERVICE', 1))
service_data = {
    'service_name': service_name,
    'id_service': id_service
}


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
    id_run = metadata.get('id_run')
    user = metadata.get('user')
    password = metadata.get('password')

    if not use_db or id_run is None:
        print(log_message_with_timestamp)  # Print the log message with timestamp
        return

    # Prepare the data for the POST request
    log_data = {
        'service_name': service_name,
        'id_run': id_run,
        'log': log_message_with_timestamp,
        'user': user,
        'password': password,
        'debug': debug,
        'warning': warning,
        'error': error
    }

    url = f'{BASE_URL}/insert_log'

    try:
        # Use handle_api_request to send the request with proper error handling
        response = handle_api_request(url, payload=log_data, method='POST', id_run=id_run)
        # If the request is successful, print the log message
        print(log_message_with_timestamp)
    except Exception as e:
        # Handle exceptions using centralized error handling
        # Since this is the logging function, we might not want to raise exceptions further
        # Instead, we can print the error message
        print(f"Error logging to API: {str(e)}")



def get_new_runid(metadata):
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
        'user': metadata.get('user'),
        'password': metadata.get('password')
    }

    url = f"{BASE_URL}/create_new_run"

    try:
        # Use handle_api_request to send the API request
        new_run_response = handle_api_request(url, payload=payload, method='POST')

        # Process the response
        new_run_id = new_run_response.get('id_run')
        if new_run_id:
            log_to_api(metadata,f"New run ID created: {new_run_id} for script ID: {metadata.get('id_script')} in service {service_name}. Executed in {new_run_response.get('execution_time_ms')} ms.",debug=True)
            return {'id_run': new_run_id}
        else:
            log_and_raise(APIError, "Run ID not found in the response", id_run=None, context="get_new_runid")

    except Exception as e:
        log_and_raise(APIError, f"Error in get_new_runid: {str(e)}", id_run=None, context="get_new_runid")


def update_run_fields(id_run, id_user=None, status=None):
    """
    Function to update the run with the given id_user and/or status.
    
    Args:
        id_run (int): The ID of the run to update.
        id_user (int, optional): The user ID to update. Defaults to None.
        status (int, optional): The status to update. Defaults to None.

    Returns:
        tuple: (response_json, status_code)
    """
    # Build the payload for updating the run
    update_data = {
        "id_run": id_run
    }

    if id_user is not None:
        update_data['id_user'] = id_user

    if status is not None:
        update_data['status'] = status

    # Make an API call to the update endpoint (or use a DB function if available)
    response = requests.put(f'{BASE_URL}/update_run', json=update_data)

    # Return the response in a tuple (response JSON and status code)
    return response.json(), response.status_code

    
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
        dict: JSON object with error details if the request failed or the server responded with a status code indicating an error.
    """
    
    # Define the endpoint URL
    url = f'{BASE_URL}/get_data_run_types'
    
    # Prepare the parameters as a dictionary (for a GET request, these are query parameters)
    params = {
        'id_category': id_category,
        'id_type': id_type,
    }
    
    try:
        # Make a request using the centralized handle_api_request function
        response = handle_exceptions(
            lambda: handle_api_request(url, payload=params,method='GET', id_run=id_run),
            context=f"get_data_type: {url}",
            id_run=id_run
        )
        return response

    except Exception as e:
        # Log the exception before raising it further
        log_to_api(id_run, f"Exception in get_data_type: {str(e)}", error=True)
        raise

def save_outcome_data(metadata, id_category, id_type, v_integer=None, v_float=None, v_string=None, v_boolean=None, v_timestamp=None, v_jsonb=None):
    """
    Submits outcome data for a given run ID directly to the new architecture, accommodating various types of outcome data including a JSONB field.

    Parameters:
    - new_run_id (int): The new run ID for which to save the outcome.
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
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Use current time
    }

    # Filter out None values so they default to NULL in the database
    filtered_data = {k: v for k, v in outcome_data.items() if v is not None}

    # Log the values being saved for better transparency in debugging
    log_message = f"Attempting to save outcome: {filtered_data}"

    # Submit the outcome data to the API
    outcome_response = requests.post(f'{BASE_URL}/insert_outcome_run', json=filtered_data)
    
    if outcome_response.status_code == 201:
        print("Outcome saved successfully.")  # Adjust this to appropriate logging
        return True
    else:
        print(f"Failed to save outcome. Response: {outcome_response.text}")  # Adjust this to appropriate logging
        return False

def update_run_status(metadata, status=None):
    """
    Updates the run with the given id_run by making a POST request to the /update_run_status endpoint.

    Args:
        metadata (dict): A dictionary containing the necessary data to update the run, including:
            - id_run (int): The run ID to update.
            - user (str): Username for authentication.
            - password (str): Password for authentication.
            - script_start_time
        status (int, optional): The new status value to set.

    Returns:
        dict: The response from the API.

    Raises:
        Exception: If the API call fails.
    """
    payload = {
        'id_run': metadata.get('id_run'),
        'service_name': service_name,  # Assuming service_name is set globally
        'user': metadata.get('user'),
        'password': metadata.get('password'),
    }
    
    if status is not None:
        payload['status'] = status

    url = f"{BASE_URL}/update_run_status"

    try:
        # Use handle_api_request to send the API request
        response = handle_api_request(url, payload=payload)
        
        # If there's an error in the response, raise an error with proper logging
        if 'error' in response:
            log_and_raise(APIError, f"Error updating run status: {response['error']}", id_run=metadata.get('id_run'), context="update_run_status")
        executed_time_ms=int((time.time() - metadata.get("script_start_time")) * 1000)
        log_to_api(metadata,f"Run status has been updated to: {status}. Executed in {executed_time_ms}ms since script started.",debug=True)
        save_outcome_data(metadata=metadata,id_category=1,id_type=0,v_string=f"status={status}",v_integer=executed_time_ms)
        # Return the response if successful
        return response

    except Exception as e:
        # Handle any unexpected errors and log them properly
        log_and_raise(APIError, f"Error in update_run_status: {str(e)}", id_run=metadata.get('id_run'), context="update_run_status")



def user_identify(metadata):
    """
    Identifies the user by calling the user validation API and updates the run status accordingly.

    Args:
        metadata (dict): A dictionary containing necessary information including:
            - user (str): The username for authentication.
            - password (str): The password for authentication.
            - id_run (int): The run ID for logging and updating the run.

    Returns:
        int: User ID if valid.

    Raises:
        ValidationError: If the request fails or the user is invalid.
    """
    # Get user manager host and port from environment variables
    user_manager_host = os.getenv("user_manager_host", "localhost")
    user_manager_port = os.getenv("user_manager_port", "20070")
    url = f"http://{user_manager_host}:{user_manager_port}/user_validation"

    payload = {
        "user": metadata.get("user"),
        "pswrd": metadata.get("password"),
    }

    id_run = metadata.get("id_run")

    # Call the user validation API
    try:
        result = handle_api_request(url, payload=payload, id_run=id_run)
        id_user = result.get("id_user")

        # Check if user_id exists
        if id_user is None:
            log_and_raise(
                ValidationError,
                "User ID not found in the API response",
                id_run=id_run,
                context="user_identify",
            )

        # Update metadata with the user_id
        metadata["id_user"] = id_user
        log_to_api(metadata, f"User identified successfully: id_user={id_user}. Executed in {result.get('execution_time_ms')} ms.", debug=True, use_db=True)

        return id_user

    except Exception as e:
        # Handle and raise exceptions
        log_and_raise(APIError, f"Error in user_identify: {str(e)}", id_run=id_run, context="user_identify")



def handle_api_request(url, payload=None, method='POST', id_run=None):
    """
    Sends an API request with error handling and logging.

    Args:
        url (str): The URL of the API endpoint to which the request is sent.
        payload (dict, optional): The data to be sent in the request body (for POST) or as query parameters (for GET). Defaults to None.
        method (str): The HTTP method to use for the request ('POST' or 'GET'). Defaults to 'POST'.
        id_run (int, optional): The ID of the associated run for logging purposes. Defaults to None.

    Returns:
        dict: The parsed JSON response from the API if the request is successful.

    Raises:
        APIError: If the response status code is not 200 or if a network error occurs.
    """

    def request_func():
        if method.upper() == 'POST':
            response = requests.post(url, json=payload)
        elif method.upper() == 'GET':
            response = requests.get(url, params=payload)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        # If the response status code indicates an error, handle it
        if response.status_code >= 400:
            try:
                # Attempt to parse the error response as JSON
                error_info = response.json()
            except ValueError:
                # If parsing fails, use the response text
                error_info = {'error': response.text}

            # Extract error details
            service_name = error_info.get('service')
            route_name = error_info.get('method') or error_info.get('route_name')
            error_message = error_info.get('error', 'Unknown error occurred')

            # Raise an APIError with detailed information
            raise APIError(
                message=f"Error from service '{service_name}', route '{route_name}': {error_message}",
                status_code=response.status_code,
                details=error_info
            )

        response.raise_for_status()  # Raises HTTPError if status code >= 400
        return response

    try:
        # Use handle_exceptions to manage error handling and logging
        response = handle_exceptions(request_func, context=f"handle_api_request: {url}", id_run=id_run)
        return response.json()

    except Exception as e:
        # Log the exception using log_to_api before re-raising it
        log_to_api(id_run, f"Exception in handle_api_request: {str(e)}", error=True)
        raise  # Re-raise the exception to propagate it upstream