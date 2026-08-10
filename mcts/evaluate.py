from game.classes import Card, Deck, Player, Enemy
from mcts.ismcts import run_ismcts, is_fight_over
import random
import math

def make_clad(): #seperate than playgame so changing menus and stuff wouldnt affect this
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

def apply_action(player, enemy, action):
    if action[0] == 'play':
        card = None
        for x in player.deck.hand:
            if x.name == action[1]:
                card = x
                break
        card.play(player, enemy=enemy)
        if card.exhaust:
            pile = 'exhaust_pile'
        else:
            pile = 'discard_pile'
        player.deck.move_card(card, 'hand', pile)
    elif action[0] == 'end_turn':
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
    while player.hp > 0 and enemy.hp > 0 and turns_taken < max_turns:
        while True:
            action = policy(player, enemy)
            apply_action(player, enemy, action)
            if action[0] == 'end_turn' or is_fight_over(player, enemy): #stop if turn is over or fight ends
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
    }

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

    print(f"\n results for {label} over {n_fights} fights")
    print(f"\n winrate: {wins}/{n_fights} ({100 * wins / n_fights:.3f}%)")
    if avg_hp_lost is not None:
        print(f"\n average hp lost in wins: {avg_hp_lost:.3f}")
    else:
        print(f"\n average hp lost in wins: n/a no wins")
    print(f"\n average turns per fight: {avg_turns:.3f}")

    return {
        'label': label,
        'n_fights': n_fights,
        'wins': wins,
        'avg_hp_lost': avg_hp_lost,
        'avg_turns': avg_turns,
        'raw_results': results,
    }

if __name__ == "__main__":
    def quick_ismcts_policy(player, enemy):
        return ismcts_policy(player, enemy, iterations=200)
    run_trials(quick_ismcts_policy, n_fights=10, label="ISMCTS (200 iterations)")