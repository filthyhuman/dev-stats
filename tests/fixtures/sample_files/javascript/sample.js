/**
 * Sample JavaScript file for parser testing.
 *
 * Expected values (hand-verified):
 *   Classes:    1  (Calculator)
 *   Methods:    3  (constructor, add, reset)
 *   Functions:  1  (helper)
 *   Imports:    path
 *   CC(add)     = 3  (if / else if / else)
 */

const path = require("path");

class Calculator {
    constructor(initial = 0) {
        this.value = initial;
        this.history = [];
    }

    add(x) {
        if (x > 0) {
            this.value += x;
        } else if (x < 0) {
            this.value += x;
        } else {
            // no-op
        }
        this.history.push(x);
        return this;
    }

    reset() {
        this.value = 0;
        this.history = [];
    }
}

function helper(a, b, c = 0) {
    return a + b + c;
}

module.exports = { Calculator, helper };
