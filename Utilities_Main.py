# Utilities_Main.py
import yaml
from Utilities_Architecture import log_to_api, get_new_runid, save_outcome_data,user_identify,update_run_status
from Utilities_error_handling import log_and_raise, handle_exceptions, APIError,ValidationError
from flask import request

def sum_and_save(data, metadata, use_db=True):
    """
    Computes the sum of two numbers and saves the arguments and the result.

    Parameters:
    - data (dict): A dictionary containing the arguments. Should contain 'arg1' and 'arg2'.
    - metadata (dict): A dictionary containing metadata, including 'id_run'.
    - use_db (bool): Whether to use database connection for logging and saving outcome data. Defaults to True.

    Returns:
    - dict: A dictionary containing the arguments and the result of the summation.

    Raises:
    - ValidationError: If arg1 or arg2 are missing or not numbers.
    - Exception: For any other exceptions during the summation.
    """
    id_run = metadata.get('id_run')

    try:
        # Extract arguments
        arg1 = data.get('arg1')
        arg2 = data.get('arg2')

        # Check if arg1 and arg2 are provided
        if arg1 is None or arg2 is None:
            log_and_raise(
                ValidationError,
                "arg1 and arg2 are required in data dictionary",
                id_run=id_run,
                context="sum_and_save"
            )

        # Attempt to convert arg1 and arg2 to numbers
        try:
            arg1 = float(arg1)
            arg2 = float(arg2)
        except ValueError as ve:
            log_and_raise(
                ValidationError,
                f"arg1 and arg2 must be numbers. Error: {ve}",
                id_run=id_run,
                context="sum_and_save"
            )

        # Perform the summation
        result = arg1 + arg2

        outcome_data = {"arg1": arg1, "arg2": arg2, "sum": result}

        if use_db and id_run is not None:
            log_to_api(metadata, log_message=f"Arguments: arg1 = {arg1}, arg2 = {arg2}, sum = {result}", use_db=use_db)
            save_outcome_data(
                metadata=metadata,
                id_category=1,
                id_type=0,
                v_jsonb=outcome_data
            )
            log_to_api(metadata, log_message="Outcome data saved successfully.", use_db=use_db)
        else:
            print("Outcome data:", outcome_data)

        # Return the result data
        return {
            "result": result,
            "id_run": id_run
        }

    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        if use_db and id_run is not None:
            log_to_api(metadata, log_message=error_message, error=True, use_db=use_db)
        # Log and raise the exception
        log_and_raise(
            type(e),
            error_message,
            id_run=id_run,
            context="sum_and_save"
        )

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
        "script_start_time":data.get("script_start_time")
    }

    def validate_user(metadata):
        user = metadata.get("user")
        password = metadata.get("password")
        if user is None or password is None:
            log_and_raise(
                ValidationError,
                "User and password are required for authentication",
                id_run=metadata.get("id_run"),
                context="validate_user"
            )

        # Assume user_identify returns an id_user or None
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
                ValidationError,
                "id_father_service is required when id_father_run is provided",
                id_run=metadata.get("id_run"),
                context="create_new_run_id"
            )

        if metadata["id_script"] is None:
            log_and_raise(
                ValidationError,
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
        if metadata["use_db"]:
            handle_exceptions(lambda: create_new_run_id(metadata), context="method: create_new_run_id")     # Create a new run ID 
            handle_exceptions(lambda: validate_user(metadata), context="method: validate_user_credentials") # Validate user

        # If user validation is successful, update the run with the user_id and status
        update_run_status(metadata, status=1)
        # Return the updated metadata
        return metadata

    except Exception as e:
        # log_and_raise will handle logging and raising of exceptions
        log_and_raise(Exception, str(e), id_run=metadata.get("id_run"), context="data_validation_metadata_generation")

    
def parse_request_data():
    """
    Parses the request data based on the Content-Type header.

    Returns:
    dict: The parsed data from the request.

    Raises:
    ValidationError: If the content type is unsupported or parsing fails.
    """
    if request.content_type in ['application/x-yaml', 'text/yaml']:
        try:
            data = yaml.safe_load(request.data)  # Parse the YAML payload
            return data
        except yaml.YAMLError as e:
            log_and_raise(
                ValidationError,
                f"YAML parsing error: {str(e)}",
                context="parse_request_data"
            )
    elif request.content_type == 'application/json':
        data = request.get_json()  # Parse JSON payload
        return data
    else:
        log_and_raise(
            ValidationError,
            "Unsupported content type. Use application/json or application/x-yaml.",
            context="parse_request_data"
        )