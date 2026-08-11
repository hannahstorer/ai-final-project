import copy
import random
from game.classes import Card, Deck, Player, Enemy
import math

def deepcopy_state(player, enemy): #deepcopy so we dont modify the original state
    return copy.deepcopy(player), copy.deepcopy(enemy)

def guess_card_shuffle(player): #shuffle the cards left so its random
    cards_left = player.deck.draw_pile + player.deck.discard_pile
    random.shuffle(cards_left)
    player.deck.draw_pile = cards_left
    player.deck.discard_pile = []

def possible_moves(player, enemy): #possible moves by card name
    if player.hp <= 0 or enemy.hp <= 0:
        return []
    moves = []
    already_added = set()
    for card in player.deck.hand:
        if card.name not in already_added:
            if player.energy >= card.cost:
                moves.append(('play', card.name))
                already_added.add(card.name)
    moves.append(('end_turn',))
    return moves

def play_move(player, enemy, move): #play possible move
    if move[0] == 'play':
        card_name = move[1]
        card = None
        for x in player.deck.hand:
            if x.name == card_name:
                card = x
                break
        card.play(player, enemy = enemy)
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

def is_fight_over(player, enemy): #check if the fight is over
    if player.hp <= 0 or enemy.hp <= 0:
        return True
    else:
        return False

def rollout_policy(player, enemy): #added rollout poilcy to give more logic behind picking cards
    available_moves = possible_moves(player, enemy)
    if len(available_moves) == 1:
        return available_moves[0]
    incoming_dmg = 0
    for value, task in enemy.moveset[enemy.move]:
        if task == 'dmg':
            incoming_dmg += value + enemy.strength
    needed_block = max(0, incoming_dmg - player.block)
    block_moves = []
    dmg_moves = []
    for move in available_moves:
        if move[0] != 'play':
            continue
        card = None
        for x in player.deck.hand:
            if x.name == move[1]:
                card = x
                break
        gives_block = False
        best_dmg_value = 0
        for value, task in card.effects:
            if task == 'block':
                gives_block = True
            if task == 'dmg':
                if value > best_dmg_value:
                    best_dmg_value = value
        if gives_block:
            block_moves.append(move)
        if best_dmg_value:
            dmg_moves.append((move, best_dmg_value))
    if needed_block > 0 and block_moves:
        return random.choice(block_moves)
    if dmg_moves:
        dmg_moves.sort(key=lambda pair: pair[1], reverse=True)
        return dmg_moves[0][0]
    return random.choice(available_moves)

def evaluate_outcome(player): #return remaining hp
    if player.hp <= 0:
        return -100 #give a really bad reward if player dies because living with 1hp is way better than dying and should be treated differently
    return float(player.hp)

class Node:
    def __init__(self, move=None, parent=None):
        self.move = move
        self.parent = parent
        self.children = {}
        self.visits = 0
        self.total_value = 0.0

    def ucb_score(self, c=1.41): #upper confidence bound and c is exploratiion constant
        if self.visits == 0:
            return float('inf')
        exploit = self.total_value / self.visits
        explore = c * math.sqrt(math.log(self.parent.visits) / self.visits)
        return exploit + explore

def ismcts_search(root_player, root_enemy, iterations=500, rollout_depth=40): #actual ismcts loop
    root = Node()
    for _ in range(iterations):
        player, enemy = deepcopy_state(root_player, root_enemy)
        guess_card_shuffle(player)
        node = root
        path = [node]
        while not is_fight_over(player, enemy): #during the fight
            available_moves = possible_moves(player, enemy)
            available_children = {}
            for x in available_moves:
                if x in node.children:
                    available_children[x] = node.children[x]
            not_tried = []
            for x in available_moves:
                if x not in node.children:
                    not_tried.append(x)
            if not_tried or not available_children: #if its not a node we can use
                break
            best_move = None
            best_score = None
            for x in available_children:
                score = available_children[x].ucb_score()
                if best_score is None or score > best_score: #update score if its better or if its the first score
                    best_score = score
                    best_move = x
            play_move(player, enemy, best_move)
            node = node.children[best_move]
            path.append(node)
        if not is_fight_over(player, enemy):
            available_moves = possible_moves(player, enemy)
            not_tried = []
            for x in available_moves:
                if x not in node.children:
                    not_tried.append(x)
            if not_tried:
                suggested = rollout_policy(player, enemy)
                if suggested in not_tried:
                    move = suggested
                else:
                    move = random.choice(not_tried)
                play_move(player, enemy, move)
                child = Node(move=move, parent=node)
                node.children[move] = child
                node = child
                path.append(node)
        depth = 0 #random rollout until fight ends because we guess shuffle (unknown info)
        while not is_fight_over(player, enemy) and depth < rollout_depth:
            move = rollout_policy(player, enemy)
            play_move(player, enemy, move)
            depth += 1
        reward = evaluate_outcome(player)
        for n in path:
            n.visits += 1
            n.total_value += reward
    if not root.children:
        return ('end_turn',), root
    best_move = None
    best_visits = None
    for x in root.children:
        visits = root.children[x].visits
        if best_visits is None or visits > best_visits: #update best visits and move if its better or first visit
            best_visits = visits
            best_move = x
    return best_move, root

def run_ismcts(player, enemy, iterations=500): #makes the output easier to use
    move, root = ismcts_search(player, enemy, iterations=iterations)
    stats = {} #move and its score
    for x in root.children:
        child = root.children[x]
        if child.visits:
            avg_value = round(child.total_value / child.visits, 3) #round to 3 decimal places if its long
        else:
            avg_value = 0
        stats[x] = (child.visits, avg_value)
    return move, stats