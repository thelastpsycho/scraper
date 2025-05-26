from flask import Blueprint, jsonify
import sqlite3
import os
import logging

bp = Blueprint('database', __name__)

def get_db_connection(db_name):
    try:
        # Get the absolute path to the scraper/data directory
        current_dir = os.path.dirname(os.path.dirname(__file__))  # backend/app
        db_path = os.path.join(current_dir, 'scraper', 'data', db_name)
        
        # Log the path for debugging
        logging.info(f"Attempting to connect to database at: {db_path}")
        
        if not os.path.exists(db_path):
            logging.error(f"Database file not found: {db_path}")
            raise FileNotFoundError(f"Database file not found: {db_path}")
            
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logging.error(f"Error connecting to database {db_name}: {str(e)}")
        raise

@bp.route('/api/db/combined-inventory', methods=['GET'])
def get_combined_inventory():
    try:
        conn = get_db_connection('combined_inventory.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM combined_inventory')
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        conn.close()
        return jsonify({"status": "success", "data": data})
    except FileNotFoundError as e:
        logging.error(f"Database file not found: {str(e)}")
        return jsonify({"status": "error", "message": "Database file not found"}), 404
    except sqlite3.Error as e:
        logging.error(f"SQLite error: {str(e)}")
        return jsonify({"status": "error", "message": "Database error"}), 500
    except Exception as e:
        logging.error(f"Unexpected error in get_combined_inventory: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/api/db/inventory-allocation', methods=['GET'])
def get_inventory_allocation():
    try:
        conn = get_db_connection('inventory_allocation.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM daily_inventory_allocation')
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        conn.close()
        return jsonify({"status": "success", "data": data})
    except FileNotFoundError as e:
        logging.error(f"Database file not found: {str(e)}")
        return jsonify({"status": "error", "message": "Database file not found"}), 404
    except sqlite3.Error as e:
        logging.error(f"SQLite error: {str(e)}")
        return jsonify({"status": "error", "message": "Database error"}), 500
    except Exception as e:
        logging.error(f"Unexpected error in get_inventory_allocation: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/api/db/pms-inventory-processed', methods=['GET'])
def get_pms_inventory_processed():
    try:
        conn = get_db_connection('pms_inventory_processed.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM pms_inventory_processed')
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        conn.close()
        return jsonify({"status": "success", "data": data})
    except FileNotFoundError as e:
        logging.error(f"Database file not found: {str(e)}")
        return jsonify({"status": "error", "message": "Database file not found"}), 404
    except sqlite3.Error as e:
        logging.error(f"SQLite error: {str(e)}")
        return jsonify({"status": "error", "message": "Database error"}), 500
    except Exception as e:
        logging.error(f"Unexpected error in get_pms_inventory_processed: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/api/db/pms-inventory-raw', methods=['GET'])
def get_pms_inventory_raw():
    try:
        conn = get_db_connection('pms_inventory_raw.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM pms_inventory')
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        conn.close()
        return jsonify({"status": "success", "data": data})
    except FileNotFoundError as e:
        logging.error(f"Database file not found: {str(e)}")
        return jsonify({"status": "error", "message": "Database file not found"}), 404
    except sqlite3.Error as e:
        logging.error(f"SQLite error: {str(e)}")
        return jsonify({"status": "error", "message": "Database error"}), 500
    except Exception as e:
        logging.error(f"Unexpected error in get_pms_inventory_raw: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500 