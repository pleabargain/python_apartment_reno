#!/usr/bin/env python3
import argparse
import json
import logging
from datetime import datetime
import os
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    filename='renovation_manager.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class RenovationManager:
    def __init__(self, json_file: str):
        self.json_file = json_file
        self.data = self.load_json()

    def load_json(self) -> Dict:
        """Load JSON data from file."""
        try:
            with open(self.json_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"File not found: {self.json_file}")
            raise
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON format in {self.json_file}")
            raise

    def save_json(self):
        """Save JSON data to file with backup."""
        # Create backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{os.path.splitext(self.json_file)[0]}_{timestamp}.json"
        with open(backup_file, 'w') as f:
            json.dump(self.data, f, indent=2)
        logging.info(f"Created backup: {backup_file}")

        # Save updated data
        with open(self.json_file, 'w') as f:
            json.dump(self.data, f, indent=2)
        logging.info("Data saved successfully")

    def get_nested_value(self, path: list) -> Any:
        """Get value at nested path."""
        current = self.data
        for key in path:
            if isinstance(current, dict):
                if key not in current:
                    raise KeyError(f"Key '{key}' not found")
                current = current[key]
            elif isinstance(current, list):
                try:
                    idx = int(key)
                    current = current[idx]
                except (ValueError, IndexError):
                    raise KeyError(f"Invalid list index: {key}")
            else:
                raise KeyError(f"Cannot navigate further at {key}")
        return current

    def set_nested_value(self, path: list, value: Any):
        """Set value at nested path."""
        current = self.data
        for i, key in enumerate(path[:-1]):
            if isinstance(current, dict):
                if key not in current:
                    current[key] = {}
                current = current[key]
            elif isinstance(current, list):
                try:
                    idx = int(key)
                    while len(current) <= idx:
                        current.append({})
                    current = current[idx]
                except ValueError:
                    raise KeyError(f"Invalid list index: {key}")
        
        if isinstance(current, dict):
            current[path[-1]] = value
        elif isinstance(current, list):
            try:
                idx = int(path[-1])
                while len(current) <= idx:
                    current.append(None)
                current[idx] = value
            except ValueError:
                raise KeyError(f"Invalid list index: {path[-1]}")
        self.save_json()

    def delete_nested_value(self, path: list):
        """Delete value at nested path."""
        current = self.data
        for key in path[:-1]:
            if isinstance(current, dict):
                if key not in current:
                    raise KeyError(f"Key '{key}' not found")
                current = current[key]
            elif isinstance(current, list):
                try:
                    idx = int(key)
                    current = current[idx]
                except (ValueError, IndexError):
                    raise KeyError(f"Invalid list index: {key}")

        if isinstance(current, dict):
            if path[-1] not in current:
                raise KeyError(f"Key '{path[-1]}' not found")
            del current[path[-1]]
        elif isinstance(current, list):
            try:
                idx = int(path[-1])
                del current[idx]
            except (ValueError, IndexError):
                raise KeyError(f"Invalid list index: {path[-1]}")
        self.save_json()

    def format_value(self, value: Any, indent: int = 0) -> str:
        """Format value for display."""
        if isinstance(value, dict):
            lines = []
            for k, v in value.items():
                if isinstance(v, (dict, list)):
                    lines.append("  " * indent + f"{k}:")
                    lines.append(self.format_value(v, indent + 1))
                else:
                    formatted_value = v
                    if isinstance(v, (int, float)) and k in ['cost', 'amount', 'pay_rate_by_hour']:
                        formatted_value = f"{v:,.2f} AED"
                    lines.append("  " * indent + f"{k}: {formatted_value}")
            return "\n".join(lines)
        elif isinstance(value, list):
            lines = []
            for i, item in enumerate(value):
                if isinstance(item, (dict, list)):
                    lines.append("  " * indent + f"{i}:")
                    lines.append(self.format_value(item, indent + 1))
                else:
                    lines.append("  " * indent + f"{i}: {item}")
            return "\n".join(lines)
        return str(value)

