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
from Utilities_Main import sum_and_save, data_validation_metadata_generation,parse_request_data
from Utilities_Architecture import log_to_api, arq_save_outcome_data,arq_update_run_fields,service_data
from Utilities_error_handling import log_and_raise, format_error_response, ValidationError, HTTPError, APIError

logging.basicConfig(level=logging.DEBUG)  # Configures logging to display all debug messages

app = Flask(__name__)

@app.route("/sum_and_save", methods=["POST"])
def sum_and_save_route():
    """
    Handles the /sum_and_save API endpoint.

    This route parses the request data, validates metadata, and delegates the
    summation logic to the sum_and_save function in Utilities_Main. It also
    handles exceptions and returns appropriate responses.

    Returns:
    - JSON: A response containing the result of the summation and, if applicable,
      metadata such as execution time. If an error occurs, an error message is returned.
    """
    
    
    script_start_time = time.time()
    route_name = 'sum_and_save_route'
    logging.debug(f'Starting {route_name} process.')
    id_run = None  # Initialize id_run for error handling
    id_script=1
    try:
        # Parse the request data using parse_request_data()
        input_json = parse_request_data()

        # Set default id_script if not provided
        input_json.setdefault("id_script", id_script)
        input_json.setdefault("script_start_time", script_start_time)
        # Extract arguments
        data = {
            "arg1": input_json.get("arg1"),
            "arg2": input_json.get("arg2")
        }

        # Extract and validate metadata using data_validation_metadata_generation
        metadata = data_validation_metadata_generation(input_json)
        id_run = metadata.get("id_run")
        use_db = metadata.get("use_db", True)
        if use_db and id_run:
            arq_save_outcome_data(metadata=metadata,id_category=1,id_type=0,v_string="data_validation_metadata_generation executed succesfully",v_integer=execution_time_ms)
        # Log the start of the operation
        log_to_api(metadata, log_message=f'{route_name} starts.', use_db=use_db)

        # Perform the summation by calling the sum_and_save function
        result_data = sum_and_save(data, metadata, use_db=use_db)

        # Calculate execution time
        execution_time_ms = int((time.time() - script_start_time) * 1000)
        result_data["execution_time_ms"] = execution_time_ms

        # Save execution time if using the database
        if use_db and id_run:
            arq_save_outcome_data(
                metadata=metadata,
                id_category=0,
                id_type=1,
                v_integer=execution_time_ms
            )

        # Log the execution time and end of the operation
        log_to_api(metadata, log_message=f"total execution_time_ms={execution_time_ms}", use_db=use_db)
        log_to_api(metadata, log_message=f"{route_name} ends.", use_db=use_db)

        succes_status=200
        arq_update_run_fields(metadata, status=succes_status)
        return jsonify(result_data), succes_status

    except Exception as e:
        error_response, status_code = format_error_response(
            service_name=service_data.get('service_name'),
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
