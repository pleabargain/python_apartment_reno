from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
from pathlib import Path
import os
import logging
from datetime import datetime
import shutil
import uuid
import mimetypes
import traceback

# Configure logging with more detailed formatting
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('server.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Add file handler for JSON-specific operations
json_logger = logging.getLogger('json_operations')
json_logger.setLevel(logging.DEBUG)
json_handler = logging.FileHandler('json_operations.log', encoding='utf-8')
json_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'))
json_logger.addHandler(json_handler)

def get_latest_version():
    """Get the latest version file from the versions directory"""
    versions_dir = 'versions'
    if not os.path.exists(versions_dir):
        os.makedirs(versions_dir)
        logger.info(f"Created versions directory: {versions_dir}")
        return None
    
    version_files = [f for f in os.listdir(versions_dir) if f.endswith('.json')]
    if not version_files:
        return None
    
    latest_version = sorted(version_files)[-1]
    return os.path.join(versions_dir, latest_version)

def load_json_file(filepath, backup_recovery=True):
    """Load and parse a JSON file with error handling and backup recovery"""
    json_logger.info(f"Attempting to load JSON file: {filepath}")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                json_logger.info(f"Successfully loaded JSON from {filepath}")
                return data
            except json.JSONDecodeError as e:
                json_logger.error(f"JSON decode error in {filepath}: {str(e)}", exc_info=True)
                if backup_recovery:
                    # Attempt to recover from backup
                    backup_files = sorted([f for f in os.listdir() if f.startswith(f"{os.path.basename(filepath)}.") and f.endswith('.bak')])
                    if backup_files:
                        latest_backup = backup_files[-1]
                        json_logger.warning(f"Attempting to recover from backup: {latest_backup}")
                        return load_json_file(latest_backup, backup_recovery=False)
                raise
    except FileNotFoundError:
        json_logger.error(f"File not found: {filepath}", exc_info=True)
        raise
    except Exception as e:
        json_logger.error(f"Unexpected error loading {filepath}: {str(e)}", exc_info=True)
        raise

def save_json_file(filepath, data, indent=2):
    """Save JSON data to file with error handling"""
    json_logger.info(f"Attempting to save JSON file: {filepath}")
    try:
        # Create backup before saving
        if os.path.exists(filepath):
            create_backup(filepath)
        
        # Only create directories if filepath includes a directory path
        directory = os.path.dirname(filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        # Save the file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent)
        json_logger.info(f"Successfully saved JSON to {filepath}")
        return True
    except Exception as e:
        json_logger.error(f"Error saving JSON to {filepath}: {str(e)}", exc_info=True)
        return False

def ensure_directory(directory):
    """Ensure a directory exists, create if it doesn't"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")

def get_file_type(filename):
    """Determine file type based on mimetype"""
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type:
        if mime_type.startswith('image/'):
            return 'image'
        elif mime_type.startswith(('application/', 'text/')):
            return 'document'
    return 'other'

def save_uploaded_file(file_data, room_name):
    """Save an uploaded file and return its metadata"""
    # Generate unique filename
    original_filename = file_data['filename']
    ext = os.path.splitext(original_filename)[1]
    unique_filename = f"{uuid.uuid4()}{ext}"
    
    # Determine file type and directory
    file_type = get_file_type(original_filename)
    uploads_dir = os.path.join('uploads', room_name)
    ensure_directory(uploads_dir)
    
    # Save file
    filepath = os.path.join(uploads_dir, unique_filename)
    with open(filepath, 'wb') as f:
        f.write(file_data['file'])
    
    # Create metadata
    metadata = {
        "filename": unique_filename,
        "original_filename": original_filename,
        "type": file_type,
        "uploaded_at": datetime.now().isoformat(),
        "description": ""
    }
    
    return metadata

def create_backup(filename):
    """Create a timestamped backup of the file"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"{filename}.{timestamp}.bak"
    try:
        shutil.copy2(filename, backup_name)
        logger.info(f"Created backup: {backup_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to create backup: {str(e)}")
        return False

def validate_save_data(data, path):
    """Validate the data being saved"""
    json_logger.info(f"Validating data for path: {path}")
    try:
        if path == '/save':
            if not isinstance(data, dict):
                json_logger.error("Building management data must be a dictionary")
                return False, "Building management data must be a dictionary"
        elif path == '/save_rooms':
            if not isinstance(data, dict):
                json_logger.error("Room data must be a dictionary")
                return False, "Room data must be a dictionary"
            for room, room_data in data.items():
                if not isinstance(room_data, dict):
                    json_logger.error(f"Invalid data format for room {room}")
                    return False, f"Invalid data format for room {room}"
        elif path == '/add_project':
            required_fields = ['title', 'description', 'budget', 'priority', 'room_name']
            for field in required_fields:
                if field not in data:
                    json_logger.error(f"Missing required field: {field}")
                    return False, f"Missing required field: {field}"
        json_logger.info("Data validation successful")
        return True, None
    except Exception as e:
        json_logger.error(f"Validation error: {str(e)}", exc_info=True)
        return False, str(e)

class BuildingManagementHandler(SimpleHTTPRequestHandler):
    def send_json_response(self, data, status=200):
        """Helper method to send JSON responses"""
        try:
            self.send_response(status)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Convert data to JSON and send in chunks
            json_data = json.dumps(data)
            chunk_size = 8192  # 8KB chunks
            
            for i in range(0, len(json_data), chunk_size):
                chunk = json_data[i:i + chunk_size]
                try:
                    self.wfile.write(chunk.encode())
                except (ConnectionAbortedError, BrokenPipeError) as e:
                    logger.error(f"Connection error while sending response: {str(e)}")
                    break
                
        except Exception as e:
            logger.error(f"Error sending JSON response: {str(e)}\n{traceback.format_exc()}")
            raise

    def parse_multipart(self):
        """Parse multipart form data"""
        content_type = self.headers.get('Content-Type')
        if not content_type:
            return None
        
        try:
            boundary = content_type.split('=')[1].encode()
            remainbytes = int(self.headers['Content-Length'])
            line = self.rfile.readline()
            remainbytes -= len(line)
            
            if not boundary in line:
                return None
            
            form = {}
            while remainbytes > 0:
                line = self.rfile.readline()
                remainbytes -= len(line)
                
                if boundary in line:
                    break
                
                # Parse headers
                line = line.decode()
                if 'Content-Disposition' in line:
                    # Get field name and filename if present
                    key = line.split('name="')[1].split('"')[0]
                    if 'filename="' in line:
                        # File upload
                        filename = line.split('filename="')[1].split('"')[0]
                        # Skip content type line
                        line = self.rfile.readline()
                        remainbytes -= len(line)
                        # Skip blank line
                        line = self.rfile.readline()
                        remainbytes -= len(line)
                        # Read file content
                        form[key] = {
                            'filename': filename,
                            'file': self.rfile.read(remainbytes)
                        }
                        break
                    else:
                        # Regular form field
                        # Skip blank line
                        line = self.rfile.readline()
                        remainbytes -= len(line)
                        # Read value
                        line = self.rfile.readline()
                        remainbytes -= len(line)
                        form[key] = line.decode().strip()
            
            return form
        except Exception as e:
            logger.error(f"Error parsing multipart data: {str(e)}\n{traceback.format_exc()}")
            return None

    def do_POST(self):
        logger.info(f"Received POST request to {self.path}")
        
        try:
            if self.path == '/upload':
                form = self.parse_multipart()
                if not form:
                    self.send_error(400, "Invalid form data")
                    return
                
                room_name = form.get('room_name')
                if not room_name:
                    self.send_error(400, "Room name is required")
                    return
                
                file_data = form.get('file')
                if not file_data:
                    self.send_error(400, "No file uploaded")
                    return
                
                # Save file and get metadata
                metadata = save_uploaded_file(file_data, room_name)
                
                self.send_json_response({
                    "status": "success",
                    "message": "File uploaded successfully",
                    "metadata": metadata
                })
                
            elif self.path == '/add_project':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                # Validate project data
                is_valid, error_msg = validate_save_data(data, self.path)
                if not is_valid:
                    self.send_error(400, error_msg)
                    return
                
                # Read current data with robust error handling
                try:
                    full_data = load_json_file('converted_source.json')
                except Exception as e:
                    self.send_error(500, f"Error loading data: {str(e)}")
                    return
                
                room_name = data['room_name']
                if room_name not in full_data['rooms']:
                    self.send_error(400, f"Room {room_name} not found")
                    return
                
                # Initialize projects array if it doesn't exist
                if 'projects' not in full_data['rooms'][room_name]:
                    full_data['rooms'][room_name]['projects'] = []
                
                # Add new project
                project = {
                    "title": data['title'],
                    "description": data['description'],
                    "budget": float(data['budget']),
                    "priority": data['priority'],
                    "created_at": datetime.now().isoformat(),
                    "status": "planned",
                    "attachments": []
                }
                
                full_data['rooms'][room_name]['projects'].append(project)
                
                # Save updated data with error handling
                if not save_json_file('converted_source.json', full_data):
                    self.send_error(500, "Failed to save updated data")
                    return
                
                self.send_json_response({
                    "status": "success",
                    "message": "Project added successfully"
                })
                
            else:
                # Handle existing POST endpoints
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                try:
                    data = json.loads(post_data.decode('utf-8'))
                    json_logger.info("Successfully parsed JSON data")
                except json.JSONDecodeError as e:
                    json_logger.error(f"Failed to parse JSON: {e}")
                    self.send_error(400, "Invalid JSON data")
                    return
                
                # Read the existing file with robust error handling
                try:
                    full_data = load_json_file('converted_source.json')
                except Exception as e:
                    self.send_error(500, f"Error loading data: {str(e)}")
                    return
                    
                if self.path == '/save':
                    # Update building management section
                    full_data['general_considerations']['building_management'] = data
                
                elif self.path == '/save_rooms':
                    # Update rooms section
                    json_logger.debug(f"Received room data: {json.dumps(data, indent=2)}")
                    for room_name, room_data in data.items():
                        if room_name in full_data['rooms']:
                            json_logger.debug(f"Updating {room_name}")
                            current_room = full_data['rooms'][room_name]
                            
                            # Update priority
                            current_room['priority'] = room_data['priority']
                            json_logger.debug(f"Updated priority to {room_data['priority']}")
                            
                            # Update budget
                            if 'budget' in room_data:
                                current_room['budget']['amount'] = float(room_data['budget']['amount'])
                                current_room['budget']['notes'] = room_data['budget']['notes']
                                json_logger.debug(f"Updated budget to {room_data['budget']['amount']}")
                            
                            # Update square footage
                            if 'square_footage' in room_data:
                                current_room['square_footage']['value'] = int(room_data['square_footage']['value'])
                                json_logger.debug(f"Updated square footage to {room_data['square_footage']['value']}")
                            
                            # Update painting
                            if 'painting' in room_data and 'walls' in room_data['painting']:
                                if 'painting' not in current_room:
                                    current_room['painting'] = {}
                                if 'walls' not in current_room['painting']:
                                    current_room['painting']['walls'] = {}
                                current_room['painting']['walls'].update(room_data['painting']['walls'])
                                json_logger.debug(f"Updated painting data")
                
                # Validate the data before saving
                is_valid, error_msg = validate_save_data(data, self.path)
                if not is_valid:
                    json_logger.error(f"Validation failed: {error_msg}")
                    self.send_error(400, error_msg)
                    return

                # Save the updated data with robust error handling
                timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                json_logger.info(f"Saving changes at {timestamp}")
                
                # Add timestamp to the data
                full_data['last_updated'] = timestamp
                full_data['last_modified_by'] = 'user'  # Could be expanded to track specific users
                
                # Save to timestamped file in versions directory
                versions_dir = 'versions'
                ensure_directory(versions_dir)
                new_filename = os.path.join(versions_dir, f'renovation_data_{timestamp}.json')
                
                if not save_json_file(new_filename, full_data):
                    self.send_error(500, "Failed to save version file")
                    return
                
                # Update the current version
                if not save_json_file('converted_source.json', full_data):
                    self.send_error(500, "Failed to update current version")
                    return
                
                self.send_json_response({
                    "status": "success",
                    "timestamp": timestamp,
                    "message": "Changes saved successfully"
                })
                    
        except Exception as e:
            logger.error(f"Error processing POST request: {str(e)}\n{traceback.format_exc()}")
            self.send_error(500, f"Internal server error: {str(e)}")

    def do_GET(self):
        try:
            if self.path == '/' or self.path == '':
                self.path = '/building_management.html'
            elif self.path.startswith('/uploads/'):
                try:
                    # Serve files from uploads directory
                    file_path = self.path[1:]  # Remove leading slash
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            content = f.read()
                        self.send_response(200)
                        content_type, _ = mimetypes.guess_type(file_path)
                        if content_type:
                            self.send_header('Content-type', content_type)
                        self.end_headers()
                        self.wfile.write(content)
                        return
                    else:
                        self.send_error(404, "File not found")
                        return
                except Exception as e:
                    logger.error(f"Error serving file: {str(e)}\n{traceback.format_exc()}")
                    self.send_error(500, f"Error serving file: {str(e)}")
                    return
            elif self.path == '/list_json_files':
                try:
                    # List files from versions directory
                    versions_dir = 'versions'
                    ensure_directory(versions_dir)
                    
                    json_files = []
                    if os.path.exists(versions_dir):
                        json_files = [f for f in os.listdir(versions_dir) if f.endswith('.json')]
                    
                    self.send_json_response(json_files)
                    return
                except Exception as e:
                    logger.error(f"Error listing JSON files: {str(e)}\n{traceback.format_exc()}")
                    self.send_error(500, f"Error listing JSON files: {str(e)}")
                    return
            elif self.path.startswith('/load_json/'):
                try:
                    filename = os.path.basename(self.path[10:])
                    if not filename.endswith('.json'):
                        self.send_error(400, "Invalid file type")
                        return
                    
                    filepath = os.path.join('versions', filename)
                    if not os.path.exists(filepath):
                        self.send_error(404, "File not found")
                        return
                    
                    # Load and validate JSON with robust error handling
                    try:
                        data = load_json_file(filepath)
                    except Exception as e:
                        self.send_error(500, f"Error loading JSON: {str(e)}")
                        return
                    
                    # Validate JSON structure
                    is_valid, error_msg = self.validate_json_structure(data)
                    if not is_valid:
                        self.send_error(400, error_msg)
                        return
                    
                    # If valid, update current version
                    if not save_json_file('converted_source.json', data):
                        self.send_error(500, "Failed to update current version")
                        return
                    
                    self.send_json_response({
                        "status": "success",
                        "message": "File loaded successfully"
                    })
                    return
                except Exception as e:
                    logger.error(f"Error loading JSON file: {str(e)}\n{traceback.format_exc()}")
                    self.send_error(500, f"Error loading JSON file: {str(e)}")
                    return
            elif self.path == '/converted_source.json':
                try:
                    data = load_json_file('converted_source.json')
                    self.send_json_response(data)
                    return
                except Exception as e:
                    logger.error(f"Error serving JSON file: {str(e)}\n{traceback.format_exc()}")
                    self.send_error(500, f"Error serving JSON file: {str(e)}")
                    return
                    
            return super().do_GET()
            
        except Exception as e:
            logger.error(f"Error processing GET request: {str(e)}\n{traceback.format_exc()}")
            self.send_error(500, f"Internal server error: {str(e)}")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def validate_json_structure(self, data):
        """Validate the JSON data structure with detailed logging"""
        json_logger.info("Starting JSON structure validation")
        
        try:
            required_fields = ['project_name', 'last_updated', 'status', 'rooms']
            for field in required_fields:
                if field not in data:
                    json_logger.error(f"Validation failed: Missing required field '{field}'")
                    return False, f"Missing required field: {field}"
                json_logger.debug(f"Found required field: {field}")
            
            if not isinstance(data.get('rooms'), dict):
                json_logger.error("Validation failed: 'rooms' is not a dictionary")
                return False, "Rooms must be a dictionary"
            
            # Validate room structure
            for room_name, room_data in data.get('rooms', {}).items():
                json_logger.debug(f"Validating room: {room_name}")
                if not isinstance(room_data, dict):
                    json_logger.error(f"Room '{room_name}' data is not a dictionary")
                    return False, f"Invalid room data for {room_name}"
                
                # Validate required room fields
                required_room_fields = ['priority', 'budget']
                for field in required_room_fields:
                    if field not in room_data:
                        json_logger.error(f"Room '{room_name}' missing required field: {field}")
                        return False, f"Room {room_name} missing required field: {field}"
            
            json_logger.info("JSON structure validation completed successfully")
            return True, None
            
        except Exception as e:
            json_logger.error(f"Unexpected error during JSON validation: {str(e)}", exc_info=True)
            return False, f"Validation error: {str(e)}"

def initialize_json_file():
    """Initialize JSON file by loading the latest version"""
    latest_version = get_latest_version()
    if latest_version:
        try:
            data = load_json_file(latest_version)
            if save_json_file('converted_source.json', data):
                logger.info(f"Initialized from latest version: {latest_version}")
                return
        except Exception as e:
            logger.error(f"Failed to initialize from {latest_version}: {str(e)}")
    
    logger.warning("No valid version found in versions directory")
    logger.info("Please load a valid JSON file through the web interface")

def run_server():
    port = 8000
    server_address = ('', port)
    
    # Initialize JSON file from latest version
    initialize_json_file()
    
    # Create required directories
    ensure_directory('uploads')
    ensure_directory('versions')
    
    httpd = HTTPServer(server_address, BuildingManagementHandler)
    print(f"Server running at http://localhost:{port}")
    print("Please load a JSON file through the web interface if no version was found")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
