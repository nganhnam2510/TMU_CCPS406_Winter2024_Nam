import json

# Load room data from JSON file
with open('rooms.json', 'r') as file:
    room_data = json.load(file)

# Define a function to display room information
def display_room(room_id):
    room = room_data[room_id - 1]

    print(f"You are in the {room['name']}.")
    print(room['description'])
    print(f"The monster is : {room['monsters'][0]['name']}.")
    print("Exits:")
    for exit in room['exits']:
        print(f"- {exit['direction']}")
        print(f"- {exit['room_id']}")

# Example of displaying the entrance hall
display_room(1)