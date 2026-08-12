import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / 'game'))

import matplotlib.pyplot as plt
import random
import pickle
import json
import os
from collections import defaultdict

import numpy as np
from helper_functions import ACTIONS, END_TURN, state_to_key, make_clad, make_nibbit
from playgame import enemy_move


class FightEnv:
    def __init__(self, seed = None):
        if seed is not None:
            random.seed(seed)
        self.loss_penalty = 100.0
        self.damage_reward_scale = 0.1
        self.reset()
    
    def reset(self):
        self.player = make_clad()
        self.enemy = make_nibbit()
        self.turn = 1
        self.done = False
        self.result = None
        self.player.deck.draw(5)
        return self._state()
    
    def _state(self):
        return state_to_key(self.player, self.enemy)

    def legal_actions(self):
        legal = []
        hand_names = [c.name for c in self.player.deck.hand]
        if 'Bash' in hand_names and self.player.energy >= 2:
            legal.append(0)
        if 'Defend' in hand_names and self.player.energy >= 1:
            legal.append(1)
        if 'Strike' in hand_names and self.player.energy >= 1:
            legal.append(2)
        legal.append(END_TURN)
        return legal
    
    def step(self, action):
        if self.done:
            raise RuntimeError("step called after episode ended")

        if action != END_TURN:
            card_name = ACTIONS[action]
            card = next(c for c in self.player.deck.hand if c.name == card_name)
            assert card.cost <= self.player.energy, "Not enough energy to play this card"

            enemy_hp_before = self.enemy.hp
            card.play(self.player, enemy = self.enemy)
            pile = 'exhaust_pile' if card.exhaust else 'discard_pile'
            self.player.deck.move_card(card, 'hand', pile)

            damage_dealt = max(0, enemy_hp_before - self.enemy.hp)
            reward = self.damage_reward_scale * damage_dealt

            #Enemy died -> Win Reward
            if self.enemy.hp <= 0:
                self.done = True
                self.result = 'win'
            return self._state(), reward, self.done


        # Normal Turn -> HP Loss Reward
        self.player.deck.discard_hand()
        hp_before = self.player.hp
        self.enemy.start_turn()
        self.enemy.take_turn(self.player)
        reward = -(hp_before - self.player.hp)

        #If player dies -> Loss Penalty
        if self.player.hp <= 0:
            self.done = True
            self.result = 'loss'
            reward -= self.loss_penalty
            return self._state(), reward, True

        self.turn += 1

        self.player.start_turn()
        self.player.energy = 3
        self.player.deck.draw(5)
        return self._state(), reward, self.done



def epsilon_greedy(q_row, legal, epsilon):
    if random.random() < epsilon:
        return random.choice(legal)
    best_q = max(q_row[a] for a in legal)
    best = [a for a in legal if q_row[a] == best_q]
    return random.choice(best)


def train_q_learning(env, episodes = 50000, alpha = 0.1, gamma=1.0, epsilon = 0.1):
    Q = defaultdict(lambda: np.zeros(len(ACTIONS)))
    episode_returns = []
    for ep in range(episodes):
        state = env.reset()
        legal = env.legal_actions()
        total_reward = 0.0
        done = False

        while not done:
            action = epsilon_greedy(Q[state], legal, epsilon)
            next_state, reward, done = env.step(action)
            next_legal = env.legal_actions() if not done else []

            if done:
                target = reward
            else:
                target = reward + gamma * max(Q[next_state][a] for a in next_legal)
            
            Q[state][action] += alpha * (target - Q[state][action])

            state = next_state
            legal = next_legal
            total_reward += reward
        
        episode_returns.append(total_reward)

    return Q, episode_returns

