# Utilities_Main.py
import logging
import requests
import os
from Utilities_Architecture import log_to_api, get_new_runid, save_outcome_data

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

    Returns:
    - int: User ID if valid, or 0 if invalid.
    """
    user_manager_host = os.getenv('user_manager_host','localhost')
    user_manager_port = os.getenv('user_manager_port',10070)
    url = f"http://{user_manager_host}:{user_manager_port}/user_validation"

    payload = {
        "user": user,
        "pswrd": pswrd
    }

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            # Assuming the API returns a JSON response with a "user_id" field
            result = response.json()
            return result.get('id_user', None)
        else:
            return None
    except requests.exceptions.RequestException as e:
        # Log the exception or handle it as necessary
        print(f"Request failed: {e}")
        return None