import random

class Card:
    def __init__(self, name, cost, type, effects, exhaust=False):
        self.name = name
        self.cost = cost
        self.type = type
        self.effects = effects
        self.exhaust = exhaust

    def play(self, player, enemy=None, target_cards=None):
        player.energy -= self.cost
        for effect in self.effects:
            value = effect[0]
            task = effect[1]
            player_debuffs = [x[0] for x in player.debuffs]
            if enemy != None:
                enemy_debuffs = [x[0] for x in enemy.debuffs]
            else:
                enemy_debuffs = []
            if task == 'block':
                if 'frail' in player_debuffs:
                    value = round(value * .66)
                player.gain_block(value)
            if task == 'dmg':
                if 'weak' in player_debuffs:
                    value = value * .75
                if 'vuln' in enemy_debuffs:
                    value = value * 1.5
                value = round(value)
                enemy.take_dmg(value)
            if task in ['vuln', 'weak']:
                enemy.take_debuff(task, value)
            if task == 'add_card':
                player.deck.add_card(value) #add card to deck

class Deck:
    def __init__(self, cards):
        self.draw_pile = list(cards)
        self.discard_pile = []
        self.exhaust_pile = []
        self.hand = []
        random.shuffle(self.draw_pile)

    #draws n cards from draw pile
    def draw(self, n=1):
        drawn = []
        for i in range(n):
            if not self.draw_pile:
                self.reshuffle() #reshuffles if there arent enough cards
            if self.draw_pile:
                card = self.draw_pile.pop()
                self.hand.append(card)
                drawn.append(card)
        return drawn

    #puts cards left in hand into discard pile for at the end of the turn
    def discard_hand(self):
        self.discard_pile.extend(self.hand)
        self.hand.clear()

    #moves a card between two locations
    def move_card(self, card, old_location, new_location):
        #removes card from old location
        if old_location == 'hand':
            self.hand.remove(card)
        elif old_location == 'draw_pile':
            self.draw_pile.remove(card)
        elif old_location == 'discard_pile':
            self.discard_pile.remove(card)
        elif old_location == 'exhaust_pile':
            self.exhaust_pile.remove(card)
        #adds card to new location
        if new_location == 'hand':
            self.hand.append(card)
        elif new_location == 'draw_pile':
            self.draw_pile.append(card)
        elif new_location == 'discard_pile':
            self.discard_pile.append(card)
        elif new_location == 'exhaust_pile':
            self.exhaust_pile.append(card)

    #adds a new card to a pile
    def add_card(self, card, to="discard_pile"):
        if to == 'draw_pile':
            self.draw_pile.append(card)
            random.shuffle(self.draw_pile) #shuffle so new card is in a random spot in the deck
        elif to == 'discard_pile':
            self.discard_pile.append(card)
        elif to == 'hand':
            self.hand.append(card)
        elif to == 'exhaust_pile':
            self.exhaust_pile.append(card)

    def reshuffle(self):
        #reshuffles cards by making the discard pile the new draw pile and shuffles that
        self.draw_pile = self.discard_pile
        self.discard_pile = []
        random.shuffle(self.draw_pile)


class Player:
    def __init__(self, hp, deck):
        self.hp = hp
        self.block = 0
        self.energy = 3
        self.debuffs = []
        self.deck = deck

    def start_turn(self):
        self.block = 0
        self.energy = 3
        for debuff in self.debuffs[:]: #[:] makes a copy so it doesnt skip after remove
            debuff[1] -= 1
            if debuff[1] <= 0:
                self.debuffs.remove(debuff)

    def gain_block(self, value):
        self.block += value

    def take_dmg(self, value):
        if self.block >= value:
            self.block -= value
        else:
            self.hp += self.block - value
            self.block = 0

    def take_debuff(self, debuff, value):
            active_debuffs = [x[0] for x in self.debuffs]
            if debuff in active_debuffs:
                index = active_debuffs.index(debuff)
                self.debuffs[index][1] += value
            else:
                self.debuffs.append([debuff, value])

class Enemy:
    def __init__(self, hp, moveset, init_move=0):
        self.hp = hp
        self.block = 0
        self.moveset = moveset
        self.debuffs = []
        self.strength = 0
        self.move = init_move

    def start_turn(self):
        self.block = 0
        for debuff in self.debuffs[:]:
            debuff[1] -= 1
            if debuff[1] <= 0:
                self.debuffs.remove(debuff)

    def take_turn(self, player):
        active_move = self.moveset[self.move]
        for effect in active_move:
            value = effect[0]
            task = effect[1]
            player_debuffs = [x[0] for x in player.debuffs]
            enemy_debuffs = [x[0] for x in self.debuffs]
            if task == 'block':
                self.block += value
            if task == 'strength':
                self.strength += value
            if task == 'dmg':
                value += self.strength
                if 'weak' in enemy_debuffs:
                    value = value * .75
                if 'vuln' in player_debuffs:
                    value = value * 1.5
                value = round(value)
                player.take_dmg(value)
            if task in ['vuln', 'weak']:
                player.take_debuff(task, value)
            if task == 'add_card':
                player.deck.add_card(value) #enemy can add a card

        # change intent to next move
        self.move += 1
        if self.move == len(self.moveset):
            self.move = 0

    def take_dmg(self, value):
        if self.block >= value:
            self.block -= value
        else:
            self.hp += self.block - value
            self.block = 0

    def take_debuff(self, debuff, value):
        active_debuffs = [x[0] for x in self.debuffs]
        if debuff in active_debuffs:
            index = active_debuffs.index(debuff)
            self.debuffs[index][1] += value
        else:
            self.debuffs.append([debuff, value])

strike = Card('Strike', 1, 'Attack', [(6, 'dmg')])
defend = Card('Defend', 1, 'Skill', [(5, 'block')])
bash = Card('Bash', 2, 'Attack', [(8, 'dmg'), (2, 'vuln')])

clad_deck = Deck([strike, defend, bash, strike, defend, bash])
clad = Player(64, clad_deck)

nibbit_moveset = [
    [(13, 'dmg')],
    [(7, 'block'),(6, 'dmg')],
    [(3, 'strength')]]

nibbit = Enemy(45, nibbit_moveset)

def main():
    for i in range(6):
        nibbit.take_turn(clad)
        print(f'Turn: {i}')
        print(f'Clad hp: {clad.hp}')
        print(f'Nibbit block: {nibbit.block}')
        print(f'Nibbit strength: {nibbit.strength}')

main()