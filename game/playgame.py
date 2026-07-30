from classes import Card, Deck, Player, Enemy

#enemy's next move
def enemy_move(enemy):
    move = enemy.moveset[enemy.move]
    enemy_move_list = []
    for value, task in move:
        if task == 'dmg':
            total = value + enemy.strength
            enemy_move_list.append(f"Enemy attacks for {total}")
        elif task == 'block':
            enemy_move_list.append(f"Enemy blocks for {value}")
        elif task == 'strength':
            enemy_move_list.append(f"Enemy gains {value} strength")
        elif task in ('vuln', 'weak'):
            enemy_move_list.append(f"Apply {value} {task} to enemy")
        else:
            enemy_move_list.append(f"{task} {value}")
    return ", ".join(enemy_move_list)

#gameplay
def print_state(player,enemy):
    print("\n" + "-" * 40)
    print(f"Player HP: {player.hp}    Player Block: {player.block}   Player Energy: {player.energy}")
    print(f"Nibbit HP: {enemy.hp}    Nibbit Block: {enemy.block}    Nibbit Strength: {enemy.strength}")
    print(f"Nibbit's next move: {enemy_move(enemy)}")
    print("-" * 40)
    print("Hand:")
    for i, card in enumerate (player.deck.hand):
        print(f"{i + 1}) {card.name} (cost {card.cost}) - {card.type}")
    print("-" * 40)

def player_turn(player, enemy):
    player.start_turn()
    player.deck.draw(5)
    while True:
        if enemy.hp <= 0 or player.hp <= 0:
            return #game over player died or enemy died
        choice = input("Play a card (number) or type 'end turn' to end your turn: ").strip().lower()
        if choice == 'end turn':
            break
        if not choice.isdigit():
            print("Enter a card number or 'end turn'!")
            continue
        idx = int(choice) - 1
        if idx < 0 or idx >= len(player.deck.hand):
            print("Not valid card number")
            continue
        card = player.deck.hand[idx]
        if player.energy < card.cost: #not enough energy
            print(f"You don't have enough energy to play the card {card.name}. It costs {card.cost} energy but you only have {player.energy} energy remaining.")
            continue
        card.play(player, enemy=enemy)
        if card.exhaust:
            pile = 'exhaust_pile'
        else:
            pile = 'discard_pile'
        player.deck.move_card(card, 'hand', pile)
        print(f"Player HP: {player.hp}  Player Block: {player.block}    Player Energy: {player.energy}")
        print(f"You played the card {card.name}. Play another card or 'end turn'!")
        for i, remaining_card in enumerate(player.deck.hand):
            print(f"{i + 1}) {remaining_card.name} (cost {remaining_card.cost}) - {remaining_card.type}")
    player.deck.discard_hand()

#make the cards and put them in deck
def make_clad():
    strike = Card('Strike', 1, 'Attack', [(6, 'dmg')])
    defend = Card('Defend', 1, 'Skill', [(5, 'block')])
    bash = Card('Bash', 2, 'Attack', [(8, 'dmg'), (2, 'vuln')])
    deck = Deck([strike, defend, bash, strike, defend, bash])
    return Player(64, deck)
#make moves for nibbit enemy
def make_nibbit():
    moveset = [[(13, 'dmg')], [(7, 'block'), (6, 'dmg')], [(3, 'strength')]]
    return Enemy(45, moveset)
#registry for player characters and enemies so we can add more in the future if we have time/if we want to
CHARACTERS = {'1': ('Clad', make_clad),}
ENEMIES = {'1': ('Nibbit', make_nibbit),}
def pick_character(options):
    print("\n Choose which character to play as: ")
    for key, (name, build_character) in options.items():
        print(f"{key} {name}")
    while True:
        choice = input("Enter a number: ").strip()
        if choice in options:
            return options[choice]
        print("Invalid input, not a choice. Try again.")

def pick_enemy(options):
    print("\n Choose which enemy to fight: ")
    for key, (name, build_enemy) in options.items():
        print(f"{key} {name}")
    while True:
        choice = input("Enter a number: ").strip()
        if choice in options:
            return options[choice]
        print("Invalid input, not a choice. Try again.")

#fight logic
def run_fight():
    char_name, char_build_character = pick_character(CHARACTERS)
    enemy_name, enemy_build_enemy = pick_enemy(ENEMIES)
    clad = char_build_character()
    nibbit = enemy_build_enemy()
    print(f" You have chosen {char_name} as your character. The enemy is {enemy_name}.")
    turn = 1
    while clad.hp > 0 and nibbit.hp > 0:
        print(f"\n --------- Turn {turn} ---------")
        player_turn(clad, nibbit)
        if nibbit.hp <= 0:
            break
        nibbit.start_turn()
        nibbit.take_turn(clad)
        if clad.hp <= 0:
            break
        turn += 1
    print("\n" + "-" * 40)
    if clad.hp <= 0:
        print("You lost to Nibbit.")
    else:
        print(f"You defeated Nibbit! HP: {clad.hp}")
    print("-" * 40)

if __name__ == "__main__":
    run_fight()