from flask import Blueprint, jsonify, Response, request, stream_with_context
from ..scraper.scraper import scrape_pms_inventory
from ..scraper.combine_inventory import combine_inventory_files
from ..scraper.yielder import load_and_clean_data, apply_yield_matrix
from ..scraper.process_cm_inventory import process_cm_inventory
from ..scraper.update_pms_cm_allotment import update_allotmet
from ..shared import log_queue
import queue
import threading
import time
import sys
from io import StringIO
import logging
from werkzeug.utils import secure_filename
import os
import json
import sqlite3
import pandas as pd

bp = Blueprint('main', __name__)

# Global variables for scraping progress
scraping_active = False
scraping_error = None
scraping_progress = queue.Queue()

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scraper', 'data')
ALLOWED_EXTENSIONS = {'xlsx'}

class RealTimeStringIO(StringIO):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue
        self._is_capturing = False

    def write(self, text):
        if not self._is_capturing:
            self._is_capturing = True
            try:
                if text.strip():  # Only process non-empty lines
                    self.queue.put(text.strip())
            finally:
                self._is_capturing = False

def scrape_with_progress(start_date=None):
    global scraping_active, scraping_error
    try:
        # Redirect stdout to capture print statements
        old_stdout = sys.stdout
        sys.stdout = RealTimeStringIO(scraping_progress)
        
        result = scrape_pms_inventory(start_date)
        
        # Restore stdout
        sys.stdout = old_stdout
        
        if result is not None:
            scraping_progress.put({"status": "success", "message": "Scraping completed successfully"})
        else:
            scraping_error = "Scraping failed"
            scraping_progress.put({"status": "error", "message": "Scraping failed"})
    except Exception as e:
        scraping_error = str(e)
        scraping_progress.put({"status": "error", "message": str(e)})
    finally:
        scraping_active = False

@bp.route('/api/health')
def health_check():
    return jsonify({"status": "healthy"})

@bp.route('/api/scrape', methods=['POST'])
def trigger_scrape():
    global scraping_active, scraping_error
    if scraping_active:
        return jsonify({"status": "error", "message": "Scraping already in progress"}), 409
    
    # Get start date from request
    start_date = request.json.get('startDate')
    if not start_date:
        return jsonify({"status": "error", "message": "Start date is required"}), 400
    
    # Reset error state
    scraping_error = None
    scraping_active = True
    
    # Clear the queue
    while not scraping_progress.empty():
        try:
            scraping_progress.get_nowait()
        except queue.Empty:
            break
    
    scraping_thread = threading.Thread(target=scrape_with_progress, args=(start_date,))
    scraping_thread.daemon = True
    scraping_thread.start()
    
    return jsonify({"status": "success", "message": "Scraping started"})

@bp.route('/api/scrape/stream')
def scrape_stream():
    def generate():
        global scraping_error
        while scraping_active or not scraping_progress.empty():
            try:
                if not scraping_progress.empty():
                    message = scraping_progress.get()
                    yield f"data: {json.dumps(message)}\n\n"
                elif scraping_error:
                    yield f"data: {json.dumps({'status': 'error', 'message': scraping_error})}\n\n"
                    break
                else:
                    yield f"data: {json.dumps({'status': 'pending'})}\n\n"
                time.sleep(0.1)
            except Exception as e:
                yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"
                break
        if not scraping_error:
            yield f"data: {json.dumps({'status': 'complete', 'message': 'Scraping completed successfully'})}\n\n"

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )

