import random
import json
import sys
import time

# Load game scripting from gameScripting.json
with open('gameScripting.json', 'r') as file:
    gameScripting = json.load(file)

# Load items from items.json
with open('items.json', 'r') as items_file:
    items = json.load(items_file)


# load JSON files
def loadJSON(fileName):
    # Load room data from JSON file
    with open(fileName, 'r') as file:
        fileJSON = json.load(file)
    return fileJSON


# Load character from monsters.json
with open('character.json', 'r') as file:
    characterData = json.load(file)

# Load monsters from monsters.json
with open('monsters.json', 'r') as file:
    monstersData = json.load(file)

# Load rooms from rooms.json
with open('rooms.json', 'r') as file:
    roomsData = json.load(file)

# use to store list of visited rooms, new room will print long description, visited ones print short description
_visitedRooms = set()
# use to store the previous room
_previousRoom = None
_previousRoomTemp = None
# use to store the available items of room
roomItems = {}


# Singleton Pattern (GameManager), only one in project
class GameManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.player = None
        self.boss = None
        self.currentRoom = None
        self.rooms = loadJSON('rooms.json')
        self.directions = {
            "n": "North",
            "e": "East",
            "s": "South",
            "w": "West"
        }

    def loadIntro(self):
        intro = loadJSON('intro.json')
        for state in intro:
            print("> " + state['description'])
            time.sleep(0.1)

    def startGame(self):
        print(gameScripting["_gameWelcome"])

        # load game intro
        self.loadIntro()

        # create character object
        self.player = Character.from_json('character.json')

        # Add the sword to the inventory and equip it
        sword = next(item for item in items if item["name"] == "Sword")
        self.player.addToInventory(sword)
        self.player.equipWeapon(sword["name"])

        # start at Entrance Hall
        self.currentRoom = self.rooms[0]
        self.moveToRoom()

    # the RPG game is moving between room. Player is always in a room
    def moveToRoom(self):
        global _previousRoom  # declare _previous_room as a global variable
        self.printRoomDescription()

        global roomItems

        roomItems = self.currentRoom['items']

        # main game loop
        while True:
            if self.player.getHealth() <= 0:
                print(gameScripting["_gameExiting"])
                break

            user_input = input("> ").lower()  # convert user input to lowercase

            # input inventory
            if user_input == "inventory":
                self.player.showInventory()
                print(f"Your Health: {self.player.health}")
                print("defense = ", self.player.getTotalDefense)
                self.player.printEquippedArmor()

            # input equip itemName
            elif user_input.startswith("equip "):
                item_name = user_input.split(" ", 1)[1]  # Get the item name after "equip "
                if item_name.lower() in gameScripting["armorList"]:
                    if item_name.lower() == "ring":
                        self.player.equipRing(item_name)
                    else:
                        self.player.equipArmor(item_name)
                else:
                    self.player.equipWeapon(item_name)

            # input unequip itemName
            elif user_input.startswith("unequip "):
                item_name = user_input.split(" ", 1)[1]  # Get the item name after "equip "
                if item_name.lower() in gameScripting["armorList"]:
                    if item_name.lower() == "ring":
                        self.player.unequipRing()
                    else:
                        self.player.unequipArmor(item_name)
                else:
                    self.player.unequipWeapon()

            # input consume
            elif user_input == "consume":
                self.player.consumeHealthPotion()

            # input map
            elif user_input == "map":
                print(f"\n[{self.currentRoom['name']}]")
                print(f"{self.currentRoom['description_short']}")

            # input escape
            elif user_input == "escape" and _previousRoom and self.currentRoom['id'] != 1:
                self.currentRoom, _previousRoom = _previousRoom, self.currentRoom
                global _previousRoomTemp
                if _previousRoomTemp in _visitedRooms:
                    _visitedRooms.remove(_previousRoomTemp)  # Remove room from visitedRooms if player escaped
                print("after self.current_room['name'] = ", self.currentRoom['name'])
                print("after _visitedRooms = ", _visitedRooms)
                self.printRoomDescription()

            # input direction n, s, w, e
            elif user_input in self.directions:
                direction = self.directions[user_input]
                next_room = self.getNextRoom(direction)
                if next_room:
                    _previousRoom = self.currentRoom
                    self.currentRoom = next_room
                    self.printRoomDescription()
                    # Clear unpicked items list when moving to the next room
                    if 'items' in self.currentRoom:
                        self.currentRoom['items'] = []
                else:
                    print(gameScripting["_noDirection"])

            # input fight
            elif user_input == "fight":
                if 'monsters' in self.currentRoom:
                    self.startFight()
                else:
                    print(gameScripting["_noMonsterRoom"])

            # input take
            elif user_input.startswith("take"):
                items_to_take = user_input.split(" ")[1:]
                if items_to_take:
                    for item_name in items_to_take:
                        self.takeItem(item_name)
                else:
                    self.takeAllItems()

            # input exit
            elif user_input == gameScripting["_exit"]:
                print(gameScripting["_gameExiting"])
                break

            # addition command
            # ...
            # addition command

            # the other cases
            else:
                if self.currentRoom['id'] == 1 and user_input == "escape":
                    print(gameScripting["_escapeAlert"])
                else:
                    print(gameScripting["_inputVerb"] + user_input + "\"")

    def getNextRoom(self, direction):
        for exit in self.currentRoom['exits']:
            if exit['direction'].lower() == direction.lower():
                next_room_id = exit['room_id']
                for room in self.rooms:
                    if room['id'] == next_room_id:
                        return room
        return None

    def printRoomDescription(self):
        print(f"\n[{self.currentRoom['name']}]")
        global roomItems

        roomItems = next(room for room in roomsData if room["name"] == self.currentRoom['name'])["items"]

        if self.currentRoom['name'] not in _visitedRooms:
            _visitedRooms.add(self.currentRoom['name'])
            print(f"{self.currentRoom['description']}")

            if 'monsters' in self.currentRoom:
                for monsterData in self.currentRoom['monsters']:
                    monster_name = monsterData['name']
                    print(f"Warning !!!. There is a {monster_name} in the room!")
                    if 'weapon' in monsterData:
                        weapon_name = monsterData['weapon']['name']
                        print(f"The monster is equipped with a {weapon_name}")
        else:
            print(f"{self.currentRoom['description_short']}")

        if self.player.equipped_weapon:
            print(
                f"Equipped Weapon: {self.player.equipped_weapon['name']} - Damage: {self.player.equipped_weapon['damage']}")

        print(gameScripting["_inventoryWeapon"])
        for item in self.player.inventory:
            if item.get('type') == 'weapon':
                print(f"- {item['name']} - Damage: {item['damage']}")

    def startFight(self):
        # local boolean variable _test to help detect the existence of monster in each room
        _test = False
        for monsterData in self.currentRoom['monsters']:
            _test = True
            monster_name = monsterData['name']
            # search for monster name in the room
            monster = next((m for m in monsters if m.name == monster_name), None)
            # search for monster data in monstersData JSON
            mob = next(mob for mob in monstersData if mob["name"] == monster_name)

            monster.health = mob["health"]

            if monster:

                print(f"A {monster.name} appeared! Get ready to fight!")

                print(f"Your Health: {self.player.health}")
                print(f"{monster.name}'s Health: {int(monster.health)}")

                while self.player.health > 0 and monster.health > 0:
                    print(gameScripting["_textBuffering"])
                    _monsterAttack = random.choice(monster.attacks)
                    _monsterDamage = _monsterAttack['damage']
                    print(f"{_monsterAttack['description']} and hits you for {_monsterDamage} damage.")

                    # setHealth(self, _monsterDamage)
                    self.player.setHealth(_monsterDamage)

                    if self.player.health <= 0:
                        print(f"Your Health: 0")
                        print(gameScripting["_gameDefeated"])
                        return

                    _playerDamage = self.player.getPlayerDamage()
                    print(f"You hit the {monster.name} for {_playerDamage} damage.")
                    monster.health -= (_playerDamage - monster.resistance)

                    print(f"Your Health: {self.player.health}")

                    if monster.health <= 0:
                        print(f"{monster.name}'s Health: 0")
                        print(f"Congratulations! You defeated the {monster.name}!")
                        print(gameScripting["_textBuffering"])
                        if monster.name == gameScripting["_bossName"]:
                            print(gameScripting["_gameVictory"])
                            print(gameScripting["_gameExiting"])
                            sys.exit(1)
                        print(f"{self.currentRoom['description_short']}")
                        self.printItemsAfterDefeat()

                        if self.currentRoom['name'] == gameScripting["_buffRoom"]:
                            print(gameScripting["_textMagicPower"])
                        break
                    else:
                        print(f"{monster.name}'s Health: {int(monster.health)}")

                if self.player.health > 0:
                    self.currentRoom['monsters'] = [m for m in self.currentRoom['monsters'] if
                                                    m['name'] != monster.name]
            else:
                print(f"Monster {monster_name} not found in the database.")

        if not _test:
            print(gameScripting["_noMonsterRoom"])

    def printItemsAfterDefeat(self):
        global roomItems
        print(gameScripting["_itemInRoom"])
        for item in roomItems:
            search_item = next((i for i in items if i['name'].lower() == item['name'].lower()), None)
            print(f"- {item['name']}: {search_item['description']}")

    def takeItem(self, item_name):
        global roomItems
        for item in roomItems:
            if item['name'].lower() == item_name.lower():
                self.player.addToInventory(item)
                self.roomItems.remove(item)
                print(f"You picked up {item['name']}.")
                return
        print(f"No item named {item_name} found in this room.")

    def takeAllItems(self):
        global roomItems
        for item in roomItems:
            # search for item in items
            search_item = next((i for i in items if i['name'].lower() == item['name'].lower()), None)
            self.player.addToInventory(search_item)

        roomItems = {}
        print(gameScripting["_itemPickUp"])


