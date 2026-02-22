/**
 * Sample TypeScript file for parser testing.
 *
 * Expected values (hand-verified):
 *   Classes:    1  (Calculator)
 *   Interfaces: 1  (Computable)
 *   Methods:    3  (constructor, add, reset)
 *   Functions:  1  (helper)
 *   Imports:    path
 *   Enums:      1  (Operation)
 */

import * as path from "path";

interface Computable {
    add(x: number): Computable;
    reset(): void;
}

enum Operation {
    Add = "add",
    Reset = "reset",
}

class Calculator implements Computable {
    private value: number;
    private history: number[];

    constructor(initial: number = 0) {
        this.value = initial;
        this.history = [];
    }

    add(x: number): Calculator {
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

    reset(): void {
        this.value = 0;
        this.history = [];
    }
}

function helper(a: number, b: number, c: number = 0): number {
    return a + b + c;
}

export { Calculator, helper, Computable, Operation };
