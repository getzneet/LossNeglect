#!/usr/bin/python3.6
import numpy as np
import pickle

from simulation.models import QLearningAgent, AsymmetricQLearningAgent, PerseverationQLearningAgent


class Environment:

    def __init__(self, pbar=None, **kwargs):

        self.params = kwargs.copy()
        self.pbar = pbar

        self.n_sessions = kwargs.get('n_sessions')
        self.t_max = kwargs.get('t_max')

        self.cognitive_params = kwargs['cognitive_params']

        self.condition = kwargs.get('condition')
        self.n_options = kwargs.get('n_options')
        self.rewards = kwargs.get('rewards')
        self.t_when_reversal_occurs = kwargs.get('t_when_reversal_occurs')
        self.p = kwargs.get('p')

        self.n_agents = kwargs['n_agents']

        self.agent = None

    def run(self):

        data = {}

        for model in (QLearningAgent, AsymmetricQLearningAgent, PerseverationQLearningAgent):

            choices = np.zeros((self.n_agents, self.t_max), dtype=int)
            rewards = np.zeros((self.n_agents, self.t_max), dtype=int)
            correct_choices = np.zeros((self.n_agents, self.t_max), dtype=int)
            risky_choice = np.zeros((self.n_agents, self.t_max), dtype=int)
            p_softmax = np.zeros((self.n_agents, self.t_max, self.n_options), dtype=float)

            for n in range(self.n_agents):

                agent = model(
                    alpha=self.cognitive_params[model.__name__].get('alpha'),
                    beta=self.cognitive_params[model.__name__].get('beta'),
                    phi=self.cognitive_params[model.__name__].get('phi'),
                    t_max=self.t_max,
                    n_options=self.n_options,
                )

                for t in range(self.t_max):

                    if t in self.t_when_reversal_occurs:
                        self.p = self.p[::-1]
                        self.rewards = self.rewards[::-1]

                    choice = agent.choice(t)

                    # save that choice is correct or not
                    correct_choices[n, t] = \
                        sum(self.rewards[choice] * self.p[choice]) > \
                        sum(self.rewards[int(not choice)] * self.p[int(not choice)])

                    risky_choice[n, t] = -1 in self.rewards[choice]

                    reward = self.play(choice)

                    agent.save(choice=choice, t=t, reward=reward)

                    if t != self.t_max - 1:
                        agent.learn(choice=choice, t=t, reward=reward)

                    self.pbar[self.condition].update()

                # if reversal occurred at least once
                # we reinitialize probs and rewards
                if len(self.t_when_reversal_occurs):
                    self.p = np.copy(self.params['p'])
                    self.rewards = np.copy(self.params['rewards'])

                choices[n, :] = agent.memory['choices']
                rewards[n, :] = agent.memory['rewards']
                p_softmax[n, :, :] = agent.memory['p_softmax']

            d = {
                model.__name__: {
                    'choices': choices,
                    'rewards': rewards,
                    'correct_choices': correct_choices,
                    'risky_choice': risky_choice,
                    'p_softmax': p_softmax
                }
            }

            self.pbar[self.condition].close()

            data.update(d)

        self.save(data)

    def play(self, choice):

        return self.rewards[choice][np.random.choice(
            [0, 1],
            p=self.p[choice]
        )]

    def save(self, results):

        data = {
            'params': self.params,
            'condition': self.condition,
            'results': results
        }

        pickle.dump(obj=data, file=open(f'data/data_{self.condition}.p', 'wb'))


if __name__ == '__main__':
    exit('Please run the main.py script.')