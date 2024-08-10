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
import json
import os
import logging
import re
from waitress import serve
from flask import (
    Flask,
    request,
    jsonify,
    make_response,
    render_template,
    send_file,
    Response,
)
from Utilities_Main import SumAndSave
from Utilities_Architecture import log_to_api, get_new_runid, save_outcome_data
logging.basicConfig(
    level=logging.DEBUG
)  # Configures logging to display all debug messages

app = Flask(__name__)

@app.route("/sum_and_save", methods=["GET"])
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
    id_script = 1
    start_time = time.time()  # Record start time
    try:
        # Extract and validate request arguments
        arg1 = request.args.get("arg1", type=float)
        arg2 = request.args.get("arg2", type=float)
        id_father_run = request.args.get("id_father_run", type=int, default=None)
        id_father_service = request.args.get("id_father_service", type=int, default=None)
        user = request.args.get("user")
        pswrd = request.args.get("pswrd")
        use_db = request.args.get("use_db", type=lambda v: v.lower() == 'true', default=True)
        # Check for required parameters
        if arg1 is None or arg2 is None:
            return jsonify({"error": "arg1 and arg2 are required parameters"}), 400

        # Call user_identify to get id_user (placeholder for now)
        id_user_response = user_identify(user, pswrd)

        if id_user_response == 0:
            id_user = 0  # Placeholder for now
        else:
            return jsonify({"error": "Invalid credentials"}), 401

        # Create new run ID if use_db is True
        new_run_id = None
        if use_db:
            new_run_id_response = get_new_runid(id_script, id_user, id_father_service, id_father_run=id_father_run)

            if 'error' in new_run_id_response:
                error_message = new_run_id_response.get('error', 'Unknown error occurred while creating new run ID.')
                error_details = new_run_id_response.get('details', 'No additional details provided.')
                log_to_api(id_run=None, log_message=f"Error creating new run ID: {error_message}. Details: {error_details}", debug=True, error=True)
                return jsonify(new_run_id_response), 500

            new_run_id = new_run_id_response.get('id_run')

        # Prepare input arguments and log/save if necessary
        input_arguments = {
            "arg1": arg1,
            "arg2": arg2,
            "id_father_run": id_father_run,
            "id_father_service": id_father_service,
            "user": user,
            "use_db": use_db
        }
        log_to_api(id_run=new_run_id, log_message="sum_and_save starts.-", debug=False, warning=False, error=False, use_db=use_db)
        if use_db and new_run_id:
            save_outcome_data(new_run_id, 0, 0, v_jsonb=input_arguments)
            log_to_api(id_run=new_run_id, log_message="Outcome data saved successfully.", debug=False, warning=False, error=False, use_db=use_db)

        # Perform the summation and return the result
        result = SumAndSave(arg1, arg2, new_run_id, use_db)

        end_time = time.time()  # Record end time
        execution_time_ms = int((end_time - start_time) * 1000)  # Calculate execution time in milliseconds and convert to integer
        result["execution_time_ms"] = execution_time_ms  # Add execution time in milliseconds to the result
        if use_db and new_run_id:
            save_outcome_data(new_run_id, 0, 1, v_integer=execution_time_ms)
        log_to_api(id_run=new_run_id, log_message=f"execution_time_ms={execution_time_ms}", debug=False, warning=False, error=False, use_db=use_db)

        log_to_api(id_run=new_run_id, log_message="sum_and_save ends.-", debug=False, warning=False, error=False, use_db=use_db)
        log_to_api(id_run=new_run_id, log_message="", debug=False, warning=False, error=False, use_db=use_db)
        return jsonify(result), 200
    except Exception as e:
        log_to_api(id_run=new_run_id, log_message=f"Exception occurred: {str(e)}", debug=False, warning=False, error=True, use_db=use_db)
        return jsonify({"error": str(e)}), 500


def user_identify(user, pswrd):
    """
    Placeholder method to identify the user based on username and password.

    Returns:
    - int: User ID (placeholder value, currently returns 0).
    """
    # Placeholder authentication logic (return 0 for any credentials)
    return 0



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
        os.environ.get("PORT", 10032)
    )  # Use port from environment variable or default to 10032
    serve(app, host="0.0.0.0", port=port)
