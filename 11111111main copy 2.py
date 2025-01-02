#!/usr/bin/env python3
import argparse
import json
import logging
from datetime import datetime
import os
from typing import Dict, Any, List, Union, Tuple

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

def show_room_menu(manager: RenovationManager) -> List[str]:
    """Show simplified room menu."""
    rooms = manager.get_nested_value(['rooms'])
    print("\nSelect Room:")
    print("-" * 40)
    for i, room_name in enumerate(rooms.keys(), 1):
        budget = rooms[room_name].get('budget', {}).get('amount', 0)
        print(f"{i}. {room_name.replace('_', ' ').title()} (Budget: {budget:,.2f} AED)")
    return list(rooms.keys())

def show_room_details(manager: RenovationManager, room_name: str) -> List[Tuple[str, Dict]]:
    """Show details for a specific room."""
    room_data = manager.get_nested_value(['rooms', room_name])
    sections = []
    
    print(f"\nSections in {room_name.replace('_', ' ').title()}:")
    print("-" * 60)
    
    # Show budget first if exists
    if 'budget' in room_data:
        budget = room_data['budget']
        print(f"1. Budget")
        print("   {")
        print(f"     'amount': {budget.get('amount', 0):,.2f} AED,")
        print(f"     'notes': '{budget.get('notes', '')}',")
        if 'attachments' in budget:
            print("     'attachments': [")
            for attachment in budget.get('attachments', []):
                print(f"       '{attachment}',")
            print("     ]")
        print("   }")
        sections.append(('budget', budget))
        print()
    
    # Then show other sections with their content
    section_num = len(sections) + 1
    for key, value in room_data.items():
        if isinstance(value, dict) and key != 'budget':
            sections.append((key, value))
            print(f"{section_num}. {key.replace('_', ' ').title()}")
            print("   {")
            
            # Show the actual content
            for k, v in value.items():
                if isinstance(v, (dict, list)):
                    print(f"     '{k}': {json.dumps(v, indent=2).replace('{', '{\n').replace('}', '\n     }')},")
                elif isinstance(v, (int, float)) and k in ['cost', 'amount', 'pay_rate_by_hour']:
                    print(f"     '{k}': {v:,.2f} AED,")
                else:
                    print(f"     '{k}': {json.dumps(v)},")
            print("   }")
            print()
            section_num += 1
    
    return sections

def handle_add_update(manager: RenovationManager):
    """Handle adding or updating data with simplified navigation."""
    # Show room menu
    room_names = show_room_menu(manager)
    
    print("\nEnter room number:")
    try:
        room_index = int(input().strip()) - 1
        if not (0 <= room_index < len(room_names)):
            print("Invalid room number")
            return
    except (ValueError, EOFError):
        return

    room_name = room_names[room_index]
    sections = show_room_details(manager, room_name)
    
    print("\nEnter section number to edit:")
    try:
        section_index = int(input().strip()) - 1
        if not (0 <= section_index < len(sections)):
            print("Invalid section number")
            return
    except (ValueError, EOFError):
        return

    section_name, current_value = sections[section_index]
    print(f"\nCurrent {section_name.replace('_', ' ').title()} data:")
    print(json.dumps(current_value, indent=2))
    
    print("\nEnter new values (JSON format):")
    try:
        value = input().strip()
        if not value:
            return
        
        new_value = json.loads(value)
        path_parts = ['rooms', room_name, section_name]
        manager.set_nested_value(path_parts, new_value)
        print(f"\nSuccessfully updated {section_name}")
        
        # Show the updated section
        print("\nUpdated values:")
        print(json.dumps(new_value, indent=2))
        
    except json.JSONDecodeError:
        print("Error: Invalid JSON format")
    except Exception as e:
        print(f"Error: {str(e)}")

def run_test_script(manager: RenovationManager, script_name: str):
    """Run predefined test scripts."""
    scripts = {
        '1': ('Kitchen Budget', ['rooms', 'kitchen', 'budget']),
        '2': ('All Rooms Overview', ['rooms']),
        '3': ('Contractor Information', ['general_considerations', 'contractor_information']),
        '4': ('Room Costs', ['rooms']),
        '5': ('Timeline Information', ['general_considerations', 'timeline']),
        '6': ('Building Management Info', ['general_considerations', 'building_management']),
        '7': ('Room Cost Report', None),
    }

    if script_name not in scripts:
        print(f"Error: Test script {script_name} not found")
        return

    name, path = scripts[script_name]
    print(f"\nRunning Test Script: {name}")
    print("-" * 60)
    
    if script_name == '7':
        print(generate_cost_report(manager))
    else:
        try:
            value = manager.get_nested_value(path)
            print(manager.format_value(value))
        except KeyError as e:
            print(f"Error: {e}")

