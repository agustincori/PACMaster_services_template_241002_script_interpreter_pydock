"""
PACMasterDB API

This Flask application provides an API for managing logs, outcomes, and types related to PACMaster.

Logs:
- POST /insert_log: Inserts a new log entry. Args: id_run (int), log (string), debug (bool, optional). Returns: Confirmation message (201).
- GET /get_log_from_idrun/<int:id_run>: Retrieves logs for a specific run ID. Args: id_run (int). Returns: Array of logs (200) or error message (404).

Outcomes:
- POST /insert_outcome_run: Inserts a new outcome entry. Args: id_run, id_category, id_type (ints), v_integer (int, optional), v_floatpoint (float, optional), v_string (string, optional), v_timestamp (datetime, optional). Returns: Confirmation message (201).
- GET /get_outcome_by_category_type/<int:id_run>/<int:id_category>/<int:id_type>: Retrieves outcomes for specific run ID and category/type. Args: id_run, id_category, id_type (ints). Returns: Array of outcomes (200) or error message (404).
- GET /getOutcome: Retrieves outcomes based on various filters. Args: idRun, idCategory, idType, v_integer, v_floatpoint, v_string, v_timestamp. Returns: Array of outcomes (200) or error message (404).

Runs:
- POST /create_new_run: Creates a new run entry. Args: id_script (int), id_run_father (int, optional). Returns: New run ID (201) or error message (500).
- GET /get_all_runs: Retrieves all run IDs, their script IDs, father run IDs, and their timestamps. No args. Returns: Array of runs (200) or error message (404).
- GET /get_father_runs: Retrieves all runs that are 'father' runs. No args. Returns: Array of father runs (200) or error message (404).
- GET /get_runid_childs/<int:father_runid>: Retrieves all child run IDs for a given 'father' run ID. Args: father_runid (int). Returns: Array of child run IDs (200) or empty array (200).

Data Run Types:
- GET /get_data_run_types: Retrieves data run types based on filters. Args: id_category, id_type, category_name, type_name. Returns: Array of data run types (200) or error message (404).

Miscellaneous:
- GET /: Simple rpoute to check if the Flask app is running. No args. Returns: Confirmation message.
- GET /test_db_connection: Test DB Connection

Environment:
- Running on Docker (if applicable): {running_in_docker}
- Database Host: {db_host}
- Port: {port} (default 5431, can be set via FLASK_RUN_PORT environment variable)
- Debug Mode: {debug} (enabled if FLASK_DEBUG environment variable is set to 'true')

Author:Agustín Corigliano
Version:1.2

Note: Replace placeholder values in curly braces with actual runtime values as applicable.

"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import Error
import os
from datetime import datetime
import logging
from traceback import format_exc
import json  # Import json module

# Setup basic logging
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)
CORS(app)


# Determine if running in a Docker container
running_in_docker = os.environ.get('RUNNING_IN_DOCKER', 'false').lower() == 'true'

# Set the database host dynamically
db_host = os.environ.get('DB_HOST', 'localhost')

# Database connection parameters
DB_PARAMS = {
    'dbname': os.getenv('DB_NAME','postgres'),
    'user': os.getenv('DB_USER','postgres'),
    'password': os.getenv('DB_PASSWORD','xxx'),
    'host': os.getenv('DB_HOST',db_host),
    'port': os.getenv('DB_PORT', 5432)
}

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_PARAMS, cursor_factory=RealDictCursor)
        return conn
    except psycopg2.OperationalError as e:
        error_message = {
            "error": "Database connection failed",
            "details": str(e)
        }
        logging.error(f'Database connection error: {e}')
        return jsonify(error_message), 500
    except Exception as e:
        error_message = {
            "error": "An unexpected error occurred",
            "details": str(e)
        }
        logging.error(f'Unexpected error: {e}')
        return jsonify(error_message), 500

@app.route('/test_db_connection', methods=['GET'])
def test_db_connection():
    conn_response = get_db_connection()
    if isinstance(conn_response, tuple):
        return conn_response
    conn = conn_response
    cur = conn.cursor()

    try:
        cur.execute("SELECT 1")
        return jsonify({'message': 'Database connection successful'}), 200
    except Exception as e:
        logging.error(f'Database test query error: {e}')
        return jsonify({'message': 'Database test query failed', 'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

##################################################
##################################################
######            LOGS                ############
##################################################
##################################################


@app.route('/insert_log', methods=['POST'])
def insert_log():
    data = request.json

    # Validate required fields
    if 'id_run' not in data or 'log' not in data:
        return jsonify({'message': 'Missing required fields'}), 400

    # Ensure that 'debug', 'warning', and 'error' are provided in the JSON, defaulting to False if not provided
    debug_value = data.get('debug', False)
    warning_value = data.get('warning', False)
    error_value = data.get('error', False)

    try:
        
        conn_response = get_db_connection() # Attempt to get a database connection
        if isinstance(conn_response, tuple): # Check if a tuple was returned, indicating an error
            return conn_response  # Return the JSON error response and status code
        conn = conn_response
        cur = conn.cursor()

        # Include the 'debug', 'warning', and 'error' columns in the INSERT statement
        cur.execute(
            """
            INSERT INTO "logs_table" 
            (id_run, log, debug, warning, error) 
            VALUES (%s, %s, %s, %s, %s)
            """,
            (data['id_run'], data['log'], debug_value, warning_value, error_value)
        )

        conn.commit()
        return jsonify({'message': 'Log inserted successfully'}), 201
    except Exception as e:  # It's better to catch more specific exceptions
        logging.error(f'Database error: {e}')
        return jsonify({'message': 'Database error', 'error': str(e)}), 500
    finally:
        # Ensure resources are cleaned up regardless of success or failure
        if conn is not None:
            conn.close()


@app.route('/get_log_from_idrun/<int:id_run>', methods=['GET'])
def get_log_from_idrun(id_run):
    """
    Retrieves logs associated with a specific run ID and sorts them by the timestamp of the log entry.
    
    Parameters:
        id_run (int): The unique identifier for the run.
        
    Returns:
        A JSON response containing an array of logs sorted by timestamp, or an error message if no logs are found or a database error occurs.
    """
    logging.debug(f'Starting get_log_from_idrun process for id_run: {id_run}')
    conn_response = get_db_connection() # Attempt to get a database connection
    if isinstance(conn_response, tuple): # Check if a tuple was returned, indicating an error
        return conn_response  # Return the JSON error response and status code
    conn = conn_response
    cur = conn.cursor()

    try:
        # Fetch logs for the given id_run and sort them by log_timestamp
        cur.execute("""
            SELECT log, debug, warning, error, log_timestamp 
            FROM "logs_table" 
            WHERE id_run = %s 
            ORDER BY log_timestamp ASC
            """, (id_run,))
        logs = cur.fetchall()
        
        if logs:
            logging.debug(f'Fetched logs for id_run {id_run}: {logs}')
            return jsonify(logs), 200  # Return sorted logs
        else:
            logging.error(f'No logs found for id_run {id_run}.')
            return jsonify({'message': 'No logs found for the provided id_run'}), 404
    except psycopg2.Error as e:
        # Log and handle any database errors
        logging.error(f'Database error while fetching logs for id_run {id_run}: {e}')
        return jsonify({'error': 'Database error', 'message': str(e)}), 500
    finally:
        # Ensure the database connection is closed
        cur.close()
        conn.close()

##################################################
##################################################
######            OUTCOMES            ############
##################################################
##################################################
            
@app.route('/insert_outcome_run', methods=['POST'])
def insert_outcome_run_new_arch():
    """
    Inserts a new outcome run into the updated architecture database table with enhanced fields.
    This method expects a JSON payload with keys corresponding to the database columns. 
    Missing fields will be set to None, translating to NULL in the SQL database. 
    The method also captures the current timestamp with microsecond precision to record the exact insertion time.

    JSON Payload Example:
    {
        "id_run": 1,
        "id_category": 0,
        "id_type": 1,
        "v_integer": 100,
        "v_floatpoint": 1.23,
        "v_string": "example",
        "v_jsonb": {"key": "value"},  # This is the new field
        "v_boolean": true,
        "v_timestamp": "2024-01-01T00:00:00"
    }
    
    Returns:
        A JSON response with a message indicating the outcome of the operation and a 201 status code upon success.
    """
    
    data = request.json
    conn_response = get_db_connection() # Attempt to get a database connection
    if isinstance(conn_response, tuple): # Check if a tuple was returned, indicating an error
        return conn_response  # Return the JSON error response and status code
    conn = conn_response
    cur = conn.cursor()

    # Generate the current timestamp with microsecond precision
    current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    logging.debug(f'Current timestamp: {current_timestamp}')

    # Convert dict to JSON string for JSONB field
    v_jsonb = json.dumps(data.get('v_jsonb',None))  # Default to empty dict if not provided

    # Prepare the data for insertion, setting unspecified fields to None
    insert_data = (
        data.get('id_run'),
        data.get('id_category'),
        data.get('id_type'),
        data.get('v_integer', None),
        data.get('v_floatpoint', None),
        data.get('v_string', None),
        v_jsonb,
        data.get('v_boolean', None),
        data.get('v_timestamp', None),
        current_timestamp
    )

    try:
        # Execute the INSERT command
        cur.execute("""
            INSERT INTO "outcome_run_table"
            (id_run, id_category, id_type, v_integer, v_floatpoint, v_string, v_jsonb, v_boolean, v_timestamp, timestamp) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, insert_data)
        
        conn.commit()
        return jsonify({'message': 'Outcome_Run inserted successfully'}), 201
    except Error as e:
        logging.error(f'Database error during insert_outcome_run: {e}')
        return jsonify({'error': str(e), 'message': 'Failed to insert outcome run'}), 500
    finally:
        # Cleanup database resources
        cur.close()
        conn.close()

