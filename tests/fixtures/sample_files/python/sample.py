"""Sample Python file for parser testing.

Expected values (hand-verified):
  Classes:   1  (Calculator)
  Methods:   3  (__init__, add, reset)
  Functions: 1  (helper)
  CC(__init__) = 1
  CC(add)      = 3  (if / elif / else)
  CC(reset)    = 1
  Attributes:  value, history
  Imports:     (none)
"""


class Calculator:
    """A simple calculator for parser fixture testing."""

    def __init__(self, initial: int = 0) -> None:
        """Initialise with a starting value."""
        self.value = initial
        self.history: list[int] = []

    def add(self, x: int) -> "Calculator":
        """Add x to the current value."""
        if x > 0 or x < 0:
            self.value += x
        else:
            pass
        self.history.append(x)
        return self

    def reset(self) -> None:
        """Reset to zero."""
        self.value = 0
        self.history.clear()


def helper(a: int, b: int, c: int = 0) -> int:
    """A top-level helper function with a default parameter."""
    return a + b + c
