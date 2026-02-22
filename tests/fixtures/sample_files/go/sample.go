// Sample Go file for parser testing.
//
// Expected values (hand-verified):
//   Structs:    1  (Calculator)
//   Interfaces: 1  (Computable)
//   Functions:  1  (Helper)
//   Methods:    2  (Add, Reset)
//   Imports:    fmt
//   CC(Add)     = 3  (if / else if / else)

package main

import "fmt"

// Computable defines add and reset operations.
type Computable interface {
	Add(x int) *Calculator
	Reset()
}

// Calculator holds a value and history.
type Calculator struct {
	Value   int
	History []int
}

// Add adds x to the calculator value.
func (c *Calculator) Add(x int) *Calculator {
	if x > 0 {
		c.Value += x
	} else if x < 0 {
		c.Value += x
	} else {
		// no-op
	}
	c.History = append(c.History, x)
	return c
}

// Reset resets the calculator.
func (c *Calculator) Reset() {
	c.Value = 0
	c.History = nil
}

// Helper is a top-level function.
func Helper(a, b, c int) int {
	fmt.Println("helper called")
	return a + b + c
}
