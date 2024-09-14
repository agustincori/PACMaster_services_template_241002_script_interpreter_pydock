# Utilities_Main.py
import logging
import requests
import os
from Utilities_Architecture import log_to_api, get_new_runid, save_outcome_data,user_identify,update_run_status
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
    

def data_validation_metadata_generation(data):
    """
    Extract and validate request data and generate metadata dictionary.

    Parameters:
    - data (dict): The JSON payload from the request.

    Returns:
    - dict: A dictionary containing the extracted metadata.
    """

    # Initialize metadata from the beginning
    metadata = {
        "id_father_run": data.get("id_father_run"),
        "id_father_service": data.get("id_father_service"),
        "user": data.get("user"),
        "password": data.get("password"),
        "id_script": data.get("id_script"),
        "use_db": data.get("use_db", True),
        "id_run": None,  # This will be set later if use_db is True
        "id_user": None, # This will be set by validate_user
    }

    def validate_user(metadata):
        user = metadata.get("user")
        pswrd = metadata.get("password")
        id_user = user_identify(metadata)

        if id_user is None:
            log_and_raise(
                ValidationError,
                "Invalid credentials",
                id_run=metadata.get("id_run"),
                context="validate_user"
            )

        # Update metadata with id_user
        metadata["id_user"] = id_user

    def create_new_run_id(metadata):
        if metadata["id_father_run"] is not None and metadata["id_father_service"] is None:
            log_and_raise(
                ValueError,
                "id_father_service is required when id_father_run is provided",
                id_run=metadata.get("id_run"),
                context="create_new_run_id"
            )
        
        if metadata["id_script"] is None:
            log_and_raise(
                ValueError,
                "id_script is required and cannot be None",
                id_run=metadata.get("id_run"),
                context="create_new_run_id"
            )

        new_run_id_response = get_new_runid(metadata)

        if 'error' in new_run_id_response:
            details = new_run_id_response.get('message') or new_run_id_response.get('details') or 'No additional details provided.'
            log_and_raise(
                APIError,
                f"Error creating new run ID: {new_run_id_response.get('error')} - Details: {details}",
                id_run=metadata.get("id_run"),
                context="create_new_run_id"
            )

        # Update metadata with new run ID
        metadata["id_run"] = new_run_id_response.get('id_run')

    try:
        # Create a new run ID if use_db is True
        if metadata["use_db"]:
            handle_exceptions(lambda: create_new_run_id(metadata), context="method: create_new_run_id")
        
        # Validate user
        handle_exceptions(lambda: validate_user(metadata), context="method: validate_user_credentials")

        # Return the updated metadata
        return metadata

    except Exception as e:
        # log_and_raise will handle logging and raising of exceptions
        log_and_raise(Exception, str(e), id_run=metadata.get("id_run"), context="extract_and_validate_metadata")

    
