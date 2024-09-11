# Utilities_Main.py
import logging
import requests
import os
from Utilities_Architecture import log_to_api, get_new_runid, save_outcome_data,handle_api_request
from Utilities_error_handling import log_and_raise, handle_exceptions, APIError,HTTPError,ValidationError


def SumAndSave(arg1, arg2, run_id=None, use_db=False):
    """
    Computes the sum of two numbers and saves the arguments and the result.

    Parameters:
    - arg1 (int or float): The first number.
    - arg2 (int or float): The second number.
    - run_id (int, optional): The run ID for logging and saving outcome data.
    - use_db (bool): Whether to use database connection for logging and saving outcome data. Defaults to True.

    Returns:
    - dict: A dictionary containing the arguments and the result of the summation, or error details if an error occurs.
    """
    try:
        result = arg1 + arg2
        outcome_data = {"arg1": arg1, "arg2": arg2, "sum": result}

        if use_db and run_id is not None:
            from Utilities_Architecture import log_to_api, save_outcome_data
            log_to_api(id_run=run_id, log_message=f"Arguments: arg1 = {arg1}, arg2 = {arg2}, sum = {result}", debug=False, warning=False, error=False, use_db=use_db)
            save_outcome_data(run_id, 1, 0, v_jsonb=outcome_data)
            log_to_api(id_run=run_id, log_message="Outcome data saved successfully.", debug=False, warning=False, error=False, use_db=use_db)
        else:
            print("Outcome data:", outcome_data)
        
        return outcome_data
        
    except Exception as e:
        error_message = f"An error occurred during summation: {e}"
        if use_db and run_id is not None:
            from Utilities_Architecture import log_to_api
            log_to_api(id_run=run_id, log_message=error_message, debug=False, warning=False, error=True, use_db=use_db)
        return {
            'error': 'SummationError',
            'message': error_message
        }
    
def user_identify(user, pswrd):
    """
    Method to identify the user based on username and password by calling the user validation API.

    Args:
        user (str): The username for authentication.
        pswrd (str): The password for authentication.
        id_run (int, optional): The run ID for logging. Defaults to None.

    Returns:
        int: User ID if valid, or None if the request fails or user is invalid.

    Raises:
        APIError: If the request fails due to connection issues, timeouts, or bad responses.
    """
    # Get user manager host and port from environment variables
    user_manager_host = os.getenv('user_manager_host', 'localhost')
    user_manager_port = os.getenv('user_manager_port', 20070)
    url = f"http://{user_manager_host}:{user_manager_port}/user_validation"

    payload = {
        "user": user,
        "pswrd": pswrd
    }

    def request_func():
        result = handle_api_request(url, payload=payload)
        user_id = result.get('id_user', None)

        # Check if user_id exists
        if user_id is None:
            raise ValidationError("User ID not found in the API response")
        return user_id

    try:
        # Use handle_exceptions to wrap the request function
        return handle_exceptions(request_func, context="method: user_identify")

    except Exception as e:
        log_to_api(None, f"Exception in user_identify: {str(e)}", error=True)
        raise

    


def extract_and_validate_metadata(data):
    """
    Extract and validate metadata from the request data.

    Parameters:
    - data (dict): The JSON payload from the request.

    Returns:
    - dict: A dictionary containing the extracted metadata and a potential new_run_id.
    - dict: A dictionary containing error information if validation fails.
    """
    def validate_user():
        user = data.get("user", None)
        pswrd = data.get("password", None)
        id_user = user_identify(user, pswrd)
        if id_user is None:
            raise ValidationError("Invalid credentials")
        return id_user

    def create_new_run_id(id_user):
        id_father_run = data.get("id_father_run", None)
        id_father_service = data.get("id_father_service", None)
        if id_father_run is not None and id_father_service is None:
            raise ValueError("id_father_service is required when id_father_run is provided")
        new_run_id_response = get_new_runid(id_script=1, id_user=id_user, id_father_service=id_father_service, id_father_run=id_father_run)
        if 'error' in new_run_id_response:
            details = new_run_id_response.get('message') or new_run_id_response.get('details') or 'No additional details provided.'
            raise APIError(f"Error creating new run ID: {new_run_id_response.get('error')} - Details: {details}")
        return new_run_id_response.get('id_run')

    try:
        # Validate user
        id_user = handle_exceptions(lambda: validate_user(), context="method: validate_user_credentials")
        
        # Create a new run ID if use_db is True
        use_db = data.get("use_db", True)
        new_run_id = handle_exceptions(lambda: create_new_run_id(id_user), context="method: create_new_run_id") if use_db else None

        # Extract metadata and return
        return {
            "id_father_run": data.get("id_father_run"),
            "id_father_service": data.get("id_father_service"),
            "user": data.get("user"),
            "use_db": use_db,
            "new_run_id": new_run_id
        }, None

    except Exception as e:
        log_to_api(None, f"Exception in extract_and_validate_metadata: {str(e)}", error=True)
        raise
    
