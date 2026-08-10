import copy
import random
from classes import Card, Deck, Player, Enemy

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

def evaluate_outcome(player): #return remaining hp
    if player.hp <= 0:
        return -100 #give a really bad reward if player dies because living with 1hp is way better than dying and should be treated differently
    return float(player.hp)
