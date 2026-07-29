class Card:
    def __init__(self, name, cost, type, effects):
        self.name = name
        self.cost = cost
        self.type = type
        self.effects = effects

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
            if task == 'blk':
                if 'frail' in player.debuffs:
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


class Player:
    def __init__(self, hp):
        self.hp = hp
        self.block = 0
        self.energy = 3
        self.debuffs = []

    def start_turn(self):
        self.block = 0
        self.energy = 3
        for debuff in self.debuffs:
            debuff[1] -= 1
            if debuff[1] == 0:
                self.debuffs.pop(debuff)

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
        self.str = 0
        self.move = init_move

    def start_turn(self):
        self.block = 0
        for debuff in self.debuffs:
            debuff[1] -= 1
            if debuff[1] == 0:
                self.debuff.pop(debuff)

    def take_turn(self, player):
        active_move = self.moveset[self.move]
        for effect in active_move:
            value = effect[0]
            task = effect[1]
            player_debuffs = [x[0] for x in player.debuffs]
            enemy_debuffs = [x[0] for x in self.debuffs]
            if task == 'blk':
                self.block += value
            if task == 'str':
                self.str += value
            if task == 'dmg':
                value += self.str
                if 'weak' in enemy_debuffs:
                    value = value * .75
                if 'vuln' in player_debuffs:
                    value = value * 1.5
                value = round(value)
                player.take_dmg(value)
            if task in ['vuln', 'weak']:
                player.take_debuff(task, value)

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
defend = Card('Defend', 1, 'Skill', [(5, 'blk')])
bash = Card('Bash', 2, 'Attack', [(8, 'dmg'), (2, 'vuln')])

clad = Player(70)

nibbit_moveset = [
    [(13, 'dmg')],
    [(7, 'blk'),(6, 'dmg')],
    [(3, 'str')]]

nibbit = Enemy(45, nibbit_moveset)

def main():
    for i in range(6):
        nibbit.take_turn(clad)
        print(f'Turn: {i}')
        print(f'Clad hp: {clad.hp}')
        print(f'Nibbit block: {nibbit.block}')
        print(f'Nibbit str: {nibbit.str}')

main()