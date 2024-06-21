import time
from bisect import insort
from typing import Union
import logging
import copy

from aalpy.automata import RegisterState, RegisterAutomata

"""
    Data of form: List of (<string>, <boolean>)
"""

handler = logging.FileHandler('error.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(name)s: %(message)s')
handler.setFormatter(formatter)

completable_logger = logging.getLogger('completable')
completable_logger.addHandler(handler)
completable_logger.setLevel(logging.DEBUG)

readword_logger = logging.getLogger('readword')
readword_logger.addHandler(handler)
# readword_logger.setLevel(logging.DEBUG)

transition_logger = logging.getLogger('transition')
transition_logger.addHandler(handler)
transition_logger.setLevel(logging.DEBUG)

learner_logger = logging.getLogger('learner')
learner_logger.addHandler(handler)
learner_logger.setLevel(logging.DEBUG)

refine_logger = logging.getLogger('refine')
# refine_logger.addHandler(handler)
refine_logger.setLevel(logging.DEBUG)


class RA_passive:
    def __init__(self, data, print_info=True):
        self.to_read, self.S_plus, self.S_minus = prefixes(data)
        self.print_info = print_info
        self.root = RegisterState(0, 0)
        self.states = dict()
        self.states[0] = [self.root]
        self.num_states = 1

    def get_next_word(self):
        for w in self.to_read:
            can_read, prev_state = read_word(w, self.root)
            if not can_read:
                return w, prev_state
        return None, None

    def completeable(self):
        for w in self.S_plus:
            for i in range(len(w)+1):
                w1 = w[:i]
                can_read, w_state = read_word(w1, copy.deepcopy(self.root))
                if not can_read:
                    break
                w2 = w[i:]
                for z in self.S_minus:
                    for j in range(len(z)+1):
                        z1 = z[:j]
                        can_read, z_state = read_word(z1, copy.deepcopy(self.root))
                        if not can_read:
                            break
                        z2 = z[j:]
                        completable_logger.debug(
                            f'Testing w: {w1} + {w2}, z: {z1} + {z2}')
                        completable_logger.debug(
                            f'W state: {w_state.state_id}, mem: '+ 
                            "".join(w_state.memory))
                        completable_logger.debug(
                            f'Z state: {z_state.state_id}, mem: '+ 
                            "".join(z_state.memory))
                        if w_state.state_id != z_state.state_id:
                            completable_logger.debug("Not the same state!")
                            continue
                        completable_logger.debug(
                            "Checking similarity {} and {}".format(
                            ''.join(w_state.memory) + w2,
                            ''.join(z_state.memory) + z2))
                        if is_similar(''.join(w_state.memory) + w2,
                            ''.join(z_state.memory) + z2):
                            completable_logger.debug("Not similar...")
                            completable_logger.debug("Not completeable...")
                            completable_logger.debug("#"*15)
                            return False
                        completable_logger.debug("Similar - we continue.")
                        completable_logger.debug("#"*15)
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

        transition_logger.debug(f'Finally, we get E: {E}')
        transition_logger.debug("Now, we find target state")

        next_avail = state.availability + 1 - len(E)
        if next_avail in self.states.keys():
            for next_state in self.states[next_avail]:
                state.transitions[index] = (E, next_state)
                if not self.completeable():
                    del state.transitions[index]
                else:
                    transition_logger.debug(
                        f'Transition: {state.state_id} ' +
                        f'--({index}, {E}) --> {next_state.state_id}')
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
            w, max_read_state = self.get_next_word()
            learner_logger.debug(f'To_read word {w}')
            self.set_transition(w[-1:], max_read_state, w)
            self.refine_toread()
            learner_logger.debug(f'Words left to read: {len(self.to_read)}')
            learner_logger.debug("#"*15)

        self.set_accepting()
        RA = RegisterAutomata(self.root, sum(list(self.states.values()), []))
        return RA

def prefixes(data):
    prefixes = []
    S_plus = []
    S_minus = []
    for d, acc in data:
        if acc:
            S_plus.append(d)
        else:
            S_minus.append(d)
        for i in range(len(d)):
            pref = d[:i+1]
            if pref not in prefixes:
                prefixes.append(pref)
    prefixes.sort(key=lambda x: (len(x), x))
    return prefixes, S_plus, S_minus

def read_word(w, root):
    current = root
    readword_logger.debug(f'Reading word: {w}')
    readword_logger.debug('#'*10)
    for i in range(len(w)):
        readword_logger.debug(f'Reading letter: {w[i]}')
        try:
            readword_logger.debug(f'Current memory: {current.memory}')
            index = current.get_index(w[i])
            E, next_state = current.transitions[index]
            readword_logger.debug(f'Transition: {index} = {E, next_state.state_id}')
            memory = current.get_new_memory(w[i], E)
            next_state.set_memory(memory)
            current = next_state
        except:
            readword_logger.debug(f'Cannot read more.. stopped at {w[:i]}')
            return False, current
    return True, current

def is_similar(m, n):
    length = len(m)
    if len(n) != length:
        return False
    for i in range(length):
        for j in range(i, length):
            if m[i] == m[j] and n[i] != n[j]:
                return False
            if m[i] != m[j] and n[i] == n[j]:
                return False
    return True