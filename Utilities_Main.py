# Utilities_Main.py
import yaml
from Utilities_Architecture import log_to_api, arq_save_outcome_data, ArqValidations,ArqRuns,arq_handle_api_request,service_data
from Utilities_error_handling import exception_handler_decorator,ValidationError
from flask import request
import os
import stat 
import base64
import json
import logging


SECRET_KEY = os.getenv('SECRET_KEY', 'th3_s3cr3t_k3y')
ALLOWED_EXTENSIONS = {'yaml', 'yml'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # Maximum allowed size is 10 MB


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
    def extract_token_access_from_headers():
        """
        Extract the token_access from the request headers if provided.
        
        Returns:
        - token_access (str): The value of the token_access header, or None if not provided.
        """
        auth_header = request.headers.get("Authorization")
        
        if auth_header and auth_header.startswith("Bearer "):
            token_access = auth_header.split(" ")[1]  # Extract the token after 'Bearer'
            return token_access
        else:
            return None

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
        
        # Step 2: Ensure the token_access is available
        if not metadata.get("token_access"):
            metadata["token_access"] = extract_token_access_from_headers()
        
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
    


class ScriptManagement:
    @staticmethod
    @exception_handler_decorator
    def extract_script_data(input_data, metadata):
        """
        Extracts environment variables and script stack from input data, and adds script_name from headers.

        Parameters:
        - input_data (dict): The input data containing common_data and stack_scripts.

        Returns:
        - dict: A dictionary containing env_variables, stack_scripts, and script_name.

        Raises:
        - ValidationError: If 'common_data', 'stack_scripts', 'services', 'user', or 'password' are missing.
        """
        env_variables = input_data.get("env_variables")
        stack_scripts = input_data.get("stack_scripts")

        # Get the script_name from the header
        script_name = request.headers.get("X-Script-Name", "### no_header ###")  # Default value if header is not present

        if not stack_scripts:
            raise ValidationError("Invalid payload: 'stack_scripts' are required.")

        # Create a single dictionary 'script' with 'env_variables', 'stack_scripts', and 'script_name'
        script = {
            "env_variables": env_variables,
            "stack_scripts": stack_scripts,
            "script_name": script_name
        }

        arq_save_outcome_data(
            metadata=metadata,
            id_category=0,
            id_type=0,
            v_string=script_name  # Use the updated script dictionary
        )

        # Log each parameter in 'env_variables'
        if env_variables:
            for key, value in script['env_variables'].items():
                log_message = f"env_variables parameter: {key} = {value}"
                log_to_api(metadata, log_message=log_message, use_db=True)

        # Log each parameter in 'stack_scripts'
        if isinstance(script['stack_scripts'], list):
            for index, item in enumerate(script['stack_scripts']):
                log_message = f"stack_scripts item {index}: {item}"
                log_to_api(metadata, log_message=log_message, use_db=True)
        else:
            for key, value in script['stack_scripts'].items():
                log_message = f"stack_scripts parameter: {key} = {value}"
                log_to_api(metadata, log_message=log_message, use_db=True)
            
        return script
    
    @staticmethod
    @exception_handler_decorator
    def script_process(script, metadata, use_db=True):
        """
        Executes each script in the stack.

        Parameters:
        - script (dict): A dictionary containing env_variables and stack scripts.
        - metadata (dict): Metadata required for logging and saving outcomes.
        - use_db (bool): Whether to use a database connection for logging and saving outcome data. Defaults to True.

        Returns:
        - list: A list of results containing the service name, endpoint, status code, and response.

        Raises:
        - ValidationError: If 'service', 'endpoint', or 'payload' in stack_scripts is invalid.
        """
        # Ensure env_variables and stack_scripts exist in the script dictionary
        if "env_variables" not in script or "stack_scripts" not in script:
            raise ValidationError("Missing 'env_variables' or 'stack_scripts' in the script data.")

        env_variables = script["env_variables"]
        stack_scripts = script["stack_scripts"]

        results = []

        # Execute each script in the stack
        for step_script in stack_scripts:
            service = step_script.get("service")
            endpoint = step_script.get("endpoint")
            payload = step_script.get("payload")
            payload["id_father_run"] = metadata.get("id_run")
            payload["id_father_service"] = service_data.get("id_service")

            # Validate the script details
            if not service or not endpoint or payload is None:
                raise ValidationError(f"Invalid script details in stack_scripts: {step_script}")

            try:
                # Get the host and port using the get_service_host_port function
                host_and_port = get_service_host_port(service)
                # Construct the full URL
                url = f"http://{host_and_port}{endpoint}"

                # Send the API request using the arq_handle_api_request method
                response = arq_handle_api_request(url, payload=payload, metadata=metadata, method='POST')

                # Collect the response data
                result_data = {
                    "service": service,
                    "endpoint": endpoint,
                    "status_code": 200,  # Assuming the request was successful
                    "response": response
                }

                results.append(result_data)

                # Log the successful execution
                log_to_api(metadata, log_message=f"Executed {endpoint} on {service} with status 200.", use_db=use_db)

                # Optionally, save outcome data
                arq_save_outcome_data(
                    metadata=metadata,
                    id_category=0,
                    id_type=1,
                    v_jsonb=result_data
                )

            except ValidationError as ve:
                # Handle validation errors for missing service/host/port
                error_message = f"Validation Error: {str(ve)}"
                log_to_api(metadata, log_message=error_message, error=True, use_db=use_db)
                results.append({
                    "service": service,
                    "endpoint": endpoint,
                    "error": error_message
                })

            except Exception as e:
                # In case of a request exception, capture the error
                error_message = f"Request to {url} failed: {str(e)}"
                log_to_api(metadata, log_message=error_message, error=True, use_db=use_db)
                results.append({
                    "service": service,
                    "endpoint": endpoint,
                    "error": error_message
                })
        return results



class FileManager:
    @staticmethod
    @exception_handler_decorator
    def is_valid_filename(filename):
        """
        Verifies that the filename is safe and does not contain dangerous characters.
        """
        return os.path.basename(filename) == filename and '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    @staticmethod
    @exception_handler_decorator
    def check_file_size(file_path):
        """
        Checks that the file does not exceed the allowed maximum size.
        """
        if os.path.getsize(file_path) > MAX_FILE_SIZE:
            raise ValueError(f"File {file_path} exceeds the maximum allowed size of {MAX_FILE_SIZE / (1024 * 1024)} MB.")

    @staticmethod
    @exception_handler_decorator
    def check_file_permissions(file_path):
        """
        Verifies that the file does not have insecure permissions like public write or execute.
        """
        st = os.stat(file_path)
        if st.st_mode & (stat.S_IWOTH | stat.S_IXOTH):  # Insecure permissions
            raise PermissionError(f"File {file_path} has insecure permissions.")

    @staticmethod
    @exception_handler_decorator
    def load_yaml_from_request():
        """
        Loads and processes the YAML file either from the provided X-Script-Name header (if specified) 
        or from the POST request body directly.

        Returns:
            dict: The YAML file contents as a dictionary.
        """
        # Check if the X-Script-Name header is present
        script_name = request.headers.get("X-Script-Name")
        
        if script_name:
            # Case 1: Load the script from the /scripts directory
            # Validate the filename is safe
            if not FileManager.is_valid_filename(script_name):
                raise ValueError(f"Invalid or dangerous file name: {script_name}")

            # Define the secure path inside the container where YAML files are stored
            file_path = os.path.join(".", "scripts", script_name)
            file_path = os.path.normpath(file_path)
            # Check if the file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File {script_name} not found.")

            # Check the file size
            FileManager.check_file_size(file_path)

            # Read and load the YAML file contents
            try:
                with open(file_path, 'r') as file:
                    original_yaml = file.read()
                    print("File contents:", original_yaml)  # Debugging statement
                    input_data = yaml.safe_load(original_yaml)
                    # Ensure input_data is a dictionary
                    if not isinstance(input_data, dict):
                        raise ValueError("Parsed YAML content is not a dictionary.")

                    # Store the original YAML string in input_data
                    input_data['original_yaml'] = original_yaml


            except yaml.YAMLError as e:
                raise ValueError(f"Error loading YAML file: {str(e)}")

            logging.info(f"File {script_name} loaded successfully by {request.remote_addr}")

        else:
            # Case 2: Load the YAML from the request body
            if not request.data:
                raise ValueError("No data found in request to load YAML content.")
            try:
                # Decode request data
                request_text = request.data.decode('utf-8')
                print("Request data:", request_text)  # Debugging statement
                input_data = yaml.safe_load(request_text)
            except yaml.YAMLError as e:
                raise ValueError(f"Error loading YAML from request body: {str(e)}")

            logging.info(f"YAML loaded successfully from request body by {request.remote_addr}")

        return input_data

    



@exception_handler_decorator
def get_service_host_port(service_name):
    """
    Returns the host:port for a given service.

    If the DEBUG environment variable is set to 'True', the function uses 'localhost' as the host.

    Args:
        service_name (str): The name of the service to search for (e.g., 'service_math').

    Returns:
        str: A string in the format 'host:port' if the service is found.

    Raises:
        ValidationError: If the service is not found or is missing required parameters.
    """
    # Check if debugging is enabled
    debug_mode = os.getenv('DEBUG', 'True').lower() == 'true'
    print(f"Debug mode: {debug_mode}")  # Debugging print

    # Assuming service_data is globally available
    print(f"Service name: {service_name}")
    print(f"Service data: {service_data}")

    # Parse service_arch if it's a string
    if isinstance(service_data['service_arch'], str):
        service_data['service_arch'] = json.loads(service_data['service_arch'])

    # Get the service architecture dictionary
    service_arch = service_data.get('service_arch', {})

    # Loop through the services to find the matching service name
    for service_key, service_info in service_arch.items():
        if service_key == service_name:
            # Debugging print to check service_info
            print(f"Service info retrieved: {service_info}")

            if 'host' in service_info and 'port' in service_info:
                host = 'localhost' if debug_mode else service_info['host']
                port = service_info['port']
                return f"{host}:{port}"
            else:
                # Missing 'host' or 'port' in the service info
                raise ValidationError(
                    message=f"Service '{service_name}' is missing 'host' or 'port' information.",
                    details=f"The service '{service_name}' does not contain valid 'host' and 'port' keys."
                )

    # If the service is not found, raise a ValidationError
    raise ValidationError(
        message=f"Service '{service_name}' not found.",
        details=f"The services stack does not contain the requested service: '{service_name}'."
    )