@app.route('/get_outcome_by_category_type/<int:id_run>/<int:id_category>/<int:id_type>', methods=['GET'])
def get_outcome_by_category_type(id_run, id_category, id_type):
    logging.debug(f'Starting get_outcome_by_category_type process for id_run: {id_run}, id_category: {id_category}, id_type: {id_type}')
    conn_response = get_db_connection() # Attempt to get a database connection
    if isinstance(conn_response, tuple): # Check if a tuple was returned, indicating an error
        return conn_response  # Return the JSON error response and status code
    conn = conn_response
    cur = conn.cursor()

    try:
        # Fetch the outcomes for the given id_run, id_category, and id_type
        cur.execute("""
            SELECT * FROM "outcome_run_table" 
            WHERE id_run = %s AND id_category = %s AND id_type = %s
            """, (id_run, id_category, id_type))
        outcomes = cur.fetchall()

        if outcomes:
            logging.debug(f'Fetched outcomes for id_run {id_run}, id_category {id_category}, id_type {id_type}: {outcomes}')
            return jsonify(outcomes), 200  # Return outcomes
        else:
            logging.error(f'No outcomes found for id_run {id_run}, id_category {id_category}, id_type {id_type}.')
            return jsonify({'message': 'No outcomes found for the provided run ID, category, and type'}), 404
    except psycopg2.Error as e:
        # Log and handle any database errors
        logging.error(f'Database error while fetching outcomes: {e}')
        return jsonify({'error': 'Database error', 'message': str(e)}), 500
    finally:
        # Close the database connection
        cur.close()
        conn.close()
        
    
