"""Append-only suffix automaton for substring membership and distinct counts."""

from dataclasses import dataclass, field


@dataclass
class TextState:
    longest: int = 0
    suffix_link: int = -1
    next_state: dict[str, int] = field(default_factory=dict)


class IncidentTextAutomaton:
    def __init__(self):
        self.states = [TextState()]
        self.last = 0
        self.characters = 0

    def append(self, character: str) -> None:
        if len(character) != 1:
            raise ValueError("append exactly one character")
        current = len(self.states)
        self.states.append(TextState(longest=self.states[self.last].longest + 1))
        predecessor = self.last
        while predecessor >= 0 and character not in self.states[predecessor].next_state:
            self.states[predecessor].next_state[character] = current
            predecessor = self.states[predecessor].suffix_link
        if predecessor < 0:
            self.states[current].suffix_link = 0
        else:
            candidate = self.states[predecessor].next_state[character]
            if self.states[predecessor].longest + 1 == self.states[candidate].longest:
                self.states[current].suffix_link = candidate
            else:
                clone = len(self.states)
                original = self.states[candidate]
                self.states.append(TextState(self.states[predecessor].longest + 1, original.suffix_link, original.next_state.copy()))
                while predecessor >= 0 and self.states[predecessor].next_state.get(character) == candidate:
                    self.states[predecessor].next_state[character] = clone
                    predecessor = self.states[predecessor].suffix_link
                self.states[candidate].suffix_link = clone
                self.states[current].suffix_link = clone
        self.last = current
        self.characters += 1

    def contains(self, pattern: str) -> bool:
        state = 0
        for character in pattern:
            state = self.states[state].next_state.get(character, -1)
            if state < 0:
                return False
        return True

    def distinct_substrings(self) -> int:
        return sum(state.longest - self.states[state.suffix_link].longest
                   for state in self.states[1:])


incident_text = IncidentTextAutomaton()
for character in "dispatch-dispatch":
    incident_text.append(character)
print(incident_text.contains("patch"))
print(incident_text.contains("patch-dis"))
print(incident_text.contains("warehouse"))
print(incident_text.distinct_substrings())