def process_contractor_group(group_name: str, contractors_data: Dict, md_content: List[str]) -> Tuple[float, List[str]]:
    """Process a group of contractors and return their total cost and updated markdown content."""
    group_total = 0
    for contractor_id, contractor in contractors_data.items():
        if 'cost' in contractor and contractor['cost']:
            cost = contractor['cost']
            md_content.append(f"| {contractor['name']} ({group_name}) | Fixed Cost | {cost:,.2f} |\n")
            group_total += cost
        elif 'pay_rate_by_hour' in contractor and contractor['pay_rate_by_hour']:
            rate = contractor['pay_rate_by_hour']
            md_content.append(f"| {contractor['name']} ({group_name}) | Hourly Rate | {rate:,.2f} |\n")
    return group_total, md_content

def create_attachment_placeholders(manager: RenovationManager):
    """Create directories and placeholder files for attachments."""
    rooms = manager.get_nested_value(['rooms'])
    
    for room_name, room_data in rooms.items():
        # Create room directory if it doesn't exist
        if not os.path.exists(room_name):
            os.makedirs(room_name)
            
        # Process each section in the room
        for section_name, section_data in room_data.items():
            if isinstance(section_data, dict):
                # Handle direct attachments in the section
                if 'attachments' in section_data:
                    for attachment in section_data['attachments']:
                        filepath = os.path.join(room_name, attachment)
                        if not os.path.exists(filepath):
                            with open(filepath, 'w') as f:
                                f.write(f"Placeholder for {attachment}\n")
                
                # Handle nested attachments
                for key, value in section_data.items():
                    if isinstance(value, dict) and 'attachments' in value:
                        for attachment in value['attachments']:
                            filepath = os.path.join(room_name, attachment)
                            if not os.path.exists(filepath):
                                with open(filepath, 'w') as f:
                                    f.write(f"Placeholder for {attachment}\n")

