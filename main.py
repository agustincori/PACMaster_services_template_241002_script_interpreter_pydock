"""
Flask API for Customer Service Application

Main Features:

Routes:
- GET /: Summary of routes.
- GET /sum_and_save: Computes the sum of two numbers and saves the arguments and result.
- POST /create_new_run: Creates a new run entry in the database.

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
Version: 1.0.0
Date: 25/06/24

Notes:
- Updated to include user_id and father_service_id parameters in the run creation process.
"""

# coding: utf-8
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
    - FatherRunID (int, optional): The identifier of the parent run, if this action is part of a larger process. Defaults to None.
    - father_service_id (int, optional): The identifier of the father service. Required if FatherRunID is provided.
    - user_id (int): The identifier of the user. Required if use_db is True.
    - use_db (bool, optional): Whether to use database connection for logging and saving outcome data. Defaults to True.

    Returns:
    - JSON response containing the arguments and the result of the summation.
    """
    id_script = 1
    try:
        # Extract and validate request arguments
        arg1 = request.args.get("arg1", type=float)
        arg2 = request.args.get("arg2", type=float)
        FatherRunID = request.args.get("FatherRunID", type=int, default=None)
        father_service_id = request.args.get("father_service_id", type=int, default=None)
        user_id = request.args.get("user_id", type=int)
        use_db = request.args.get("use_db", type=lambda v: v.lower() == 'true', default=True)

        # Check for required parameters
        if arg1 is None or arg2 is None:
            return jsonify({"error": "arg1 and arg2 are required parameters"}), 400

        # Create new run ID if use_db is True
        new_run_id = None
        if use_db:
            new_run_id_response = get_new_runid(id_script, user_id, father_service_id, FatherRunid=FatherRunID)

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
            "FatherRunID": FatherRunID,
            "father_service_id": father_service_id,
            "user_id": user_id,
            "use_db": use_db
        }

        if use_db and new_run_id:
            save_outcome_data(new_run_id, 0, 0, v_jsonb=input_arguments)
            log_to_api(id_run=new_run_id, log_message="Outcome data saved successfully.", debug=False, warning=False, error=False, use_db=use_db)

        # Perform the summation and return the result
        result = SumAndSave(arg1, arg2, new_run_id, use_db)
        return jsonify(result), 200
    except Exception as e:
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
        os.environ.get("PORT", 10032)
    )  # Use port from environment variable or default to 10032
    serve(app, host="0.0.0.0", port=port)