def get_user_input(prompt: str, valid_options: list = None) -> str:
    """Get user input with validation."""
    try:
        value = input(prompt).strip()
        if not valid_options or value in valid_options:
            return value
        print(f"Invalid input. Please choose from: {', '.join(valid_options)}")
        return get_user_input(prompt, valid_options)
    except EOFError:
        return '4' if '4' in (valid_options or []) else 'q'  # Return exit option when EOF is encountered

def run_test_script(manager: RenovationManager, script_name: str):
    """Run predefined test scripts."""
    scripts = {
        '1': ('Kitchen Budget', ['rooms', 'kitchen', 'budget']),
        '2': ('All Rooms Overview', ['rooms']),
        '3': ('Contractor Information', ['general_considerations', 'contractor_information']),
        '4': ('Room Costs', ['rooms']),
        '5': ('Timeline Information', ['general_considerations', 'timeline']),
        '6': ('Building Management Info', ['general_considerations', 'building_management']),
    }

    if script_name not in scripts:
        print(f"Error: Test script {script_name} not found")
        return

    name, path = scripts[script_name]
    print(f"\nRunning Test Script: {name}")
    print("-" * 60)
    
    try:
        value = manager.get_nested_value(path)
        print(manager.format_value(value))
    except KeyError as e:
        print(f"Error: {e}")

def main():
    parser = argparse.ArgumentParser(description='Renovation Project Manager')
    parser.add_argument('--test', type=str, help='Run a test script')
    args = parser.parse_args()

    manager = RenovationManager('new_source.json')

    if args.test:
        run_test_script(manager, args.test)
        return

    while True:
        print("\nRenovation Project Manager")
        print("\nTest Scripts:")
        print("t1. View Kitchen Budget")
        print("t2. View All Rooms Overview")
        print("t3. View Contractor Information")
        print("t4. View Room Costs")
        print("t5. View Timeline Information")
        print("t6. View Building Management Info")
        print("\nOperations:")
        print("1. View Custom Data")
        print("2. Add/Update Data")
        print("3. Delete Data")
        print("q. Exit")
        
        try:
            choice = get_user_input("Enter your choice: ", 
                                  ['t1', 't2', 't3', 't4', 't5', 't6', '1', '2', '3', 'q'])
            
            if choice == 'q':
                break

            if choice.startswith('t'):
                run_test_script(manager, choice[1:])
                continue
                
            if choice == '1':
                # View data
                print("\nEnter path to view (e.g., 'rooms/kitchen/budget' or press Enter for root):")
                try:
                    path = input().strip()
                except EOFError:
                    break
                path = path.split('/') if path else []
                
                try:
                    value = manager.get_nested_value(path)
                    print("\nData at path:", '/'.join(path) if path else 'root')
                    print("-" * 60)
                    print(manager.format_value(value))
                except KeyError as e:
                    print(f"Error: {e}")
                
            elif choice == '2':
                # Add/Update data
                print("\nEnter path to add/update (e.g., 'rooms/kitchen/budget/amount'):")
                try:
                    path = input().strip().split('/')
                except EOFError:
                    break
                
                if not path or '' in path:
                    print("Error: Invalid path")
                    continue
                
                print("Enter new value (for JSON objects/arrays, use valid JSON format):")
                try:
                    value = input().strip()
                except EOFError:
                    break
                
                try:
                    # Try to parse as JSON if it looks like a JSON structure
                    if value.startswith('{') or value.startswith('['):
                        value = json.loads(value)
                    # Try to convert to number if it looks like one
                    elif value.replace('.', '').isdigit():
                        value = float(value) if '.' in value else int(value)
                    
                    manager.set_nested_value(path, value)
                    print(f"Successfully updated {'/'.join(path)}")
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"Error parsing value: {e}")
                except KeyError as e:
                    print(f"Error: {e}")
                
            elif choice == '3':
                # Delete data
                print("\nEnter path to delete (e.g., 'rooms/kitchen/budget/amount'):")
                try:
                    path = input().strip().split('/')
                except EOFError:
                    break
                
                if not path or '' in path:
                    print("Error: Invalid path")
                    continue
                
                try:
                    manager.delete_nested_value(path)
                    print(f"Successfully deleted {'/'.join(path)}")
                except KeyError as e:
                    print(f"Error: {e}")
                
        except Exception as e:
            print(f"Error: {str(e)}")
            logging.error(str(e))
            break

if __name__ == '__main__':
    main()