def generate_cost_report(manager: RenovationManager, export: bool = False) -> str:
    """Generate a markdown formatted cost report for all rooms and contractors."""
    try:
        rooms = manager.get_nested_value(['rooms'])
        contractors = manager.get_nested_value(['general_considerations', 'contractor_information'])
        
        # Initialize the markdown content as a list for better memory management
        md_content = ["# Renovation Cost Report\n\n"]
    
        # Track totals
        total_costs = {}
        room_totals = {}
        contractor_totals = {}
    
        # Ensure attachment placeholders are created
        create_attachment_placeholders(manager)
        
        # Process each room
        md_content.append("## Room Costs\n\n")
        for room_name, room_data in rooms.items():
            room_total = 0
            md_content.append(f"### {room_name.replace('_', ' ').title()}\n\n")
            md_content.append("| Item | Cost (AED) |\n|------|------------|\n")
            
            for section_name, section_data in room_data.items():
                if isinstance(section_data, dict):
                    # Add section with cost if available
                    if 'cost' in section_data:
                        cost = section_data['cost']
                        section_title = section_name.replace('_', ' ').title()
                        
                        # Add attachments if present
                        if 'attachments' in section_data:
                            attachments = [f"[{att}]({room_name}/{att})" for att in section_data['attachments']]
                            section_title += f" ({', '.join(attachments)})"
                        
                        md_content.append(f"| {section_title} | {cost:,.2f} |\n")
                        room_total += cost
                        
                        # Track item totals across rooms
                        if section_name not in total_costs:
                            total_costs[section_name] = 0
                        total_costs[section_name] += cost
                    
                    # Handle nested items with costs
                    for key, value in section_data.items():
                        if isinstance(value, dict) and 'cost' in value:
                            cost = value['cost']
                            if cost > 0:  # Only show items with actual costs
                                item_title = f"{section_name.replace('_', ' ').title()} - {key.replace('_', ' ').title()}"
                                
                                # Add attachments if present
                                if 'attachments' in value:
                                    attachments = [f"[{att}]({room_name}/{att})" for att in value['attachments']]
                                    item_title += f" ({', '.join(attachments)})"
                                
                                md_content.append(f"| {item_title} | {cost:,.2f} |\n")
                                room_total += cost
                                
                                # Track item totals
                                item_key = f"{section_name}_{key}"
                                if item_key not in total_costs:
                                    total_costs[item_key] = 0
                                total_costs[item_key] += cost
            
            room_totals[room_name] = room_total
            md_content.append(f"| **Room Total** | **{room_total:,.2f}** |\n\n")
        
        # Process contractor costs
        md_content.append("## Contractor Costs\n\n")
        md_content.append("| Contractor | Cost Type | Rate/Cost (AED) |\n|------------|------------|---------------|\n")
        
        # Process each contractor group
        for group_name, group_data in contractors.items():
            if isinstance(group_data, dict):
                if group_name == 'general_contractor':
                    total, md_content = process_contractor_group('General', {'main': group_data}, md_content)
                    contractor_totals['General Contractor'] = total
                elif isinstance(group_data, dict):
                    total, md_content = process_contractor_group(group_name.replace('_', ' ').title(), group_data, md_content)
                    if total > 0:
                        contractor_totals[group_name.replace('_', ' ').title()] = total
        
        # Add summary sections
        md_content.append("\n## Summary\n\n")
        
        # Room totals
        md_content.append("### Room Totals\n\n")
        md_content.append("| Room | Total Cost (AED) |\n|------|----------------|\n")
        room_grand_total = 0
        for room_name, total in room_totals.items():
            md_content.append(f"| {room_name.replace('_', ' ').title()} | {total:,.2f} |\n")
            room_grand_total += total
        md_content.append(f"| **Total Room Costs** | **{room_grand_total:,.2f}** |\n\n")
        
        # Contractor totals
        md_content.append("### Contractor Totals (Fixed Costs Only)\n\n")
        md_content.append("| Contractor Type | Total Cost (AED) |\n|-----------------|----------------|\n")
        contractor_grand_total = 0
        for contractor_type, total in contractor_totals.items():
            md_content.append(f"| {contractor_type} | {total:,.2f} |\n")
            contractor_grand_total += total
        md_content.append(f"| **Total Contractor Costs** | **{contractor_grand_total:,.2f}** |\n\n")
        
        # Overall total
        md_content.append("### Project Totals\n\n")
        md_content.append("| Category | Total Cost (AED) |\n|-----------|----------------|\n")
        md_content.append(f"| Room Costs | {room_grand_total:,.2f} |\n")
        md_content.append(f"| Contractor Costs | {contractor_grand_total:,.2f} |\n")
        md_content.append(f"| **Project Total** | **{(room_grand_total + contractor_grand_total):,.2f}** |\n\n")
        
        # Costs by item type
        md_content.append("### Room Costs by Item Type\n\n")
        md_content.append("| Item Type | Total Cost (AED) |\n|-----------|----------------|\n")
        for item_name, total in total_costs.items():
            md_content.append(f"| {item_name.replace('_', ' ').title()} | {total:,.2f} |\n")
        
        # Join all content into a single string
        final_content = ''.join(md_content)
        
        if export:
            with open('total_cost.md', 'w') as f:
                f.write(final_content)
            print("\nCost report exported to total_cost.md")
        
        return final_content
    except Exception as e:
        logging.error(f"Error generating cost report: {str(e)}")
        return f"Error generating cost report: {str(e)}"

def view_common_data(manager: RenovationManager, choice: str):
    """Handle viewing of common data sections."""
    sections = {
        'b': ('Building Management Information', ['general_considerations', 'building_management']),
        'c': ('Contractor Information', ['general_considerations', 'contractor_information']),
        't': ('Timeline Information', ['general_considerations', 'timeline']),
        'r': ('Room Cost Report', None),
    }

    if choice not in sections:
        print(f"Error: Invalid section choice")
        return

    name, path = sections[choice]
    print(f"\n{name}")
    print("-" * 60)
    
    if choice == 'r':
        print(generate_cost_report(manager))
        export = input("\nWould you like to export this report to total_cost.md? (y/n): ").lower() == 'y'
        if export:
            generate_cost_report(manager, export=True)
    else:
        try:
            value = manager.get_nested_value(path)
            print(manager.format_value(value))
        except KeyError as e:
            print(f"Error: {e}")

