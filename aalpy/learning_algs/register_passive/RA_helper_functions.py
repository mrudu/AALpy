import logging

completable_logger = logging.getLogger('completable')
readword_logger = logging.getLogger('readword')

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