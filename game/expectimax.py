from classes import Player, Enemy, Card, Deck
from itertools import combinations
import copy
from math import comb
from collections import Counter
from playgame import enemy_move
import matplotlib.pyplot as plt
import random
import numpy as np

class Node:
    def __init__(self, player, enemies):
        self.player = player
        self.enemies = enemies
        self.line = []
        self.p = 1.0

    def is_terminal(self):
        player = self.player
        enemies = self.enemies

        if player.hp <= 0 or enemies.hp <= 0:
            return True
        else:
            return False

    def evaluate(self):
        player_hp = self.player.hp
        enemy_hp = self.enemies.hp
        if self.is_terminal():
            return 2 * player_hp

        return 2 * player_hp - enemy_hp

    def get_neighbors(self):
        if self.is_terminal():
            return None
        hand = sorted(self.player.deck.hand, key=lambda card: card.name)
        hand_size = len(hand)
        seen_hands = set()
        neighbors = []
        for i in range(hand_size+1):
            for line_indices in combinations(range(hand_size), i):
                total_cost = sum(hand[i].cost for i in line_indices)
                if total_cost == 3:
                    cards_played = tuple(sorted(line_indices))
                    if cards_played not in seen_hands:
                        seen_hands.add(cards_played)
                        neighbors.append((cards_played))

        node_neighbors = []
        for neighbor in neighbors:
            new_node = copy.deepcopy(self)
            new_node.line = [hand[i].name for i in neighbor]
            player = new_node.player
            enemies = new_node.enemies
            new_hand = sorted(player.deck.hand, key=lambda card: card.name)

            for idx in neighbor:
                card = new_hand[idx]
                card.play(player, enemy=enemies)
                if card.exhaust:
                    pile = 'exhaust_pile'
                else:
                    pile = 'discard_pile'
                player.deck.move_card(card, 'hand', pile)
            player.deck.discard_hand()
            if not new_node.is_terminal():
                enemies.start_turn()
                enemies.take_turn(player)
                player.start_turn()

            node_neighbors.append(new_node)

        return node_neighbors

    def get_chance_neighbors(self):
        deck = self.player.deck
        draw_pile = deck.draw_pile
        discard_pile = deck.discard_pile
        draw_size = 5

        draw_counts = Counter(card.name for card in draw_pile)

        if len(draw_pile) >= draw_size:
            combos = self._sample_probabilities(draw_counts, draw_size)
            fixed_counts = Counter()
            reshuffled = False
        else:
            fixed_counts = Counter(draw_counts)
            remaining_needed = draw_size - len(draw_pile)
            discard_counts = Counter(card.name for card in discard_pile)
            actual_draw = min(remaining_needed, sum(discard_counts.values()))
            combos = self._sample_probabilities(discard_counts, actual_draw)
            reshuffled = True

        node_neighbors = []
        for combo_counts, prob in combos:
            total_counts = Counter(fixed_counts)
            total_counts.update(combo_counts)

            new_node = copy.deepcopy(self)
            self._apply_draw(new_node.player.deck, total_counts, reshuffled)
            new_node.p = prob

            node_neighbors.append(new_node)

        return node_neighbors

    def _apply_draw(self, deck, counts_to_draw, reshuffled):
        remaining = Counter(counts_to_draw)

        still_in_draw = []
        for card in deck.draw_pile:
            if remaining.get(card.name, 0) > 0:
                deck.hand.append(card)
                remaining[card.name] -= 1
            else:
                still_in_draw.append(card)
        deck.draw_pile = still_in_draw

        if reshuffled:
            still_in_discard = []
            for card in deck.discard_pile:
                if remaining.get(card.name, 0) > 0:
                    deck.hand.append(card)
                    remaining[card.name] -= 1
                else:
                    still_in_discard.append(card)
            deck.draw_pile = still_in_discard 

            deck.discard_pile = []

    def _sample_probabilities(self, pool_counts, sample_size):
        names = list(pool_counts.keys())
        max_counts = [pool_counts[name] for name in names]
        N = sum(max_counts)

        if sample_size == 0 or N == 0:
            return [({}, 1.0)]

        total_ways = comb(N, sample_size)
        results = []

        self._enumerate_combos(names, pool_counts, max_counts, sample_size,
                                total_ways, 0, sample_size, [], results)

        return results

    def _enumerate_combos(self, names, pool_counts, max_counts, sample_size,
                        total_ways, idx, remaining, current_counts, results):
        if idx == len(names):
            if remaining == 0:
                ways = 1
                for name, c in zip(names, current_counts):
                    ways *= comb(pool_counts[name], c)
                prob = ways / total_ways
                combo = {names[i]: current_counts[i]
                        for i in range(len(names)) if current_counts[i] > 0}
                results.append((combo, prob))
            return

        max_c = min(max_counts[idx], remaining)
        for c in range(max_c + 1):
            current_counts.append(c)
            self._enumerate_combos(names, pool_counts, max_counts, sample_size,
                                    total_ways, idx + 1, remaining - c,
                                    current_counts, results)
            current_counts.pop()

