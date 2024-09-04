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
Version: 1.1.0
Date: 24/09/03

Notes:
- Updated to include user_id and father_service_id parameters in the run creation process.
"""

# coding: utf-8
import time
import os
import logging
from waitress import serve
from flask import (
    Flask,
    request,
    jsonify,
    render_template,
)
from Utilities_Main import SumAndSave,extract_and_validate_metadata
from Utilities_Architecture import log_to_api, get_new_runid, save_outcome_data
logging.basicConfig(
    level=logging.DEBUG
)  # Configures logging to display all debug messages

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
    - pswrd (str): Password for authentication. (Required)
    - use_db (bool, optional): Flag to indicate whether to log the operation and its metadata to the database. Defaults to True.

    Returns:
    - JSON: A response containing the result of the summation and, if applicable, 
      metadata such as execution time. If an error occurs, an error message is returned.
    - HTTP Status Codes:
        - 200 OK: The operation was successful, and the result is returned.
        - 400 Bad Request: Required parameters are missing or invalid.
        - 401 Unauthorized: Invalid user credentials.
        - 500 Internal Server Error: An unexpected error occurred during processing.
    """
    start_time = time.time()

    try:
        # Extract and validate request arguments from JSON payload
        data = request.json
        arg1 = data.get("arg1")
        arg2 = data.get("arg2")

        # Check for required parameters
        if arg1 is None or arg2 is None:
            return jsonify({"error": "arg1 and arg2 are required parameters"}), 400

        # Extract and validate metadata
        metadata, error_response = extract_and_validate_metadata(data)
        if error_response:
            return jsonify(error_response), error_response["status"]

        new_run_id = metadata["new_run_id"]
        use_db = metadata["use_db"]

        # Log and save input arguments if necessary
        input_arguments = {"arg1": arg1, "arg2": arg2, **metadata}
        log_to_api(id_run=new_run_id, log_message="sum_and_save starts.-", debug=False, warning=False, error=False, use_db=use_db)
        
        if use_db and new_run_id:
            save_outcome_data(new_run_id, 0, 0, v_jsonb=input_arguments)
            log_to_api(id_run=new_run_id, log_message="Outcome data saved successfully.", debug=False, warning=False, error=False, use_db=use_db)

        # Perform the summation and return the result
        result = SumAndSave(arg1, arg2, new_run_id, use_db)

        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)
        result["execution_time_ms"] = execution_time_ms

        if use_db and new_run_id:
            save_outcome_data(new_run_id, 0, 1, v_integer=execution_time_ms)

        log_to_api(id_run=new_run_id, log_message=f"execution_time_ms={execution_time_ms}", debug=False, warning=False, error=False, use_db=use_db)
        log_to_api(id_run=new_run_id, log_message="sum_and_save ends.-", debug=False, warning=False, error=False, use_db=use_db)

        return jsonify(result), 200

    except Exception as e:
        log_to_api(id_run=None, log_message=f"Exception occurred: {str(e)}", debug=False, warning=False, error=True, use_db=use_db)
        return jsonify({"error": str(e)}), 500





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
