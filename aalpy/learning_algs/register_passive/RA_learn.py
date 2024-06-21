import time
from bisect import insort
from typing import Union
import logging
import copy

from aalpy.automata import RegisterState, RegisterAutomata
from aalpy.learning_algs.register_passive.RA_helper_functions import prefixes, read_word, is_similar

completable_logger = logging.getLogger('completable')
transition_logger = logging.getLogger('transition')
learner_logger = logging.getLogger('learner')
refine_logger = logging.getLogger('refine')

"""
    Data of form: List of (<string>, <boolean>)
"""


class RA_passive:
    def __init__(self, data, print_info=True):
        self.to_read, self.S_plus, self.S_minus = prefixes(data)
        self.print_info = print_info
        self.root = RegisterState(0, 0)
        self.states = dict()
        self.states[0] = [self.root]
        self.num_states = 1

    """
    Checks if currently, the RA is S-completable
    """
    def completeable(self):
        for w in self.S_plus:
            for i in range(len(w)+1):
                w1 = w[:i]
                w2 = w[i:]
                can_read, w_state = read_word(w1, copy.deepcopy(self.root))
                if not can_read:
                    break
                for z in self.S_minus:
                    for j in range(len(z)+1):
                        z1 = z[:j]
                        z2 = z[j:]
                        can_read, z_state = read_word(z1, copy.deepcopy(self.root))
                        if not can_read:
                            break
                        completable_logger.debug(
                            f'Testing w: {w1} + {w2}, z: {z1} + {z2} \n' + 
                            f'W state: {w_state.state_id}, mem: {"".join(w_state.memory)} \n'+
                            f'Z state: {z_state.state_id}, mem: {"".join(z_state.memory)}')
                        if w_state.state_id != z_state.state_id:
                            completable_logger.debug("Not the same state!")
                            continue
                        completable_logger.debug(f'Checking similarity {"".join(w_state.memory) + w2} and {"".join(z_state.memory) + z2}')
                        if is_similar(''.join(w_state.memory) + w2,
                            ''.join(z_state.memory) + z2):
                            completable_logger.debug("Similar. Not completeable...")
                            completable_logger.debug("#"*15)
                            return False
                        completable_logger.debug("Not similar, continuing...\n " + "#"*15)
        completable_logger.debug("Completable")
        return True


    def set_transition(self, char, state, word_):
        E = []
        index = state.get_index(char)
        word = str(state.state_id) + char
        transition_logger.debug(f'Finding transition for: ' +
            f'state: {state.state_id}:{state.memory}, ' +
            f'letter: {char}, ' +
            f'index: {index}')
        R = list(range(state.availability + 1))
        if index < state.availability:
            E.append(index)
            del R[index]
        
        transition_logger.debug("We find E")
        transition_logger.debug(f'We start with E: {E}, R: {R}')
        
        for r in R:
            E.append(r)
            transition_logger.debug(f'We test for E: {E}')
            new_state = RegisterState("#new", state.availability + 1 - len(E))
            state.transitions[index] = (E, new_state)

            assert read_word(word_, self.root)[0]

            if not self.completeable():
                transition_logger.debug("Did not work out....Reverting....")
                del E[len(E) - 1]
            del state.transitions[index]

        transition_logger.debug(f'Finally, we get E: {E} \n Now, we find target state')

        next_avail = state.availability + 1 - len(E)
        if next_avail in self.states.keys():
            for next_state in self.states[next_avail]:
                state.transitions[index] = (E, next_state)
                if not self.completeable():
                    del state.transitions[index]
                else:
                    transition_logger.debug(f'Transition: {state.state_id} --({index}, {E}) --> {next_state.state_id}')
                    return
        transition_logger.debug("NEW STATE!")
        next_state = RegisterState(self.num_states, next_avail)
        self.num_states = self.num_states+1
        state.transitions[index] = (E, next_state)
        if next_avail in self.states.keys():
            self.states[next_avail].append(next_state)
        else:
            self.states[next_avail] = [next_state]
        if word in self.S_plus:
            transition_logger.debug(f'Transition: {state.state_id} ' +
                f'--({index}, {E}) --> {next_state.state_id}')

    def refine_toread(self):
        del_indices = []
        for i in range(len(self.to_read)):
            word = self.to_read[i]
            refine_logger.debug(f'Reading word: {word}')
            can_read, _ = read_word(word, self.root)
            if can_read:
                refine_logger.debug(f'Can read! deleting')
                del_indices.append(i)
            refine_logger.debug(f'Cannot read')
        for i in range(len(del_indices)):
            del self.to_read[del_indices[i] - i]
        refine_logger.debug(f'to_read : {self.to_read}')

    def set_accepting(self):
        for w in self.S_plus:
            print(w)
            _, state = read_word(w, self.root)
            state.is_accepting = True

    def run_learning(self):
        while(len(self.to_read) > 0):
            w = self.to_read[0]
            _, prev_state = read_word(w, self.root)
            learner_logger.debug(f'To_read word {w}')
            self.set_transition(w[-1:], prev_state, w)
            self.refine_toread()
            learner_logger.debug(f'Words left to read: {len(self.to_read)}')
            learner_logger.debug("#"*15)

        self.set_accepting()
        RA = RegisterAutomata(self.root, sum(list(self.states.values()), []))
        return RA