@app.route('/getOutcome', methods=['GET'])
def getOutcome():
    """
    Endpoint to retrieve outcomes based on provided query string parameters.
    Filters outcomes in the 'outcome_run' table based on parameters.

    Example Usage:
        GET /getOutcome?id_run=1&id_category=2&v_string=example

    Query Parameters:
        - id_run (int): ID of the run.
        - id_category (int): Category ID.
        - id_type (int): Type ID.
        - v_integer (int): Integer value.
        - v_floatpoint (float): Floating point value.
        - v_string (str): String value.
        - v_boolean (bool): Boolean value (true/false).
        - v_jsonb (str): JSONB formatted string.
        - v_timestamp (str): Precise timestamp of the entry.
        - timestamp (str): Timestamp of the outcome.

    Returns:
        - JSON response with a list of outcomes matching the query parameters.
        - 200 HTTP status code if outcomes are found.
        - 404 HTTP status code if no outcomes are found.
    """
    # Retrieve arguments from the query string
    query_parts = ["""SELECT * FROM "outcome_run_table" WHERE 1=1"""]
    query_params = []

    # Dynamically build query based on provided parameters
    for param in ['id_run', 'id_category', 'id_type', 'v_integer', 'v_floatpoint', 'v_string', 'v_boolean', 'v_jsonb', 'v_timestamp', 'timestamp']:
        if param in request.args:
            query_parts.append(f"AND {param} = %s")
            value = request.args[param]
            # Special handling for JSONB data
            if param == 'v_jsonb':
                value = json.dumps(value)
            query_params.append(value)

    query = " ".join(query_parts)

    try:
        conn_response = get_db_connection() # Attempt to get a database connection
        if isinstance(conn_response, tuple): # Check if a tuple was returned, indicating an error
            return conn_response  # Return the JSON error response and status code
        conn = conn_response
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)  # Make sure to use RealDictCursor
        cur.execute(query, query_params)
        outcomes = cur.fetchall()

        if not outcomes:
            return jsonify({'message': 'No outcomes found for the provided parameters'}), 404

        cur.close()

        return jsonify(outcomes), 200  # Directly return the list of RealDictRow objects as JSON
    except psycopg2.Error as e:
        logging.error("Database query error: %s", e)
        return jsonify({'error': 'Database error', 'message': str(e)}), 500
    finally:
        if conn:
            conn.close()
    
