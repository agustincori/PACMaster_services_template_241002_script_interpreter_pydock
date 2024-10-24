"""
Flask API for Script Interpreter Service

Main Features:

Routes:
- GET /: Summary of routes.
- POST /execute_script_stack: Executes a stack of scripts based on the provided payload.

Dependencies:
- Flask: Web framework for building the API.
- Waitress: Production-quality pure-Python WSGI server.

Usage:

Environment Variables:
- PORT: Specifies the port on which the application will listen.

Examples:
  POST http://localhost:PORT/execute_script_stack

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
from flask_cors import CORS
import requests
from Utilities_Main import (
    data_validation_metadata_generation,
    parse_request_data,
    ScriptManagement,
    FileManager
)
from Utilities_Architecture import (
    log_to_api,
    arq_save_outcome_data,
    ArqRuns,
    service_data,
)
from Utilities_error_handling import format_error_response, ValidationError

logging.basicConfig(level=logging.DEBUG)  # Configures logging to display all debug messages

app = Flask(__name__)
CORS(app, expose_headers=["token_access"])  # Allow custom 'token-access' header

@app.route("/execute_script_stack", methods=["POST"])
def execute_script_stack():
    """
    Route to execute a stack of scripts based on a JSON or YAML payload.

    Payload Structure:
        env_variables:
            reused_var=abc
        stack_scripts:
        - service: "instrument_service"
            endpoint: "/script1"
            payload: {...}
        - service: "device_service"
            endpoint: "/script2"
            payload: {...}
        - service: "instrument_service"
            endpoint: "/script3"
            payload: {...}

    Returns:
    - JSON response containing the results of each script call.
    """
    script_start_time = time.time()
    
    route_name = 'execute_script_stack'
    logging.debug(f'Starting {route_name} process.')
    id_script = 0  # Default id_script value
    id_run = None
    try:
        # Step 1: Parse the request data (supports JSON and YAML)
        input_data = FileManager.load_yaml_from_request()
        input_data.setdefault("id_script", id_script)  # Ensure id_script is set
        input_data["script_start_time"] = script_start_time

        # Step 2: Validate metadata
        metadata = data_validation_metadata_generation(input_data)
        id_run = metadata.get("id_run")
        use_db = metadata.get("use_db", True)

        # Step 3: Log the start of the operation
        log_to_api(metadata, log_message=f'{route_name} starts.', use_db=use_db)

        # Step 4: Extract common_data and stack_scripts
        script = ScriptManagement.extract_script_data(input_data,metadata)
        
        # Step 5: Process the scripts using the script_process method
        results = ScriptManagement.script_process(script,metadata)

        # Step 6: Calculate execution time
        execution_time_ms = int((time.time() - script_start_time) * 1000)
        result_output = {
            "results": results,
            "execution_time_ms": execution_time_ms
        }

        # Step 7: Save execution time and metadata to the database if necessary
        if use_db and id_run:
            arq_save_outcome_data(
                metadata=metadata,
                id_category=1,
                id_type=1,
                v_integer=execution_time_ms
            )

        # Step 8: Log the completion and execution time
        log_to_api(metadata, log_message=f"Total execution_time_ms={execution_time_ms}", use_db=use_db)
        log_to_api(metadata, log_message=f"{route_name} ends.", use_db=use_db)

        if use_db and id_run:
            arq_save_outcome_data(
                metadata=metadata,
                id_category=0,
                id_type=12,
                v_jsonb=results
            )
        # Step 9: Update run fields and return the result
        success_status = 200
        ArqRuns.update_run_fields(metadata, status=success_status)
        return jsonify(result_output), success_status

    except Exception as e:
        error_response, status_code = format_error_response(
            service_name=service_data['service_name'],
            route_name=route_name,
            exception=e,
            id_run=id_run
        )
        if id_run is not None:
            ArqRuns.update_run_fields(metadata, status=status_code, milestone_msg=error_response)
        return jsonify(error_response), status_code

@app.route("/")
def summary():
    """
    Main root route, gives a summary of all routes.
    """
    return render_template("index.html")

if __name__ == "__main__":
    #port = int(os.environ.get("PORT", 10034))  # Use port from environment variable or default to 10033
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10034)), debug=True)  # Use this for local development only