def best_action(node, depth):
    neighbors = node.get_neighbors()
    if not neighbors:
        return None, node.evaluate()

    best_val = float('-inf')
    best_node = None
    for n in neighbors:
        val = expectimax_chance(n, depth - 1)
        if val > best_val:
            best_val = val
            best_node = n
    return best_node, best_val

def expectimax(node, depth):
    if node.is_terminal() or depth == 0:
        return node.evaluate()

    neighbors = node.get_neighbors()
    if not neighbors:
        return node.evaluate()

    return max(expectimax_chance(n, depth - 1) for n in neighbors)


def expectimax_chance(node, depth):
    if node.is_terminal() or depth == 0:
        return node.evaluate()

    chance_neighbors = node.get_chance_neighbors()
    if not chance_neighbors:
        return node.evaluate()

    return sum(child.p * expectimax(child, depth - 1) for child in chance_neighbors)


strike = Card('Strike', 1, 'Attack', [(6, 'dmg')])
defend = Card('Defend', 1, 'Skill', [(5, 'block')])
bash = Card('Bash', 2, 'Attack', [(8, 'dmg'), (2, 'vuln')])

clad_deck = Deck([strike, strike, strike, strike, strike, defend, defend, defend, defend, bash])
nibbit_moveset = [
    [(13, 'dmg')],
    [(7, 'block'),(6, 'dmg')],
    [(3, 'strength')]]

nibbit = Enemy(45, nibbit_moveset)

def play_game_expectimax(player, enemies, depth):
    game_state = Node(player, enemies)
    turn = 1
    while not game_state.is_terminal():
        player = game_state.player
        enemy = game_state.enemies
        print("Turn:", turn)
        print(f"Player HP: {player.hp}")
        print(f"Enemy HP: {enemy.hp}")
        print(f"Nibbit's next move: {enemy_move(enemy)}")
        print(f"Player draws: {[card.name for card in player.deck.hand]}")
        best_node, payoff = best_action(game_state, depth=depth)
        print("Agent plays:", best_node.line)
        print()
        game_state = best_node
        game_state.player.deck.draw(5)
        turn += 1
    return player.hp

DEPTH = 5

final_hps = []
for i in range(100):
    clad_deck = Deck([strike, strike, strike, strike, strike, defend, defend, defend, defend, bash])
    clad = Player(64, clad_deck)
    nibbit = Enemy(random.randint(44, 48), nibbit_moveset)
    clad.deck.draw(5)
    print(f"TRIAL {i+1}")
    hp = play_game_expectimax(clad, nibbit, DEPTH)
    final_hps.append(64 - hp - 6)
weights = np.ones_like(final_hps) / len(final_hps)
plt.hist(final_hps, bins=range(min(final_hps), max(final_hps) + 2), weights=weights)
plt.ylabel('Fraction of trials')
plt.xlabel('HP Loss over combat (Healing 6 HP at the end)')
plt.title('Ironclad base deck vs. Nibbit (Expectimax Agent, depth = 3 turns)')
plt.show()
print(f"Mean HP loss: {sum(final_hps)/len(final_hps)}")