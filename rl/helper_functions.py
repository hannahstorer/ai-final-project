import random
from playgame import make_clad, make_nibbit

ACTIONS = ['Bash', 'Defend', 'Strike', 'END']
END_TURN = 3

def state_to_key(player, enemy):
    hand_names = [c.name for c in player.deck.hand]
    return (
        max(player.hp, 0) // 16,
        player.energy,
        player.block,
        max(enemy.hp, 0) // 6,
        enemy.block,
        enemy.strength,
        enemy.move,
        hand_names.count('Strike'),
        hand_names.count('Defend'),
        hand_names.count('Bash'),
    )

