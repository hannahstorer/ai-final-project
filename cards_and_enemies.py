from game.classes import Card, Enemy, Player

strike = Card('Strike', 1, 'Attack', [(6, 'dmg')])
defend = Card('Defend', 1, 'Skill', [(5, 'blk')])
bash = Card('Bash', 2, 'Attack', [(8, 'dmg'), (2, 'vuln')])
neutralize = Card('Neutralize', 0, 'Attack', [(3, 'dmg'), (1, 'weak')])

clad = Player(64)

nibbit_moveset = [
    [(13, 'dmg')],
    [(7, 'blk'),(6, 'dmg')],
    [(3, 'str')]]

nibbit = Enemy(45, nibbit_moveset)