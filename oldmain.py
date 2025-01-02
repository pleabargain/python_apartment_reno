[Previous content remains the same until manage_misc_items function...]

def manage_misc_items():
    try:
        # Load misc items
        try:
            with open('misc_items.json', 'r') as file:
                misc_data = json.load(file)
        except FileNotFoundError:
            misc_data = {"misc_items": []}
        
        while True:
            print("\n" + "=" * 70)
            print(f"{'=== Miscellaneous Items Management ===':^70}")
            print("=" * 70)
            
            # Display current items
            if misc_data["misc_items"]:
                print("\nCurrent Items:")
                print("-" * 60)
                total_cost = 0
                for idx, item in enumerate(misc_data["misc_items"], 1):
                    print(f"{idx}. {item['description']} ({item['room']})")
                    print(f"   Cost: {item['cost']:.2f} AED | Est. Completion: {item['estimated_completion']}")
                    if item.get('notes'):
                        print(f"   Notes: {item['notes']}")
                    print("-" * 60)
                    total_cost += item['cost']
                print(f"\nTotal Misc Items Cost: {total_cost:.2f} AED")
            else:
                print("\nNo miscellaneous items added yet")
            
            print("\nOptions:")
            print("1. Add New Item")
            print("2. Edit Item")
            print("3. Remove Item")
            print("0. Back to Main Menu")
            
            choice = input("\nEnter choice (0-3): ")
            
            if choice == '0':
                break
            
            elif choice == '1':
                # Add new item
                print("\n" + "=" * 70)
                print(f"{'=== Add New Miscellaneous Item ===':^70}")
                print("=" * 70)
                
                item = {}
                item['description'] = input("Enter item description: ")
                item['room'] = input("Enter room name: ")
                
                try:
                    item['cost'] = float(input("Enter cost (AED): "))
                except ValueError:
                    print("Invalid cost. Setting to 0.0")
                    item['cost'] = 0.0
                
                item['estimated_completion'] = input("Enter estimated completion (e.g., '2 weeks'): ")
                item['notes'] = input("Enter any notes (optional): ")
                
                misc_data["misc_items"].append(item)
                print("\nItem added successfully!")
                
                # Save changes
                with open('misc_items.json', 'w') as file:
                    json.dump(misc_data, file, indent=2)
            
            elif choice == '2':
                if not misc_data["misc_items"]:
                    print("\nNo items to edit")
                    continue
                
                try:
                    idx = int(input("\nEnter item number to edit (1-{}): ".format(len(misc_data["misc_items"])))) - 1
                    if 0 <= idx < len(misc_data["misc_items"]):
                        item = misc_data["misc_items"][idx]
                        print("\nEditing item: " + item['description'])
                        print("\nLeave blank to keep current value")
                        
                        new_desc = input(f"Description [{item['description']}]: ")
                        if new_desc:
                            item['description'] = new_desc
                        
                        new_room = input(f"Room [{item['room']}]: ")
                        if new_room:
                            item['room'] = new_room
                        
                        new_cost = input(f"Cost [{item['cost']}]: ")
                        if new_cost:
                            try:
                                item['cost'] = float(new_cost)
                            except ValueError:
                                print("Invalid cost. Keeping current value")
                        
                        new_completion = input(f"Estimated completion [{item['estimated_completion']}]: ")
                        if new_completion:
                            item['estimated_completion'] = new_completion
                        
                        new_notes = input(f"Notes [{item.get('notes', '')}]: ")
                        if new_notes:
                            item['notes'] = new_notes
                        
                        print("\nItem updated successfully!")
                        
                        # Save changes
                        with open('misc_items.json', 'w') as file:
                            json.dump(misc_data, file, indent=2)
                    else:
                        print("\nInvalid item number")
                except ValueError:
                    print("\nInvalid input")
            
            elif choice == '3':
                if not misc_data["misc_items"]:
                    print("\nNo items to remove")
                    continue
                
                try:
                    idx = int(input("\nEnter item number to remove (1-{}): ".format(len(misc_data["misc_items"])))) - 1
                    if 0 <= idx < len(misc_data["misc_items"]):
                        removed = misc_data["misc_items"].pop(idx)
                        print(f"\nRemoved: {removed['description']}")
                        
                        # Save changes
                        with open('misc_items.json', 'w') as file:
                            json.dump(misc_data, file, indent=2)
                    else:
                        print("\nInvalid item number")
                except ValueError:
                    print("\nInvalid input")
            
            else:
                print("\nInvalid choice")
    
    except Exception as e:
        logging.error(f"Error managing miscellaneous items: {str(e)}")
        raise

def main():
    try:
        logging.info("Starting Apartment Renovation Manager")
        filename = 'new_source.json'
        data = load_json(filename)
        
        while True:
            print("\n" + "=" * 70)
            print(f"{'=== Apartment Renovation Manager ===':^70}")
            print("=" * 70)
            print("\n1. View/Edit Rooms")
            print("2. Manage Contractors")
            print("3. Manage Miscellaneous Items")
            print("0. Exit")
            
            choice = input("\nEnter choice (0-3): ")
            
            if choice == '0':
                save_choice = input("Would you like to save changes? (yes/no): ")
                if save_choice.lower() in ['y', 'yes']:
                    new_filename = save_json(data, filename)
                    logging.info(f"Changes saved to backup file: {new_filename} and {filename}")
                    print(f"Changes saved to: {new_filename}")
                logging.info("Exiting application")
                print("Goodbye!")
                break
            
            elif choice == '1':
                while True:
                    total_cost = display_all_room_costs(data)
                    rooms = display_rooms(data)
                    print("0. Back")
                    
                    room_choice = input("\nEnter room number (0 to go back): ")
                    
                    if room_choice == '0':
                        break
                    
                    try:
                        room_choice = int(room_choice)
                        if 1 <= room_choice <= len(rooms):
                            selected_room = rooms[room_choice - 1]
                            logging.info(f"Selected room: {selected_room}")
                            print(f"\nEditing {selected_room.replace('_', ' ').title()}")
                            edit_room_items(data['rooms'][selected_room], selected_room)
                        else:
                            print("Invalid choice. Please try again.")
                    except ValueError:
                        logging.warning("Invalid room selection input received")
                        print("Invalid input. Please enter a number.")
            
            elif choice == '2':
                manage_contractors(data)
            
            elif choice == '3':
                manage_misc_items()
            
            else:
                print("Invalid choice. Please try again.")
                
    except Exception as e:
        logging.critical(f"Critical error in main function: {str(e)}")
        print("An error occurred. Please check the log file for details.")
        raise

if __name__ == "__main__":
    main()