@bp.route('/api/combine-inventory', methods=['POST'])
def trigger_combine():
    try:
        print("Starting inventory combination process...")
        
        # Check if required files exist
        pms_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scraper', 'data', 'pms_inventory_processed.db')
        cm_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scraper', 'data', 'cm_inventory_processed.db')
        
        if not os.path.exists(pms_db_path):
            return jsonify({
                "status": "error",
                "message": "PMS inventory database not found. Please run scraping first."
            }), 400
            
        if not os.path.exists(cm_db_path):
            return jsonify({
                "status": "error",
                "message": "CM inventory database not found. Please upload and process CM Excel file first."
            }), 400
        
        print(f"Found required databases: PMS={pms_db_path}, CM={cm_db_path}")
        
        result = combine_inventory_files()
        
        # Verify the combined database was created
        combined_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scraper', 'data', 'combined_inventory.db')
        if not os.path.exists(combined_db_path):
            return jsonify({
                "status": "error",
                "message": "Failed to create combined inventory database"
            }), 500
            
        # Verify data was written
        conn = sqlite3.connect(combined_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM combined_inventory")
        count = cursor.fetchone()[0]
        conn.close()
        
        if count == 0:
            return jsonify({
                "status": "error",
                "message": "No data was written to the combined inventory database"
            }), 500
            
        print(f"Successfully combined inventory with {count} rows")
        
        return jsonify({
            "status": "success",
            "message": "Inventory combination completed successfully",
            "data": str(result)
        })
    except Exception as e:
        print(f"Error in combine inventory: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@bp.route('/api/yield', methods=['POST'])
def trigger_yield():
    try:
        print("Starting yield calculation process...")
        
        # Check if combined inventory exists
        combined_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scraper', 'data', 'combined_inventory.db')
        if not os.path.exists(combined_db_path):
            return jsonify({
                "status": "error",
                "message": "Combined inventory database not found. Please run combine inventory first."
            }), 400

        # Call the main function which handles the entire process
        from ..scraper.yielder import main
        result = main()
        
        if result is None:
            return jsonify({
                "status": "error",
                "message": "Failed to process yield calculation"
            }), 500
        
        # Verify the database was created
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scraper', 'data', 'inventory_allocation.db')
        if not os.path.exists(db_path):
            return jsonify({
                "status": "error",
                "message": "Failed to create inventory allocation database"
            }), 500

        # Verify the data was written correctly
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM daily_inventory_allocation")
        count = cursor.fetchone()[0]
        conn.close()

        if count == 0:
            return jsonify({
                "status": "error",
                "message": "No data was written to the inventory allocation database"
            }), 500

        # Convert the result to a format that can be serialized to JSON
        result_dict = result.to_dict(orient='records')
        
        return jsonify({
            "status": "success",
            "message": "Yield calculation completed successfully",
            "data": result_dict
        })
    except Exception as e:
        print(f"Error in yield calculation: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to calculate yield: {str(e)}"
        }), 500

@bp.route('/api/process-cm', methods=['POST'])
def trigger_process_cm():
    try:
        result = process_cm_inventory()
        return jsonify({
            "status": "success",
            "message": "CM inventory processing completed successfully",
            "data": str(result)
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@bp.route('/api/custom-yield', methods=['POST'])
def trigger_custom_yield():
    try:
        print("Starting custom yield calculation process...")
        
        # Get configuration from request
        config = request.json
        if not config:
            return jsonify({
                "status": "error",
                "message": "No configuration provided"
            }), 400

        # Validate required configuration
        required_configs = {
            'demand_bins': list,
            'demand_labels': list,
            'very_low_threshold_pct': (int, float),
            'low_threshold_pct': (int, float),
            'room_caps': dict,
            'deluxe_override_occupancy': (int, float),
            'deluxe_override_premiere': (int, float),
            'deluxe_override_amount': (int, float)
        }

        for key, expected_type in required_configs.items():
            if key not in config:
                return jsonify({
                    "status": "error",
                    "message": f"Missing required configuration: {key}"
                }), 400
            if not isinstance(config[key], expected_type):
                return jsonify({
                    "status": "error",
                    "message": f"Invalid type for {key}. Expected {expected_type}, got {type(config[key])}"
                }), 400

        # Check if combined inventory exists
        combined_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scraper', 'data', 'combined_inventory.db')
        if not os.path.exists(combined_db_path):
            return jsonify({
                "status": "error",
                "message": "Combined inventory database not found. Please run combine inventory first."
            }), 400

        # Import the yielder module
        from ..scraper.yielder import load_and_clean_data, apply_yield_matrix

        # Load and clean data with custom configuration
        data = load_and_clean_data(
            demand_bins=config['demand_bins'],
            demand_labels=config['demand_labels']
        )
        
        if data is None:
            return jsonify({
                "status": "error",
                "message": "Failed to load and clean data"
            }), 500

        # Apply yield matrix with custom configuration
        result = apply_yield_matrix(
            data,
            very_low_threshold_pct=config['very_low_threshold_pct'],
            low_threshold_pct=config['low_threshold_pct'],
            room_caps=config['room_caps']
        )

        # Save to database
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scraper', 'data', 'inventory_allocation.db')
        conn = sqlite3.connect(db_path)
        
        # Enable date handling in SQLite
        conn.execute('PRAGMA foreign_keys = ON')
        
        # Define SQLite data types for each column
        dtype = {
            'Date': 'DATE',
            'DayOfWeek': 'TEXT',
            'Season': 'TEXT',
            'Occupancy': 'REAL',
            'DemandLevel': 'TEXT',
            'Deluxe Remaining Inventory': 'INTEGER',
            'Deluxe Online Inventory': 'INTEGER',
            'Deluxe BAR Rate': 'TEXT',
            'Premiere Remaining Inventory': 'INTEGER',
            'Premiere Online Inventory': 'INTEGER',
            'Premiere BAR Rate': 'TEXT'
        }
        
        # Ensure date is in YYYY-MM-DD format before saving
        result['Date'] = pd.to_datetime(result['Date']).dt.strftime('%Y-%m-%d')
        
        # Save to database
        result.to_sql('daily_inventory_allocation', conn, if_exists='replace', index=False, dtype=dtype)
        
        # Verify the data was written
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM daily_inventory_allocation")
        count = cursor.fetchone()[0]
        conn.close()

        if count == 0:
            return jsonify({
                "status": "error",
                "message": "No data was written to the inventory allocation database"
            }), 500

        # Convert the result to a format that can be serialized to JSON
        result_dict = result.to_dict(orient='records')
        
        return jsonify({
            "status": "success",
            "message": "Custom yield calculation completed successfully",
            "data": result_dict
        })
    except Exception as e:
        print(f"Error in custom yield calculation: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to calculate custom yield: {str(e)}"
        }), 500

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/api/upload-cm-excel', methods=['POST'])
def upload_cm_excel():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename('cm_upload.xlsx')
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)
        return jsonify({'status': 'success', 'message': 'File uploaded successfully'})
    return jsonify({'status': 'error', 'message': 'Invalid file type'}), 400

@bp.route('/api/db/inventory-allocation')
def get_inventory_allocation():
    try:
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scraper', 'data', 'inventory_allocation.db')
        if not os.path.exists(db_path):
            return jsonify({
                "status": "error",
                "message": "Inventory allocation database not found"
            }), 404

        conn = sqlite3.connect(db_path)
        data = pd.read_sql_query("SELECT * FROM daily_inventory_allocation", conn)
        conn.close()

        # Convert the data to a format that can be serialized to JSON
        result = data.to_dict(orient='records')
        
        return jsonify({
            "status": "success",
            "data": result
        })
    except Exception as e:
        print(f"Error fetching inventory allocation: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to fetch inventory allocation: {str(e)}"
        }), 500

