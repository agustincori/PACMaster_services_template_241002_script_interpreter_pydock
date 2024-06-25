"""
Flask API for Customer Service Application

Main Features:

Routes:
- GET /: Summary of routes.

Dependencies:
- Flask: Web framework for building the API.
- Waitress: Production-quality pure-Python WSGI server.

Usage:

Environment Variables:
- PORT: Specifies the port on which the application will listen.

Examples:
  GET http://localhost:PORT/

Author: Agustín Corigliano
Version: 1.0.1
Date: 24/06/19

Notes:
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
    - use_db (bool, optional): Whether to use database connection for logging and saving outcome data. Defaults to True.

    Returns:
    - JSON response containing the arguments and the result of the summation.
    """
    try:
        arg1 = request.args.get("arg1", type=float)
        arg2 = request.args.get("arg2", type=float)
        FatherRunID = request.args.get("FatherRunID", type=int, default=None)
        use_db = request.args.get("use_db", type=lambda v: v.lower() == 'true', default=True)
        
        if arg1 is None or arg2 is None:
            return jsonify({"error": "arg1 and arg2 are required parameters"}), 400

        result = SumAndSave(arg1, arg2, FatherRunID, use_db)
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
