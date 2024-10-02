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
from Utilities_Main import compute_and_save, data_validation_metadata_generation,parse_request_data
from Utilities_Architecture import log_to_api, arq_save_outcome_data,ArqRuns,service_data
from Utilities_error_handling import format_error_response

logging.basicConfig(level=logging.DEBUG)  # Configures logging to display all debug messages

app = Flask(__name__)

@app.route("/arithmetic_operation", methods=["POST"])
def sum_and_save_route():
    """
    Handles the /sum_and_save API endpoint.

    This route parses the request data, validates metadata, and logs important information.
    It delegates the summation logic to the sum_and_save function and returns appropriate responses.
    
    Returns:
    - JSON: A response containing the result of the summation and metadata such as execution time.
      If an error occurs, an error message is returned.
    """
    
    script_start_time = time.time()
    route_name = 'arithmetic_operation'
    logging.debug(f'Starting {route_name} process.')
    id_script = 0  # Default id_script value
    id_run = None
    try:
        # Step 1: Parse the request data
        input_json = request.get_json()
        input_json.setdefault("id_script", id_script)  # Ensure id_script is set
        input_json["script_start_time"] = script_start_time

        
        # Step 2: Validate metadata
        metadata = data_validation_metadata_generation(input_json)
        id_run = metadata.get("id_run")
        use_db = metadata.get("use_db", True)

        # Step 3: Log the start of the operation
        log_to_api(metadata, log_message=f'{route_name} starts.', use_db=use_db)

        # Step 4: Perform the summation
        result_data = compute_and_save(input_json, metadata, use_db=use_db)

        # Step 5: Calculate execution time
        execution_time_ms = int((time.time() - script_start_time) * 1000)
        result_data["execution_time_ms"] = execution_time_ms

        # Step 6: Save execution time and metadata to the database if necessary
        if use_db and id_run:
            arq_save_outcome_data(
                metadata=metadata,
                id_category=0,
                id_type=1,
                v_integer=execution_time_ms
            )

        # Step 7: Log the completion and execution time
        log_to_api(metadata, log_message=f"total execution_time_ms={execution_time_ms}", use_db=use_db)
        log_to_api(metadata, log_message=f"{route_name} ends.", use_db=use_db)

        # Step 8: Update run fields and return the result
        success_status = 200
        ArqRuns.update_run_fields(metadata, status=success_status)
        return jsonify(result_data), success_status

    except Exception as e:
        error_response, status_code = format_error_response(
            service_name=service_data['service_name'],
            route_name=route_name,
            exception=e,
            id_run=id_run
        )
        if id_run is not None:
            ArqRuns.update_run_fields(metadata, status=status_code,milestone_msg=error_response)
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