# character class
class Character:
    def __init__(self, name, char_class, level, experience, health, strength, dexterity, intelligence):
        self.name = name
        self.char_class = char_class
        self.level = level
        self.experience = experience
        self.health = health
        self.strength = strength
        self.dexterity = dexterity
        self.intelligence = intelligence
        self.inventory = []
        self.max_health = characterData[0]["health"] + self.level * 10
        self.equipped_weapon = None
        self.equipped_ring = None
        self.equipped_armor = {
            "helm": None,
            "armor": None,
            "pant": None,
            "glove": None,
            "belt": None,
            "ring": None,
            "boot": None
        }

    def getHealth(self):
        return self.health

    def setHealth(self, damage):
        self.health -= (damage - self.getTotalDefense)

    def addToInventory(self, item):
        self.inventory.append(item)

    def getPlayerDamage(self):
        if self.equipped_weapon:
            return self.equipped_weapon['damage'] * self.strength // 10
        else:
            return 0

    def equipWeapon(self, item_name):
        for item in self.inventory:
            if item["name"].lower() == item_name.lower():
                self.equipped_weapon = item
                print(f"Equipped {item_name}.")
                return
        print(f"You don't have a {item_name} in your inventory.")

    def unequipWeapon(self):
        print("Unequipped weapon")
        self.equipped_weapon = None

    def removeFromInventory(self, item):
        if item in self.inventory:
            self.inventory.remove(item)

    def max_health(self):
        # Use the health value from character.JSON and add the level bonus
        return self.max_health

    def showInventory(self):
        for item in self.inventory:
            print(f"- {item['name']}: {item['description']}")

        if self.equipped_weapon:
            print(f"Equipped Weapon: {self.equipped_weapon['name']} - Damage: {self.equipped_weapon['damage']}")

    def consumeHealthPotion(self):
        # Check if there is at least one Health Potion in the inventory
        health_potions = [item for item in self.inventory if item["name"] == "Health Potion"]
        if not health_potions:
            print(gameScripting["_noHealthPotion"])
            return

        # Find the "Health Potion" item and get the "health_restore" value
        health_potion = next((item for item in items if item["name"] == "Health Potion"), None)
        health_restore_value = health_potion.get("health_restore")

        # Take one Health Potion from the inventory
        health_potion = health_potions[0]
        self.inventory.remove(health_potion)

        # Restore health and ensure it doesn't exceed the max_health
        print(f"HP before consume: {self.health}")
        self.health = min(self.health + health_restore_value, characterData[0]["health"] + self.level * 10)
        print(f"HP after consume: {self.health}")

    def equipArmor(self, item_name):
        # local boolean variable to detect the non-existence items
        _test = False
        for item in self.inventory:
            if item["type"] == "armor" and item["name"].lower() == item_name.lower():
                if item["name"].lower() in self.equipped_armor:
                    self.unequipArmor(item["name"].lower())  # Unequip existing armor of the same type
                    _test = True
                self.equipped_armor[item["name"].lower()] = item
                print(f"Equipped {item_name}.")
                return
        if not _test:
            print(f"You don't have {item_name} in your inventory.")

    def unequipArmor(self, item_name):
        if item_name.lower() in self.equipped_armor and self.equipped_armor[item_name.lower()]:
            self.equipped_armor[item_name.lower()] = None
            print(f"Unequipped {item_name}.")
        # else:
        #     print(f"Y    ou don't have {item_name} equipped.")

    @property
    def getTotalDefense(self):
        total = 0
        for armor_type, item in self.equipped_armor.items():
            if item:
                total += item["defense"]
        return total

    # print all equipped_armor objects
    def printEquippedArmor(self):
        print("Equipped Armor:")
        for armor_type, item in self.equipped_armor.items():
            if item:
                print(f"- {armor_type.capitalize()}: {item['name']} - Defense: {item['defense']}")

    # equip ring
    def equipRing(self, item_name):
        for item in self.inventory:
            if item["name"].lower() == item_name.lower():
                if item_name.lower() == "ring":
                    # Apply magic buff
                    self.equipped_ring = item
                    self.health *= gameScripting['buffAmplify']
                    self.strength *= gameScripting['buffAmplify']
                    print(f"Equipped {item_name}.")
                    print(gameScripting["_ringEquip"])
                    return
        print(f"You don't have a {item_name} in your inventory.")

    # unequip ring
    def unequipRing(self):
        if self.equipped_ring:
            # remove magic buff
            self.health //= gameScripting['buffAmplify']
            self.strength //= gameScripting['buffAmplify']
            print(f"Unequipped {self.equipped_ring['name']}.")
            print(gameScripting["_ringUnEquip"])
            self.equipped_ring = None
        else:
            print(gameScripting["_ringMissing"])

    @classmethod
    def from_json(cls, filename):
        data = loadJSON(filename)[0]  # load JSON from method loadJSON(filename)
        return cls(
            data["name"],
            data["class"],
            data["level"],
            data["experience"],
            data["health"],
            data["strength"],
            data["dexterity"],
            data["intelligence"]
        )


# monster class
class Monster:
    def __init__(self, name, type, level, weakness, health, attacks, resistance):
        self.name = name
        self.type = type
        self.level = level
        self.weakness = weakness
        self.health = health
        self.attacks = attacks
        self.resistance = resistance

    def take_damage(self, damage):
        self.health -= damage
        self.health = max(0, self.health)

    def is_alive(self):
        return self.health > 0

    def __str__(self):
        return f"{self.name} ({self.type} - {self.level})"


# Create monster objects
monsters = []
for monster_data in monstersData:
    monster = Monster(
        monster_data['name'],
        monster_data['type'],
        monster_data['level'],
        monster_data['weakness'],
        monster_data['health'],
        monster_data['attacks'],
        monster_data['resistance']
    )
    monsters.append(monster)

if __name__ == "__main__":
    game_manager = GameManager.get_instance()
    game_manager.startGame()