def log_stream():
    """Generator function to stream logs"""
    while True:
        try:
            # Get log message from queue
            log_data = log_queue.get()
            if log_data is None:  # None is used as a signal to stop
                break
            # Yield the log data as SSE
            yield f"data: {json.dumps(log_data)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

@bp.route('/api/update-allotment/stream')
def stream_allotment_logs():
    """Stream allotment update logs using Server-Sent Events"""
    return Response(
        stream_with_context(log_stream()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )

@bp.route('/api/update-allotment', methods=['POST'])
def trigger_update_allotment():
    """Trigger allotment update process"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({
                'status': 'error',
                'message': 'Username and password are required'
            }), 400

        # Start update process in a separate thread
        def update_process():
            try:
                # Add initial log
                log_queue.put({
                    'type': 'info',
                    'message': 'Starting allotment update process...'
                })

                # Call the update function
                result = update_allotmet(username=username, password=password)

                if result:
                    log_queue.put({
                        'type': 'success',
                        'message': 'Allotment updated successfully!'
                    })
                else:
                    log_queue.put({
                        'type': 'error',
                        'message': 'Failed to update allotment'
                    })
            except Exception as e:
                log_queue.put({
                    'type': 'error',
                    'message': f'Error during update: {str(e)}'
                })
            finally:
                # Signal the end of streaming
                log_queue.put(None)

        # Start the update process in a background thread
        thread = threading.Thread(target=update_process)
        thread.start()

        return jsonify({
            'status': 'success',
            'message': 'Update process started'
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 