def main():
    parser = argparse.ArgumentParser(description='Renovation Project Manager')
    parser.add_argument('--test', type=str, help='Run a test script')
    parser.add_argument('--room', type=str, help='View room details (guest_bathroom, kitchen, living_room, master_bedroom)')
    parser.add_argument('--section', type=str, help='View specific section in room (budget, lighting, etc.)')
    parser.add_argument('--contractors', action='store_true', help='View contractor information')
    parser.add_argument('--timeline', action='store_true', help='View timeline information')
    parser.add_argument('--management', action='store_true', help='View building management information')
    args = parser.parse_args()

    manager = RenovationManager('new_source.json')

    # Handle command line options
    if args.contractors:
        view_common_data(manager, 'c')
        return
    elif args.timeline:
        view_common_data(manager, 't')
        return
    elif args.management:
        view_common_data(manager, 'b')
        return
    elif args.room:
        try:
            if args.section:
                value = manager.get_nested_value(['rooms', args.room, args.section])
                print(f"\n{args.room.replace('_', ' ').title()} - {args.section.replace('_', ' ').title()}:")
                print("-" * 60)
                print(manager.format_value(value))
            else:
                value = manager.get_nested_value(['rooms', args.room])
                print(f"\n{args.room.replace('_', ' ').title()} Details:")
                print("-" * 60)
                print(manager.format_value(value))
        except KeyError as e:
            print(f"Error: {e}")
        return
    elif args.test:
        run_test_script(manager, args.test)
        return

    # Interactive mode
    while True:
        print("\nRenovation Project Manager")
        print("\nTest Scripts:")
        print("t1. View Kitchen Budget")
        print("t2. View All Rooms Overview")
        print("t3. View Contractor Information")
        print("t4. View Room Costs")
        print("t5. View Timeline Information")
        print("t6. View Building Management Info")
        print("t7. View Room Cost Report")
        
        print("\nQuick Views:")
        print("b. Building Management Information")
        print("c. Contractor Information")
        print("t. Timeline Information")
        print("r. Room Cost Report")
        
        print("\nOperations:")
        print("1. View Custom Data")
        print("2. Add/Update Data")
        print("3. Delete Data")
        print("q. Exit")
        
        print("\nCommand Line Examples:")
        print("python main.py --room kitchen --section budget")
        print("python main.py --contractors")
        print("python main.py --timeline")
        print("python main.py --management")
        
        try:
            valid_options = ['t1', 't2', 't3', 't4', 't5', 't6', 't7',
                           'b', 'c', 't', 'r',
                           '1', '2', '3', 'q']
            choice = get_user_input("Enter your choice: ", valid_options)
            
            if choice == 'q':
                break

            if choice.startswith('t') and len(choice) > 1:
                run_test_script(manager, choice[1:])
                continue
            
            if choice in ['b', 'c', 't', 'r']:
                view_common_data(manager, choice)
                continue
                
            if choice == '1':
                # View data
                room_names = show_room_menu(manager)
                
                print("\nEnter room number:")
                try:
                    room_index = int(input().strip()) - 1
                    if 0 <= room_index < len(room_names):
                        room_name = room_names[room_index]
                        sections = show_room_details(manager, room_name)
                    else:
                        print("Invalid room number")
                        continue
                except (ValueError, EOFError):
                    break
                
            elif choice == '2':
                handle_add_update(manager)
                
            elif choice == '3':
                # Delete data
                room_names = show_room_menu(manager)
                
                print("\nEnter room number:")
                try:
                    room_index = int(input().strip()) - 1
                    if not (0 <= room_index < len(room_names)):
                        print("Invalid room number")
                        continue
                except (ValueError, EOFError):
                    break

                room_name = room_names[room_index]
                sections = show_room_details(manager, room_name)
                
                print("\nEnter section number to delete:")
                try:
                    section_index = int(input().strip()) - 1
                    if not (0 <= section_index < len(sections)):
                        print("Invalid section number")
                        continue
                except (ValueError, EOFError):
                    break

                section_name, _ = sections[section_index]
                path_parts = ['rooms', room_name, section_name]
                
                try:
                    manager.delete_nested_value(path_parts)
                    print(f"Successfully deleted {section_name}")
                except KeyError as e:
                    print(f"Error: {e}")
                
        except Exception as e:
            print(f"Error: {str(e)}")
            logging.error(str(e))
            break

if __name__ == '__main__':
    main()
