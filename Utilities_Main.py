# Utilities_Main.py
import yaml
from Utilities_Architecture import log_to_api, arq_save_outcome_data, ArqValidations,ArqRuns
from Utilities_error_handling import exception_handler_decorator,ValidationError
from flask import request
import os
import base64

SECRET_KEY = os.getenv('SECRET_KEY', 'th3_s3cr3t_k3y')

@exception_handler_decorator
def compute_and_save(data, metadata, use_db=True):
    """
    Computes the result of a specified mathematical operation on two numbers and saves the arguments and the result.

    Parameters:
    - data (dict): A dictionary containing the arguments. Should contain 'arg1', 'arg2', and 'operation'.
    - metadata (dict): A dictionary containing metadata, including 'id_run'.
    - use_db (bool): Whether to use a database connection for logging and saving outcome data. Defaults to True.

    Returns:
    - dict: A dictionary containing the result of the computation.

    Raises:
    - ValidationError: If 'arg1', 'arg2', or 'operation' are missing, or if the operation is invalid.
    - Exception: For any other exceptions during the computation.
    """
    id_run = metadata.get('id_run')

    # Extract arguments
    arg1 = data.get('arg1')
    arg2 = data.get('arg2')
    operation = data.get('operation')

    # Check if arg1, arg2, and operation are provided
    if arg1 is None or arg2 is None or operation is None:
        raise ValidationError("arg1, arg2, and operation are required in data dictionary")

    # Attempt to convert arg1 and arg2 to numbers
    try:
        arg1 = float(arg1)
        arg2 = float(arg2)
    except ValueError as ve:
        raise ValidationError(f"arg1 and arg2 must be numbers. Error: {ve}")

    # Perform the specified operation
    if operation == "sum":
        result = arg1 + arg2
    elif operation == "diff":
        result = arg1 - arg2
    elif operation == "mult":
        result = arg1 * arg2
    elif operation == "div":
        if arg2 == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        result = arg1 / arg2
    elif operation == "pwr":
        result = arg1 ** arg2
    elif operation == "root":
        if arg1 < 0 and arg2 % 2 == 0:
            raise ValidationError("Even roots of negative numbers are not allowed")
        result = arg1 ** (1 / arg2)
    else:
        raise ValidationError(f"Invalid operation '{operation}' specified.- operations available are: sum, diff, mult, div, pwr, root")

    input_data = {"arg1": arg1, "arg2": arg2, "operation": operation}

    # Save or log outcome data if necessary
    if use_db:
        log_to_api(metadata, log_message=f"Arguments: arg1 = {arg1}, arg2 = {arg2}, operation = {operation}, result = {result}", use_db=use_db)
        arq_save_outcome_data(
            metadata=metadata,
            id_category=0,
            id_type=0,
            v_jsonb=input_data
        )
        arq_save_outcome_data(
            metadata=metadata,
            id_category=0,
            id_type=1,
            v_float=result
        )
        log_to_api(metadata, log_message="Income & outcome data saved successfully.", use_db=use_db)
    else:
        print("Income data:", input_data)

    # Return the result data
    return {
        "result": result
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


    @exception_handler_decorator
    def create_new_run_id(metadata):
        """
        Create a new run ID based on the metadata.
        Ensure user and password are available before creating a new run.
        Args:
            metadata (dict): Contains information needed to create a new run, including 'id_father_run', 'id_father_service', and 'id_script'.
        Returns:
            dict: Response containing the new run ID.\
        Raises:
            ValidationError: If 'id_father_service' or 'id_script' are not provided when required.
        """
        # Validate presence of id_father_service if id_father_run is provided
        if metadata.get("id_father_run") is not None and metadata.get("id_father_service") is None:
            raise ValidationError("id_father_service is required when id_father_run is provided", metadata.get("id_run"))
        # Validate presence of id_script
        if metadata.get("id_script") is None:
            raise ValidationError("id_script is required and cannot be None", metadata.get("id_run"))
        # Call to get a new run ID
        new_run_id_response = ArqRuns.get_new_id_run(metadata)
        # Update metadata with the new run ID
        metadata["id_run"] = new_run_id_response.get('id_run')
        # Return the updated metadata with the new run ID
        return metadata

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
        ArqRuns.update_run_fields(metadata, milestone_msg='data_validation_metadata_generation done')

        # Return the updated metadata
        return metadata

    except Exception as e:
        raise

    
@exception_handler_decorator
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
            raise ValidationError(f"YAML parsing error: {str(e)}")
    
    elif request.content_type == 'application/json':
        data = request.get_json()  # Parse JSON payload
        return data
    
    else:
        raise ValidationError("Unsupported content type. Use application/json or application/x-yaml.")