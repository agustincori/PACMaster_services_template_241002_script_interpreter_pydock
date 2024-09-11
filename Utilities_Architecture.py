"""
Utilities_Architecture.py

This module contains utility functions to interact with a specific API for logging and managing run outcomes and port assignments.

Functions:
    log_to_api(id_run, log_message, debug=False, warning=False, error=False):
        Logs a message to the API with an associated run ID and log type indicators.

    get_new_runid(idscript, id_category=None, FatherRunid=None):
        Generates a new run ID for a script and logs the operation.

    get_data_type(id_category, id_type):
        Fetches data types from the API based on category and type IDs.

    save_outcome_data(new_run_id, id_category, id_type, v_integer=None, v_float=None, v_string=None, v_boolean=None, v_timestamp=None, v_jsonb=None):
        Submits outcome data for a given run ID.

    get_projecttype(projectname=None, id_project=None):
        Fetches project type information based on project name or project ID.

    v1.0 Init
    v1.1 Added use_db parameter to log_to_api
    v1.2 Improved Error Handling new_run, get_data_type
"""


import requests
import os
from datetime import datetime
import logging
from Utilities_error_handling import log_and_raise,handle_exceptions,APIError,HTTPError

# Obtener host y puerto desde variables de entorno
db_manager_HOST = os.getenv('db_manager_HOST', 'localhost')
db_manager_PORT = os.getenv('db_manager_PORT', '20082')
BASE_URL = f'http://{db_manager_HOST}:{db_manager_PORT}'


def log_to_api(id_run, log_message, debug=False, warning=False, error=False, use_db=True):
    # Get current timestamp in the desired format
    timestamp = datetime.now().strftime('%H:%M:%S:%f')[:-3]  # '%f' gives microseconds, slicing to get milliseconds
    
    # Prepend timestamp to the log message
    log_message_with_timestamp = f"{timestamp} {log_message}"
    
    if not use_db or id_run==None: 
        print(log_message_with_timestamp)  # Print the log message with timestamp
        return
    
    # Prepare the data for the POST request
    log_data = {
        'id_run': id_run,
        'log': log_message_with_timestamp,
        'debug': debug,
        'warning': warning,
        'error': error
    }
    
    # Send the request to the Flask API
    response = requests.post(f'{BASE_URL}/insert_log', json=log_data)
    
    # Check for errors in the response
    if response.status_code != 201:
        print(f"Error logging: {response.text}")
    else:
        print(log_message_with_timestamp)

def get_new_runid(id_script, id_user, id_father_service=None, id_category=None, id_father_run=None):
    """
    Generates a new run ID by sending a request to a specific endpoint with the script ID,
    user ID, optional parent run ID, and optional father service ID. It fetches the script's
    category and type by ID, logs the operation, and handles the creation of a new run ID.

    The method logs both the operation's initiation and its outcome (success or failure).
    If successful, it returns the new run ID; otherwise, it logs the error and returns the error details.

    Args:
        id_script (int): The unique identifier for the script whose run ID is being created.
        id_user (int): The unique identifier for the user.
        id_father_service (int, optional): The identifier of the father service. Required if id_father_run is provided.
        id_category (int, optional): The category ID of the script. If not provided, a default value is used.
        id_father_run (str, optional): The run ID of the parent operation, if applicable.

    Returns:
        dict: The new run ID if the creation was successful; otherwise, a dictionary with error details.

    Raises:
        ValueError: If required arguments are not provided.
    """
    # Validate required arguments
    if id_user is None:
        raise ValueError("id_user is required and cannot be None")

    if (id_father_run is not None and id_father_service is None) or (id_father_run is None and id_father_service is not None):
        raise ValueError("id_father_service and id_father_run must either both be provided or both be None")

    # Ensure get_data_type returns a dictionary or handle it appropriately here
    data_type = get_data_type(id_category if id_category is not None else 0, id_script)
    
    if 'error' in data_type:
        error_message = data_type.get('error', 'Unknown error occurred while fetching data type.')
        details = data_type.get('message') or data_type.get('details') or 'No additional details provided.'
        # Check if the error message indicates a connection issue
        connection_error_keywords = ["Max retries", "Failed to establish a new connection", "No connection could be made"]
        use_db = True  # Default value for use_db
        if any(keyword in details for keyword in connection_error_keywords):
            use_db = False
        log_to_api(id_script, f"Error fetching data type: {error_message} - Details: {details}", debug=True, error=True, use_db=use_db)
        return data_type

    if isinstance(data_type, list) and len(data_type) > 0:
        data_type = data_type[0]  # Assuming the first item is the relevant one

    script_name = f"{data_type.get('category_name', 'Unknown')} - {data_type.get('type_name', 'Script')}" if data_type else 'Unknown Script'

    # Prepare the payload for the POST request
    payload = {
        'id_script': id_script,
        'id_user': id_user,
        'father_service_id': id_father_service,
        'id_run_father': id_father_run
    }

    try:
        # Send a POST request to the new API endpoint
        new_run_response = requests.post(f'{BASE_URL}/create_new_run', json=payload)
        new_run_response.raise_for_status()  # Raise an error for bad status codes

        if new_run_response.status_code == 201:
            new_run_id = new_run_response.json().get('id_run')

            # Log the running script name and creation of a new run ID
            log_to_api(new_run_id, f'Running {script_name}', debug=True)
            log_to_api(new_run_id, f"New run ID created: {new_run_id} for script ID: {id_script}", debug=True)

            return {'id_run': new_run_id}
        else:
            error_response = new_run_response.json()
            log_to_api(id_script, f"Error creating new run: {error_response.get('message', 'Unknown error')}", debug=True, error=True)
            return error_response
    except requests.RequestException as e:
        # Log any exceptions that occur during the request
        logging.error(f'RequestException: {str(e)}')
        error_response = {
            'error': 'RequestException occurred',
            'message': str(e)
        }
        log_to_api(id_script, f"RequestException: {str(e)}", debug=True, error=True)
        return error_response



    
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
    
def save_outcome_data(new_run_id, id_category, id_type, v_integer=None, v_float=None, v_string=None, v_boolean=None, v_timestamp=None, v_jsonb=None):
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
        'id_run': new_run_id,
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

def get_projecttype(projectname=None, id_project=None):
    """
    Fetches project type based on project name or project ID.

    Parameters:
    - projectname (str, optional): The name of the project.
    - id_project (int, optional): The ID of the project.

    Returns:
    - A JSON response containing the project types matching the criteria, or None if an error occurred.
    """
    base_url = f'{BASE_URL}/get_data_run_types'
    params = {}

    # Add parameters to the query string if they are provided
    if projectname is not None:
        params['type_name'] = projectname
    if id_project is not None:
        params['id_type'] = id_project
    params['id_category'] = 4
    # Make the GET request with the query parameters
    try:
        response = requests.get(base_url, params=params)
        
        if response.status_code == 200:
            # If the request was successful, parse and return the JSON data
            project_types = response.json()
            log_to_api(0, f"Successfully fetched project types: {project_types}", debug=True)  # Example log, adjust as necessary
            return project_types
        else:
            # Log and return None if the request was unsuccessful
            log_to_api(0, f"Failed to fetch project types. Status code: {response.status_code}", debug=True, error=True)
            return None
    except Exception as e:
        # Log any exceptions that occur during the request
        log_to_api(0, f"Exception occurred while fetching project types: {e}", debug=True, error=True)
        return None

def handle_api_request(url, payload=None, method='POST', id_run=None):
    """
    Sends an API request with error handling and logging.

    This method sends a request (GET or POST) to the provided URL with the given payload and logs any 
    errors encountered during the request.

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