def evaluate(env, Q, episodes = 1000):
    wins = losses = 0
    hp_lost_on_wins = []
    turns = []

    for _ in range(episodes):
        env.reset()
        while not env.done:
            state = env._state()
            legal = env.legal_actions()
            q_row = Q.get(state,np.zeros(len(ACTIONS)))
            best_q = max(q_row[a] for a in legal)
            best = [a for a in legal if q_row[a] == best_q]
            action = random.choice(best)
            env.step(action)

        if env.result == 'win':
            wins += 1
            hp_lost_on_wins.append(64 - env.player.hp)
        else:
            losses += 1
        turns.append(env.turn)
    
    return {
        'win_rate' : wins / episodes,
        'mean_hp_lost_on_win': (sum(hp_lost_on_wins) / len(hp_lost_on_wins)) if hp_lost_on_wins else None,
        'mean_turns' : sum(turns) / len(turns),
    }


def hp_trace(env, Q, use_greedy=True):
    env.reset()
    hp_history = [env.player.hp]
    while not env.done:
        legal = env.legal_actions()
        if use_greedy:
            state = env._state()
            q_row = Q.get(state, np.zeros(len(ACTIONS)))
            best_q = max(q_row[a] for a in legal)
            best = [a for a in legal if q_row[a] == best_q]
            action = random.choice(best)
        else:
            action = random.choice(legal)
        env.step(action)
        if action == END_TURN or env.done:
            hp_history.append(env.player.hp)
    return hp_history, env.result


def demo_run(env, Q, n_runs=3):
    for run in range(n_runs):
        print(f"\n{'='*50}")
        print(f"DEMO FIGHT {run + 1}")
        print(f"{'='*50}")
        env.reset()
        print(f"Start: Clad HP={env.player.hp}, Nibbit HP={env.enemy.hp}")

        while not env.done:
            turn_num = env.turn
            hand_before = [c.name for c in env.player.deck.hand]
            hp_before = env.player.hp
            enemy_hp_before = env.enemy.hp
            intent_before = enemy_move(env.enemy)
            cards_played = []

            while not env.done:
                state = env._state()
                legal = env.legal_actions()
                q_row = Q.get(state, np.zeros(len(ACTIONS)))
                best_q = max(q_row[a] for a in legal)
                best = [a for a in legal if q_row[a] == best_q]
                action = random.choice(best)

                if action == END_TURN:
                    env.step(action)
                    break
                cards_played.append(ACTIONS[action])
                env.step(action)

            print(f"\n  Turn {turn_num} | Hand: {hand_before}")
            print(f"  Nibbit's next move: {intent_before}")
            print(f"  Actions: {cards_played + ['END']}")
            print(f"  Clad HP: {hp_before} -> {env.player.hp} (block {env.player.block})")
            print(f"  Nibbit HP: {enemy_hp_before} -> {env.enemy.hp}")

        print(f"\n  Result: {env.result.upper()} in {env.turn} turns, {64 - env.player.hp} HP lost")


if __name__ == "__main__":
    random.seed(0)
    env = FightEnv()

    print("Training Q-learning agent")

    Q, returns = train_q_learning(env, episodes = 50000)

    stats = evaluate(env, Q, episodes = 1000)
    print(stats)

    os.makedirs('results', exist_ok=True)

    with open('results/q_table.pkl', 'wb') as f:
        pickle.dump(dict(Q), f)
    with open ('results/metrics.json', 'w') as f:
        json.dump(stats, f, indent=2)

    print("Q-table and metrics saved to results/q_table.pkl and results/metrics.json")

    print("Random as baseline")
    random_stats = evaluate(env, defaultdict(lambda: np.zeros(len(ACTIONS))), episodes = 1000)
    print("Random:", random_stats)
    demo_run(env, Q, n_runs=3)
    window = 500
    smoothed = np.convolve(returns, np.ones(window)/window, mode='valid')
    plt.plot(smoothed)
    plt.xlabel('Episode')
    plt.ylabel(f'Smoothed Return (window={window})')
    plt.title('Q-learning Training Performance')
    plt.savefig('results/training_performance.png')
    plt.show()