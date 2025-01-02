#!/usr/bin/env python3
import argparse
import json
import logging
from datetime import datetime
import os
from typing import Dict, Any, List, Union

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

    def get_available_paths(self, current_path: List[str] = None) -> List[str]:
        """Get available paths from current position."""
        if current_path is None:
            current_path = []
            
        try:
            current = self.get_nested_value(current_path) if current_path else self.data
        except KeyError:
            return []

        paths = []
        base_path = '/'.join(current_path)
        base_path = f"{base_path}/" if base_path else ""

        if isinstance(current, dict):
            for key in current.keys():
                paths.append(f"{base_path}{key}")
                if isinstance(current[key], (dict, list)):
                    paths.extend(self.get_available_paths(current_path + [key]))
        elif isinstance(current, list):
            for i, item in enumerate(current):
                paths.append(f"{base_path}{i}")
                if isinstance(item, (dict, list)):
                    paths.extend(self.get_available_paths(current_path + [str(i)]))

        return paths

    def suggest_paths(self, partial_path: str = "") -> List[str]:
        """Suggest available paths based on partial input."""
        all_paths = self.get_available_paths()
        if not partial_path:
            return all_paths
        return [p for p in all_paths if p.startswith(partial_path)]

    def get_path_info(self, path: List[str]) -> Dict[str, Any]:
        """Get information about a path's value type and current value."""
        try:
            value = self.get_nested_value(path)
            return {
                'type': type(value).__name__,
                'current_value': value,
                'is_monetary': isinstance(value, (int, float)) and path[-1] in ['cost', 'amount', 'pay_rate_by_hour'],
                'is_list': isinstance(value, list),
                'is_dict': isinstance(value, dict)
            }
        except KeyError:
            return None

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

def show_available_paths(manager: RenovationManager, current_path: str = ""):
    """Show available paths from current position."""
    paths = manager.suggest_paths(current_path)
    if not paths:
        print("No paths available")
        return

    print("\nAvailable paths:")
    for path in paths:
        info = manager.get_path_info(path.split('/'))
        if info:
            value_type = info['type']
            if info['is_monetary']:
                value_type = 'monetary'
            print(f"  {path} ({value_type})")

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

def view_common_data(manager: RenovationManager, choice: str):
    """Handle viewing of common data sections."""
    sections = {
        'b': ('Building Management Information', ['general_considerations', 'building_management']),
        'c': ('Contractor Information', ['general_considerations', 'contractor_information']),
        't': ('Timeline Information', ['general_considerations', 'timeline']),
    }

    if choice not in sections:
        print(f"Error: Invalid section choice")
        return

    name, path = sections[choice]
    print(f"\n{name}")
    print("-" * 60)
    
    try:
        value = manager.get_nested_value(path)
        print(manager.format_value(value))
    except KeyError as e:
        print(f"Error: {e}")

def handle_add_update(manager: RenovationManager):
    """Handle adding or updating data with path suggestions."""
    print("\nAvailable paths to modify:")
    show_available_paths(manager)
    
    print("\nEnter path to add/update (e.g., 'rooms/kitchen/budget/amount'):")
    try:
        path = input().strip()
    except EOFError:
        return
    
    if not path:
        print("Error: Invalid path")
        return
        
    path_parts = path.split('/')
    path_info = manager.get_path_info(path_parts)
    
    if path_info:
        print(f"\nCurrent value ({path_info['type']}): {path_info['current_value']}")
        if path_info['is_monetary']:
            print("Enter new value (numeric amount in AED):")
        elif path_info['is_list']:
            print("Enter new value (JSON array format, e.g., [\"item1\", \"item2\"]):")
        elif path_info['is_dict']:
            print("Enter new value (JSON object format):")
        else:
            print("Enter new value:")
    else:
        print("Enter new value:")
    
    try:
        value = input().strip()
    except EOFError:
        return
    
    try:
        # Try to parse as JSON if it looks like a JSON structure
        if value.startswith('{') or value.startswith('['):
            value = json.loads(value)
        # Try to convert to number if it looks like one
        elif value.replace('.', '').isdigit():
            value = float(value) if '.' in value else int(value)
        
        manager.set_nested_value(path_parts, value)
        print(f"Successfully updated {path}")
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error parsing value: {e}")
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
        
        print("\nQuick Views:")
        print("b. Building Management Information")
        print("c. Contractor Information")
        print("t. Timeline Information")
        
        print("\nOperations:")
        print("1. View Custom Data")
        print("2. Add/Update Data")
        print("3. Delete Data")
        print("q. Exit")
        
        try:
            valid_options = ['t1', 't2', 't3', 't4', 't5', 't6', 
                           'b', 'c', 't',
                           '1', '2', '3', 'q']
            choice = get_user_input("Enter your choice: ", valid_options)
            
            if choice == 'q':
                break

            if choice.startswith('t') and len(choice) > 1:
                run_test_script(manager, choice[1:])
                continue
            
            if choice in ['b', 'c', 't']:
                view_common_data(manager, choice)
                continue
                
            if choice == '1':
                # View data
                print("\nAvailable paths to view:")
                show_available_paths(manager)
                
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
                handle_add_update(manager)
                
            elif choice == '3':
                # Delete data
                print("\nAvailable paths to delete:")
                show_available_paths(manager)
                
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
