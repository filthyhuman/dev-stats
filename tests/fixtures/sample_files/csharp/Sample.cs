/**
 * Sample C# file for parser testing.
 *
 * Expected values (hand-verified):
 *   Classes:    1  (Calculator)
 *   Interfaces: 1  (IComputable)
 *   Methods:    3  (Calculator, Add, Reset)
 *   Functions:  0
 *   Usings:     System, System.Collections.Generic
 *   CC(Add)     = 3  (if / else if / else)
 */

using System;
using System.Collections.Generic;

namespace DevStats.Fixtures
{
    public interface IComputable
    {
        Calculator Add(int x);
        void Reset();
    }

    public class Calculator : IComputable
    {
        private int value;
        private List<int> history;

        public Calculator(int initial = 0)
        {
            this.value = initial;
            this.history = new List<int>();
        }

        public Calculator Add(int x)
        {
            if (x > 0)
            {
                this.value += x;
            }
            else if (x < 0)
            {
                this.value += x;
            }
            else
            {
                // no-op
            }
            this.history.Add(x);
            return this;
        }

        public void Reset()
        {
            this.value = 0;
            this.history.Clear();
        }
    }
}
