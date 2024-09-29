# Utilities_Main.py
import yaml
from Utilities_Architecture import log_to_api, arq_get_new_id_run, arq_save_outcome_data,arq_update_run_fields, ArqValidations
from Utilities_error_handling import log_and_raise, handle_exceptions, APIError,ValidationError
from flask import request
import os
import jwt
import base64

SECRET_KEY = os.getenv('SECRET_KEY', 'th3_s3cr3t_k3y')

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
            arq_save_outcome_data(
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
        'token_access' : data.get("token_access"),
        'token_refresh' : data.get("token_refresh"),
        "user": data.get("user"),    # User passed in the request
        "password": data.get("password"),  # Password passed in the request
        "id_script": data.get("id_script"),
        "use_db": data.get("use_db", True),
        "id_run": None,  # This will be set later if use_db is True
        "id_user": None,  # This will be set by validate_token_or_user
        "script_start_time": data.get("script_start_time")
    }

    def extract_user_and_password_from_headers():
        """
        Extract user and password from the Authorization header if provided.
        """
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Basic "):
            auth_base64 = auth_header.split(" ")[1]
            auth_decoded = base64.b64decode(auth_base64).decode("utf-8")
            return auth_decoded.split(":")
        return None, None


    def create_new_run_id(metadata):
        """
        Create a new run ID based on the metadata. 
        Ensure user and password are available before creating a new run.
        """
        if metadata["id_father_run"] is not None and metadata["id_father_service"] is None:
            log_and_raise(ValidationError, "id_father_service is required when id_father_run is provided", id_run=metadata.get("id_run"), context="create_new_run_id")

        if metadata["id_script"] is None:
            log_and_raise(ValidationError, "id_script is required and cannot be None", id_run=metadata.get("id_run"), context="create_new_run_id")

        new_run_id_response = arq_get_new_id_run(metadata)

        # Update metadata with new run ID
        metadata["id_run"] = new_run_id_response.get('id_run')
        metadata["token"] = new_run_id_response.get('token')

    try:
        # Step 1: Ensure the user and password are available before creating the run
        if not metadata["user"] or not metadata["password"]:
            metadata["user"], metadata["password"] = extract_user_and_password_from_headers()
        
        if metadata["use_db"]:
             # Validate the token or generate a new one
            metadata=ArqValidations.validate_auth(metadata)           
            # Create a new run ID if necessary
            create_new_run_id(metadata)

        # If everything is successful, update the run with the user_id and status
        arq_update_run_fields(metadata, milestone_msg='data_validation_metadata_generation done', id_user=metadata["id_user"])

        # Return the updated metadata
        return metadata

    except Exception as e:
        raise

    
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