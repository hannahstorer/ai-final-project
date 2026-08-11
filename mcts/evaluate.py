from game.classes import Card, Deck, Player, Enemy
from mcts.ismcts import run_ismcts, is_fight_over, possible_moves
import random
import matplotlib.pyplot as plt

def enemy_move(enemy): #playgame enemy_move but for mcts so it prints the full game
    move = enemy.moveset[enemy.move]
    parts = []
    for value, task in move:
        if task == 'dmg':
            total = value + enemy.strength
            parts.append(f"Enemy attacks for {total}")
        elif task == 'block':
            parts.append(f"Enemy blocks for {value}")
        elif task == 'strength':
            parts.append(f"Enemy gains {value} strength")
        elif task in ('vuln', 'weak'):
            parts.append(f"Apply {value} {task} to enemy")
        else:
            parts.append(f"{task} {value}")
    return ", ".join(parts)

def make_clad(): #seperate than playgame so changing menus and stuff wont affect this
    strike = Card('Strike', 1, 'Attack', [(6, 'dmg')])
    defend = Card('Defend', 1, 'Skill', [(5, 'block')])
    bash = Card('Bash', 2, 'Attack', [(8, 'dmg'), (2, 'vuln')])
    deck = Deck([strike, strike, strike, strike, defend, defend, defend, defend, bash])
    return Player(64, deck, name='Clad')

def make_nibbit():
    moveset = [[(13, 'dmg')], [(7, 'dmg'), (6, 'block')], [(3, 'strength')]]
    hp = random.randint(44, 48)
    return Enemy(hp, moveset, name='Nibbit')

def ismcts_policy(player, enemy, iterations=300):
    action, stats = run_ismcts(player, enemy, iterations=iterations)
    return action

def random_policy(player, enemy):
    moves = possible_moves(player, enemy)
    return random.choice(moves)

def play_move(player, enemy, move):
    if move[0] == 'play':
        card = None
        for x in player.deck.hand:
            if x.name == move[1]:
                card = x
                break
        card.play(player, enemy=enemy)
        if card.exhaust:
            pile = 'exhaust_pile'
        else:
            pile = 'discard_pile'
        player.deck.move_card(card, 'hand', pile)
    elif move[0] == 'end_turn':
        player.deck.discard_hand()
        if enemy.hp > 0:
            enemy.start_turn()
            enemy.take_turn(player)
        if player.hp > 0 and enemy.hp > 0:
            player.start_turn()
            player.deck.draw(5)

def run_one_fight(policy, max_turns=30):
    player = make_clad()
    enemy = make_nibbit()
    starting_hp = player.hp
    player.start_turn()
    player.deck.draw(5)
    turns_taken = 0
    trees_tested = 0
    while player.hp > 0 and enemy.hp > 0 and turns_taken < max_turns:
        while True:
            move = policy(player, enemy)
            trees_tested += 1
            play_move(player, enemy, move)
            if move[0] == 'end_turn' or is_fight_over(player, enemy): #stop if turn is over or fight ends
                break
        turns_taken += 1
    won = enemy.hp <= 0 and player.hp > 0
    hp_lost = max(0, starting_hp - player.hp)
    return {
        'won': won,
        'hp_lost': hp_lost,
        'final_player_hp': player.hp,
        'final_enemy_hp': enemy.hp,
        'turns_taken': turns_taken,
        'trees_tested' : trees_tested,
    }

def run_text_fight(iterations=300, max_turns=30): #runs a fight with log of actions and prints final move sequence and stats
    player = make_clad()
    enemy = make_nibbit()
    player.start_turn()
    player.deck.draw(5)
    moves_taken = []
    log = []
    turn = 1
    while not is_fight_over(player, enemy) and turn <= max_turns:
        log.append(f"\n ----- turn {turn} ----- ")
        log.append(f"\n player HP: {player.hp}  player block: {player.block}   player energy: {player.energy}")
        log.append(f"\n enemy HP: {enemy.hp}    enemy block: {enemy.block}  enemy strength: {enemy.strength}")
        log.append(f"\n enemy's next move: {enemy_move(enemy)}")
        log.append(f"\n hand: {[x.name for x in player.deck.hand]}")

        while True:
            move, stats = run_ismcts(player, enemy, iterations=iterations)
            log.append(f" moves considered: {stats}")
            log.append(f" move chosen: {move}")
            moves_taken.append(move)
            play_move(player, enemy, move)
            if move[0] == 'end_turn' or is_fight_over(player, enemy):
                break
        turn += 1
    print("\n ----- full move sequence ----- ")
    for x, move in enumerate(moves_taken):
        print(f" {x + 1}) {move}")
    print("\n ----- full gameplay ----- ")
    for line in log:
        print(line)
    print("\n ----- fight over ----- ")
    print(f"\n final player HP: {player.hp}")
    print(f"\n final enemy HP: {enemy.hp}")
    if enemy.hp <= 0 and player.hp > 0:
        print("\n result: WIN")
    else:
        print("\n result: LOSS")