##################################################
##################################################
######            RUNS                ############
##################################################
##################################################

@app.route('/create_new_run', methods=['POST'])
def create_new_run_new_architecture():
    logging.debug('Starting create_new_run_new_architecture process.')
    
    # Extract parameters from the request
    id_script = request.json.get('id_script')
    id_run_father = request.json.get('id_run_father', None)  # Default to None if not provided

    # Ensure that mandatory parameter is present
    if id_script is None:
        logging.error('id_script is a mandatory parameter.')
        return jsonify({'message': 'id_script is a mandatory parameter.'}), 400

    conn_response = get_db_connection() # Attempt to get a database connection
    if isinstance(conn_response, tuple): # Check if a tuple was returned, indicating an error
        return conn_response  # Return the JSON error response and status code
    conn = conn_response
    cur = conn.cursor()
    # Get the current timestamp
    current_timestamp = datetime.now()
    logging.debug(f'Current timestamp: {current_timestamp}')

    try:
        # Insert the new run into the runs table without specifying id_run
        logging.debug('Inserting the new run into the runs table.')
        cur.execute("""
            INSERT INTO "runs_table" (id_script, id_run_father, timestamp) 
            VALUES (%s, %s, %s) RETURNING id_run
        """, (id_script, id_run_father, current_timestamp))
        result = cur.fetchone()
        if result:
            new_id_run = result['id_run']  # Access by column name
            conn.commit()
            logging.debug(f'New run created successfully with id_run: {new_id_run}')
            return jsonify({'id_run': new_id_run}), 201
        else:
            raise Exception('No row inserted.')
    except Exception as e:
        logging.error(f'Error creating new run: {e}')
        conn.rollback()
        return jsonify({'message': 'Error creating new run', 'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/get_all_runs', methods=['GET'])
def get_all_runs():
    """
    Retrieves all runs from the database, including their script IDs, father run IDs, 
    and timestamps, and returns them sorted by timestamp in descending order.

    
    Returns:
        - JSON response with a list of runs.
        - 200 HTTP status code if runs are found.
        - 404 HTTP status code if no runs are found.
    """
    logging.debug('Starting get_all_runs process.')
    try:
        conn_response = get_db_connection() # Attempt to get a database connection
        if isinstance(conn_response, tuple): # Check if a tuple was returned, indicating an error
            return conn_response  # Return the JSON error response and status code
        conn = conn_response
        cur = conn.cursor()

        # Fetch all run information and order by timestamp in descending order
        cur.execute("""SELECT id_run, id_script, id_run_father, timestamp FROM "runs_table" ORDER BY timestamp DESC""")
        runs = cur.fetchall()

        # Close the database connection
        cur.close()

        if runs:
            # Process the data, for example, replacing None with 'No Father Run'
            processed_runs = [
                {
                    'id_run': run['id_run'],
                    'id_script': run['id_script'],
                    'id_run_father': run.get('id_run_father', 'No Father Run'),
                    'timestamp': run['timestamp']
                }
                for run in runs
            ]

            logging.debug(f'Fetched runs successfully: {processed_runs}')
            return jsonify(processed_runs), 200  # Return all runs with additional fields
        else:
            logging.error('No runs found.')
            return jsonify({'message': 'No runs found'}), 404

    except psycopg2.Error as e:
        logging.error("Database query error: %s", e)
        return jsonify({'error': 'Database error', 'message': str(e)}), 500
    finally:
        if conn:
            conn.close()
    

@app.route('/get_father_runs', methods=['GET'])
def get_father_runs():
    logging.debug('Starting get_father_runs process.')
    conn_response = get_db_connection() # Attempt to get a database connection
    if isinstance(conn_response, tuple): # Check if a tuple was returned, indicating an error
        return conn_response  # Return the JSON error response and status code
    conn = conn_response
    cur = conn.cursor()

    # Query to fetch runs that do not have a child (id_run_father is NULL)
    query = """
    SELECT id_run, timestamp
    FROM "runs_table"
    WHERE id_run_father IS NULL
    ORDER BY id_run DESC
    """
    
    cur.execute(query)
    father_runs = cur.fetchall()

    cur.close()
    conn.close()

    # Return the list of father runs
    if father_runs:
        logging.debug(f'Fetched father runs successfully: {father_runs}')
        return jsonify(father_runs), 200
    else:
        logging.error('No father runs found.')
        return jsonify({'message': 'No father runs found'}), 404


@app.route('/get_runid_childs/<int:father_runid>', methods=['GET'])
def get_runid_childs(father_runid):
    logging.debug(f'Starting get_runid_childs process for father_runid: {father_runid}')
    conn_response = get_db_connection() # Attempt to get a database connection
    if isinstance(conn_response, tuple): # Check if a tuple was returned, indicating an error
        return conn_response  # Return the JSON error response and status code
    conn = conn_response
    cur = conn.cursor()

    try:
        # Fetch all child run IDs that have the given father_runid
        cur.execute("""
            SELECT id_run
            FROM "runs_table"
            WHERE id_run_father = %s
            ORDER BY id_run DESC
            """, (father_runid,))
        child_runs = cur.fetchall()

        # Extract the id_run from each child run record
        child_run_ids = [run['id_run'] for run in child_runs]

        if child_run_ids:
            logging.debug(f'Fetched child run IDs for father_runid {father_runid}: {child_run_ids}')
            return jsonify(child_run_ids), 200  # Return list of child run IDs
        else:
            logging.info(f'No child runs found for father_runid {father_runid}.')
            # Instead of returning a 404 error, return an empty array with a 200 OK status
            return jsonify([]), 200
    except psycopg2.Error as e:
        # Log and handle any database errors
        logging.error(f'Database error while fetching child runs for father_runid {father_runid}: {e}')
        return jsonify({'error': 'Database error', 'message': str(e)}), 500
    finally:
        # Close the database connection
        cur.close()
        conn.close()

##################################################
##################################################
######            data_run_types      ############
##################################################
##################################################

@app.route('/get_data_run_types', methods=['GET'])
def get_data_run_types():
    # Retrieve arguments from the query string
    id_category = request.args.get('id_category', default=None, type=int)
    id_type = request.args.get('id_type', default=None, type=int)
    category_name = request.args.get('category_name', default=None, type=str)
    type_name = request.args.get('type_name', default=None, type=str)

    # Build the base query
    query = """SELECT * FROM "data_run_types_table" WHERE 1=1"""
    query_params = []

    # Dynamically append conditions to the query based on provided arguments
    if id_category is not None:
        query += " AND id_category = %s"
        query_params.append(id_category)
    if id_type is not None:
        query += " AND id_type = %s"
        query_params.append(id_type)
    if category_name is not None:
        query += " AND category_name = %s"
        query_params.append(category_name)
    if type_name is not None:
        query += " AND type_name = %s"
        query_params.append(type_name)

    conn_response = get_db_connection() # Attempt to get a database connection
    if isinstance(conn_response, tuple): # Check if a tuple was returned, indicating an error
        return conn_response  # Return the JSON error response and status code
    conn = conn_response
    cur = conn.cursor()
    try:
        cur.execute(query, query_params)
        data_run_types = cur.fetchall()
        # Check if data_run_types are found and return the results
        if data_run_types:
            return jsonify(data_run_types), 200
        else:
            return jsonify({'message': 'No data types found for the provided parameters'}), 404
    except psycopg2.Error as e:
        # Log and handle any database errors
        logging.error(f'Database error while fetching data run types: {e}')
        return jsonify({'error': 'Database error', 'message': str(e)}), 500
    finally:
        # Close the database connection
        cur.close()
        conn.close()
    



@app.route('/')
def index():
    return render_template('index.html')
    

# Version history tracking
version_history = {
    "v1.2": "Added jsonb v_type in outcome_runs table.",
    "v1.1": "Added v_boolean v_timestamp and timestamp in outcome_runs table.",
    "v1.0": "Initial release."
    
}


if __name__ == '__main__':
    # Set the port to 5431 or to the 'PORT' environment variable if it is set.
    port = int(os.environ.get('PORT', 5435))
    # Enable debug mode if the 'FLASK_DEBUG' environment variable is set to 'true'.
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    # Run the Flask application on the host 'localhost' which binds to all available interfaces.
    app.run(debug=True, host='localhost', port=port)