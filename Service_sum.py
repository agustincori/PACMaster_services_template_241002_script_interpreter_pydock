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
from Utilities_Main import SumAndSave, data_validation_metadata_generation
from Utilities_Architecture import log_to_api, save_outcome_data
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
    start_time = time.time()
    id_run = None
    id_script = 0 
    try:
        # Extract and validate request arguments from JSON payload
        data = request.json
        data["id_script"] = id_script        
        arg1 = data.get("arg1")
        arg2 = data.get("arg2")

        # Check for required parameters
        if arg1 is None or arg2 is None:
            log_and_raise(ValidationError, "arg1 and arg2 are required parameters", id_run=None)

        # Extract and validate metadata
        metadata = data_validation_metadata_generation(data)
        id_run = metadata["id_run"]
        use_db = metadata["use_db"]

        # Log and save input arguments if necessary
        input_arguments = {"arg1": arg1, "arg2": arg2, **metadata}
        log_to_api(metadata, log_message="sum_and_save starts.-", debug=False, warning=False, error=False, use_db=use_db)
        
        if use_db and id_run:
            save_outcome_data(id_run, 0, 0, v_jsonb=input_arguments)
            log_to_api(metadata, log_message="Outcome data saved successfully.", debug=False, warning=False, error=False, use_db=use_db)

        # Perform the summation and return the result
        result = SumAndSave(arg1, arg2, id_run, use_db)

        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)
        result["execution_time_ms"] = execution_time_ms

        if use_db and id_run:
            save_outcome_data(id_run, 0, 1, v_integer=execution_time_ms)

        log_to_api(metadata, log_message=f"execution_time_ms={execution_time_ms}", debug=False, warning=False, error=False, use_db=use_db)
        log_to_api(metadata, log_message="sum_and_save ends.-", debug=False, warning=False, error=False, use_db=use_db)

        return jsonify(result), 200

    except ValidationError as e:
        return jsonify(format_error_response("Service_sum", str(e), id_run)), 400  # 400 Bad Request
    except APIError as e:
        return jsonify(format_error_response("Service_sum", str(e), id_run)), 500  # 500 Internal Server Error
    except ConnectionError as e:
        return jsonify(format_error_response("Service_sum", str(e), id_run)), 503  # 503 Service Unavailable
    except HTTPError as e:
        return jsonify(format_error_response("Service_sum", str(e), id_run)), 502  # 502 Bad Gateway
    except Exception as e:
        return jsonify(format_error_response("Service_sum", f"Unexpected error: {str(e)}", id_run)), 500  # 500 Internal Server Error



@app.route("/")
def summary():
    """
    Main root route, gives a summary of all routes.
    """
    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10033))  # Use port from environment variable or default to 10033
    serve(app, host="0.0.0.0", port=port)
