"""
Flask API for Customer Service Application

Main Features:

Routes:
- GET /: Summary of routes.
- POST /sum_and_save: Computes the sum of two numbers and saves the arguments and result.

Dependencies:
- Flask: Web framework for building the API.
- Waitress: Production-quality pure-Python WSGI server.

Usage:

Environment Variables:
- PORT: Specifies the port on which the application will listen.

Examples:
  POST http://localhost:PORT/sum_and_save

Author: Agustín Corigliano
Version: 1.1.0
Date: 24/09/03

Notes:
- Updated to include user_id and father_service_id parameters in the run creation process.
"""

import time
import os
import logging
from flask import Flask, request, jsonify, render_template
from waitress import serve
from Utilities_Main import SumAndSave, data_validation_metadata_generation,parse_request_data
from Utilities_Architecture import log_to_api, save_outcome_data,service_data
from Utilities_error_handling import log_and_raise, format_error_response, ValidationError, HTTPError, APIError

logging.basicConfig(level=logging.DEBUG)  # Configures logging to display all debug messages

app = Flask(__name__)

@app.route("/sum_and_save", methods=["POST"])
def sum_and_save_route():
    """
    Handles the /sum_and_save API endpoint.

    This route computes the sum of two numbers provided in the request, 
    and optionally logs the operation and its metadata to a database. 
    The function supports user authentication and allows the operation 
    to be part of a larger workflow identified by metadata.

    The route accepts the following JSON payload:
    - arg1 (int or float): The first operand for the summation. (Required)
    - arg2 (int or float): The second operand for the summation. (Required)
    - id_father_run (int, optional): Identifier for the parent run, if part of a larger process.
    - id_father_service (int, optional): Identifier for the parent service, required if `id_father_run` is provided.
    - user (str): Username for authentication. (Required)
    - password (str): Password for authentication. (Required)
    - use_db (bool, optional): Flag to indicate whether to log the operation and its metadata to the database. Defaults to True.

    Returns:
    - JSON: A response containing the result of the summation and, if applicable, 
      metadata such as execution time. If an error occurs, an error message is returned.
    """
    route_name = 'sum_and_save'
    logging.debug(f'Starting {route_name} process.')
    start_time = time.time()
    id_run = None  # Initialize id_run for error handling

    try:
        # Parse the request data using parse_request_data()
        data = parse_request_data()

        # Set default id_script if not provided
        data.setdefault("id_script", 0)

        args = {
        "arg1": data.get("arg1"),
        "arg2": data.get("arg2")
        }

        # Check for required parameters
        if args["arg1"] is None or args["arg2"] is None:
            log_and_raise(
                ValidationError,
                "arg1 and arg2 are required parameters",
                id_run=id_run,
                context=route_name
            )

        # Extract and validate metadata using data_validation_metadata_generation
        metadata = data_validation_metadata_generation(data)
        id_run = metadata.get("id_run")
        use_db = metadata.get("use_db", True)

        # Log and save input arguments if necessary
        input_arguments = {"arg1": arg1, "arg2": arg2, **metadata}
        log_to_api(metadata, log_message=f'{route_name} starts.', use_db=use_db)

        if use_db and id_run:
            save_outcome_data(id_run, 0, 0, v_jsonb=input_arguments)
            log_to_api(metadata, log_message="Outcome data saved successfully.", use_db=use_db)

        # Perform the summation and return the result
        result_value = arg1 + arg2
        result = {
            "result": result_value,
            "id_run": id_run
        }

        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)
        result["execution_time_ms"] = execution_time_ms

        if use_db and id_run:
            save_outcome_data(id_run, 0, 1, v_integer=execution_time_ms)

        log_to_api(metadata, log_message=f"execution_time_ms={execution_time_ms}", use_db=use_db)
        log_to_api(metadata, log_message="sum_and_save ends.", use_db=use_db)

        return jsonify(result), 200

    except Exception as e:
        error_response, status_code = format_error_response(
            service_name=service_data.get('service_name', 'Service_sum'),
            route_name=route_name,
            exception=e,
            id_run=id_run
        )
        return jsonify(error_response), status_code



@app.route("/")
def summary():
    """
    Main root route, gives a summary of all routes.
    """
    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10033))  # Use port from environment variable or default to 10033
    serve(app, host="0.0.0.0", port=port)
