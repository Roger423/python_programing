"""
🔹 all() — Overview
✅ Syntax

all(iterable)
✅ Purpose
Returns True if all elements in the iterable are true (or if the iterable is empty). Otherwise, returns False.

🔹 How It Works
all() checks each element in the iterable (like a list, tuple, set).

It short-circuits: returns False as soon as it finds a False element.

Truthiness is determined using Python's rules (e.g., 0, None, False, '', [], {} are considered False).
"""
# 🔹 Examples
# ✅ Basic Usage
all([True, True, True])         # → True
all([True, False, True])        # → False
all([])                         # → True (empty iterable is considered True)

# ✅ With Numbers
all([1, 2, 3])                  # → True (non-zero values are truthy)
all([1, 0, 3])                  # → False (0 is falsy)

# ✅ With Strings
all(["hello", "world"])         # → True
all(["hello", ""])              # → False (empty string is falsy)

# ✅ With Generators
all(x > 0 for x in [1, 2, 3])   # → True
all(x > 0 for x in [1, -1, 3])  # → False

# 🔹 Practical Use Cases
# ✅ Validate All Inputs
inputs = ["user", "pass", "email"]
if all(inputs):
    print("All fields filled in.")

# ✅ Check Conditions on List Elements
numbers = [10, 20, 30]
if all(n > 5 for n in numbers):
    print("All numbers > 5")

"""
# 🔹 Difference Between all() and any()
-----------------------------------------------------------------------------
Function	Description	                     Example
-----------------------------------------------------------------------------
all()	    True if all are truthy	         all([True, True]) → True
any()	    True if any one is truthy	     any([False, True]) → True
-----------------------------------------------------------------------------

🔹 Summary
all() is simple but powerful for input validation, filtering, assertions, etc.

It's very useful in loops, generators, and condition checking.

It's a short-circuit operation: stops early for efficiency.
"""