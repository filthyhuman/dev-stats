/**
 * Sample Java file for parser testing.
 *
 * Expected values (hand-verified):
 *   Classes:    2  (Calculator, MathUtils)
 *   Methods:    4  (Calculator: constructor, add, reset; MathUtils: factorial)
 *   Imports:    java.util
 *   Interfaces: 0
 *   CC(add)     = 3  (if / else if / else)
 *   CC(factorial) = 2  (if)
 */

import java.util.ArrayList;
import java.util.List;

public class Calculator {
    private int value;
    private List<Integer> history;

    public Calculator(int initial) {
        this.value = initial;
        this.history = new ArrayList<>();
    }

    public Calculator add(int x) {
        if (x > 0) {
            this.value += x;
        } else if (x < 0) {
            this.value += x;
        } else {
            // no-op
        }
        this.history.add(x);
        return this;
    }

    public void reset() {
        this.value = 0;
        this.history.clear();
    }
}

class MathUtils {
    public static int factorial(int n) {
        if (n <= 1) {
            return 1;
        }
        return n * factorial(n - 1);
    }
}
