/**
 * Sample C++ file for parser testing.
 *
 * Expected values (hand-verified):
 *   Classes:    1  (Calculator)
 *   Structs:    1  (Result)
 *   Methods:    3  (Calculator, add, reset)
 *   Functions:  1  (helper)
 *   Includes:   vector, string
 *   CC(add)     = 3  (if / else if / else)
 */

#include <vector>
#include <string>

struct Result {
    int value;
    std::string label;
};

class Calculator {
private:
    int value;
    std::vector<int> history;

public:
    Calculator(int initial = 0) : value(initial) {}

    Calculator& add(int x) {
        if (x > 0) {
            value += x;
        } else if (x < 0) {
            value += x;
        } else {
            // no-op
        }
        history.push_back(x);
        return *this;
    }

    void reset() {
        value = 0;
        history.clear();
    }
};

int helper(int a, int b, int c = 0) {
    return a + b + c;
}