def run_trials(policy, n_fights=20, label="policy"):
    results = []
    for _ in range(n_fights):
        results.append(run_one_fight(policy))
    wins = 0
    for x in results:
        if x['won']:
            wins += 1
    hp_losses = []
    for x in results:
        if x['won']:
            hp_losses.append(x['hp_lost'])
    if hp_losses:
        avg_hp_lost = sum(hp_losses) / len(hp_losses)
    else:
        avg_hp_lost = None
    total_turns = 0
    for x in results:
        total_turns += x['turns_taken']
    avg_turns = total_turns / len(results)
    total_trees_tested = 0
    for x in results:
        total_trees_tested += x['trees_tested']

    print(f"\n results for {label} over {n_fights} fights")
    print(f"\n winrate: {wins}/{n_fights} ({100 * wins / n_fights:.3f}%)")
    if avg_hp_lost is not None:
        print(f"\n average hp lost in wins: {avg_hp_lost:.3f}")
    else:
        print(f"\n average hp lost in wins: n/a no wins")
    print(f"\n average turns per fight: {avg_turns:.3f}")
    print(f"\n tested {total_trees_tested} trees total ({total_trees_tested / n_fights:.3f}) per fight")

    return {
        'label': label,
        'n_fights': n_fights,
        'wins': wins,
        'avg_hp_lost': avg_hp_lost,
        'avg_turns': avg_turns,
        'total_trees_tested': total_trees_tested,
        'raw_results': results,
    }

def plot_hp_histogram(trial_results, filename="mcts_histogram.png"):
    final_hps = []
    for x in trial_results['raw_results']:
        final_hps.append(max(0, x['final_player_hp']))
    plt.figure()
    plt.hist(final_hps, bins=10, edgecolor='black')
    plt.xlabel('Final Player HP')
    plt.ylabel('Number of Fights')
    plt.title(f"Final HP Distribution Over 1000 Games - {trial_results['label']}")
    plt.savefig(filename)
    plt.close()
    print(f"saved histogram to {filename}")

def plot_hp_comparison(trial_results_list, filename="hp_comparison.png"):
    plt.figure()
    for trial_results in trial_results_list:
        final_hps = []
        for x in trial_results['raw_results']:
            final_hps.append(max(0, x['final_player_hp']))
        plt.hist(final_hps, bins=10, alpha=0.5, edgecolor='black', label=trial_results['label'])
    plt.xlabel('Final Player HP')
    plt.ylabel('Number of Fights')
    plt.title('Final HP Distribution Comparison')
    plt.legend()
    plt.savefig(filename)
    plt.close()
    print(f"Saved comparison histogram to {filename}")

def compare_ismcts_vs_random(n_fights=1000, iterations=150):
    def quick_ismcts_policy(player, enemy):
        return ismcts_policy(player, enemy, iterations=iterations)
    print(f" --- running ISMCTS for {n_fights} fights --- ")
    ismcts_results = run_trials(quick_ismcts_policy, n_fights=n_fights, label=f"ISMCTS ({iterations} iterations)")
    print(f"\n --- running random baseline for {n_fights} fights --- ")
    random_results = run_trials(random_policy, n_fights=n_fights, label="Random baseline")
    plot_hp_comparison([ismcts_results, random_results], filename="hp_comparison.png")
    return ismcts_results, random_results

if __name__ == "__main__":
    def quick_ismcts_policy(player, enemy):
        return ismcts_policy(player, enemy, iterations=200)
    #pick which one to run 
    #the first is no text explanation and just end stats and second is all of it with full gameplay
    #run_trials(quick_ismcts_policy, n_fights=10, label="ISMCTS (200 iterations)")
    run_text_fight(iterations=200)