from typing import Generic, Dict

from aalpy.base import AutomatonState, Automaton
from aalpy.base.Automaton import InputType


class RegisterState(AutomatonState, Generic[InputType]):
    """
    Single state of a Register Automata. 
    Each state has:
    1. an availability metric, and
    2. a memory value
    3. a transition function
    """

    def __init__(self, state_id, availability, is_accepting=False):
        super().__init__(state_id)
        self.availability: int = availability
        self.memory : list[InputType] = []
        self.transitions : Dict[int, list[list[int], RegisterState]] = dict()
        self.is_accepting = is_accepting

    def set_memory(self, memory: list[InputType]):
        assert len(memory) == self.availability
        self.memory = memory

    def get_index(self, letter: InputType):
        try:
            return self.memory.index(letter)
        except ValueError as e:
            return self.availability

    def get_new_memory(self, letter:InputType, E: list[int]):
        new_memory = self.memory + [letter]
        for e in E:
            del new_memory[e]
        return new_memory

class RegisterAutomata(Automaton[RegisterState[InputType]]):

    def __init__(self, initial_state: RegisterState, states):
        super().__init__(initial_state, states)

    def step(self, letter):
        """
        In Register Automata, transitions are a function of memory and input
            Args:

                letter: single input that is looked up in the memory and the transition is performed

            Returns:

                True if the reached state is an accepting state, False otherwise
        """
        if letter is not None:
            index = self.current_state.get_index(letter)
            
            assert index <= self.current_state.availability
            
            E, target_state = self.current_state.transitions[index]
            memory = self.current_state.get_new_memory(letter, E)

            assert len(memory) == target_state.availability

            target_state.set_memory(memory)
            self.current_state = target_state
        return self.current_state.is_accepting

    def to_state_setup(self):
        state_setup_dict = {}

        sorted_states = sorted(self.states, key=lambda x: x.availability)
        for s in sorted_states:
            state_setup_dict[s.state_id] = (s.is_accepting,
                s.availability, s.transitions)

        return state_setup_dict

    def get_input_alphabet():
        return []

    @staticmethod
    def from_state_setup(state_setup : dict, **kwargs):
        """
            First state in the state setup is the initial state.
            Format: <state_id>: (<is_accepting>, <availability>, dict(transitions))
            Format of transitions: <index>: <deletion_list>, <target_state>
            state_setup = {
                "q0": (False, 0, {0: ([], "q1")}),
                "q1": (False, 1, {0: ([1], "q2"), 1: ([1], "q1")}),
                "q2": (True, 1, {0: ([1], "q2"), 1: ([1], "q1")})
            }


        Args:

            state_setup:
                state_setup should map from state_id to tuple(transitions_dict).

        Returns:

            Register Automata
        """

        # build states with state_id, accepting, availability
        states = {key: RegisterState(key, _[1], _[0]) for key, _ in state_setup.items()}

        # add transitions to states
        for state_id, state in states.items():
            for _input, (E, new_state) in state_setup[state_id][2].items():
                state.transitions[_input] = (E, states[new_state])

        # states to list
        states = [state for state in states.values()]

        # build RA with first state as starting state
        ra = RegisterAutomata(states[0], states)

        return ra