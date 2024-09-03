"""
Flask API for Customer Service Application

Main Features:

Routes:
- GET /: Summary of routes.
- GET /sum_and_save: Computes the sum of two numbers and saves the arguments and result.

Dependencies:
- Flask: Web framework for building the API.
- Waitress: Production-quality pure-Python WSGI server.

Usage:

Environment Variables:
- PORT: Specifies the port on which the application will listen.

Examples:
  GET http://localhost:PORT/
  GET http://localhost:PORT/sum_and_save?arg1=10&arg2=20&user_id=1&use_db=true

Author: Agustín Corigliano
Version: 1.0.1
Date: 25/06/24

Notes:
- Updated to include user_id and father_service_id parameters in the run creation process.
"""

# coding: utf-8
import time
import requests
import os
import logging
from waitress import serve
from flask import (
    Flask,
    request,
    jsonify,
    render_template,
)
from Utilities_Main import SumAndSave
from Utilities_Architecture import log_to_api, get_new_runid, save_outcome_data
logging.basicConfig(
    level=logging.DEBUG
)  # Configures logging to display all debug messages

app = Flask(__name__)

@app.route("/sum_and_save", methods=["POST"])
def sum_and_save_route():
    """
    Route to compute the sum of two numbers and save the arguments and the result.

    Parameters:
    - arg1 (int or float): The first number.
    - arg2 (int or float): The second number.
    - id_father_run (int, optional): The identifier of the parent run, if this action is part of a larger process. Defaults to None.
    - id_father_service (int, optional): The identifier of the father service. Required if FatherRunID is provided.
    - user (str): The username for identification.
    - pswrd (str): The password for identification.
    - use_db (bool, optional): Whether to use database connection for logging and saving outcome data. Defaults to True.

    Returns:
    - JSON response containing the arguments and the result of the summation.
    """
    id_script = 1  # Script ID for logging
    start_time = time.time()  # Record start time
    try:
        # Extract and validate request arguments from JSON payload
        data = request.json  # Parse JSON payload
        arg1 = data.get("arg1", None)  # First number
        arg2 = data.get("arg2", None)  # Second number
        id_father_run = data.get("id_father_run", None)  # Optional parent run ID
        id_father_service = data.get("id_father_service", None)  # Optional father service ID
        user = data.get("user", None)  # Username for identification
        pswrd = data.get("password", None)  # Password for identification
        use_db = data.get("use_db", True)  # Whether to use the database

        # Check for required parameters
        if arg1 is None or arg2 is None:
            return jsonify({"error": "arg1 and arg2 are required parameters"}), 400  # Ensure both numbers are provided

        # Call user_identify to get id_user
        id_user = user_identify(user, pswrd)  # Identify the user

        if id_user is None:
            return jsonify({"error": "Invalid credentials"}), 401  # Return error if credentials are invalid

        # Create new run ID if use_db is True
        new_run_id = None  # Initialize new_run_id
        if use_db:
            new_run_id_response = get_new_runid(id_script, id_user, id_father_service, id_father_run=id_father_run)  # Get new run ID

            if 'error' in new_run_id_response:
                error_message = new_run_id_response.get('error', 'Unknown error occurred while creating new run ID.')  # Extract error message
                error_details = new_run_id_response.get('details', 'No additional details provided.')  # Extract error details
                log_to_api(id_run=None, log_message=f"Error creating new run ID: {error_message}. Details: {error_details}", debug=True, error=True)  # Log error
                return jsonify(new_run_id_response), 500  # Return error response

            new_run_id = new_run_id_response.get('id_run')  # Get new run ID from response

        # Prepare input arguments and log/save if necessary
        input_arguments = {
            "arg1": arg1,
            "arg2": arg2,
            "id_father_run": id_father_run,
            "id_father_service": id_father_service,
            "user": user,
            "use_db": use_db
        }  # Input arguments dictionary
        log_to_api(id_run=new_run_id, log_message="sum_and_save starts.-", debug=False, warning=False, error=False, use_db=use_db)  # Log start of process
        if use_db and new_run_id:
            save_outcome_data(new_run_id, 0, 0, v_jsonb=input_arguments)  # Save input arguments to database
            log_to_api(id_run=new_run_id, log_message="Outcome data saved successfully.", debug=False, warning=False, error=False, use_db=use_db)  # Log successful save

        # Perform the summation and return the result
        result = SumAndSave(arg1, arg2, new_run_id, use_db)  # Calculate sum and save if necessary

        end_time = time.time()  # Record end time
        execution_time_ms = int((end_time - start_time) * 1000)  # Calculate execution time in milliseconds
        result["execution_time_ms"] = execution_time_ms  # Add execution time to the result
        if use_db and new_run_id:
            save_outcome_data(new_run_id, 0, 1, v_integer=execution_time_ms)  # Save execution time to database
        log_to_api(id_run=new_run_id, log_message=f"execution_time_ms={execution_time_ms}", debug=False, warning=False, error=False, use_db=use_db)  # Log execution time

        log_to_api(id_run=new_run_id, log_message="sum_and_save ends.-", debug=False, warning=False, error=False, use_db=use_db)  # Log end of process
        return jsonify(result), 200  # Return the result with a 200 OK status
    except Exception as e:
        log_to_api(id_run=new_run_id, log_message=f"Exception occurred: {str(e)}", debug=False, warning=False, error=True, use_db=use_db)  # Log exception
        return jsonify({"error": str(e)}), 500  # Return error response with a 500 Internal Server Error status


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



@app.route("/")
def summary():
    """
    Main root route, gives a summary of all routes.

    Parameters:

    Raises:

    Returns:
    - A summary of all routes and their arguments.
    """
    return render_template("index.html")


if __name__ == "__main__":
    port = int(
        os.environ.get("PORT", 10033)
    )  # Use port from environment variable or default to 10032
    serve(app, host="0.0.0.0", port=port)
