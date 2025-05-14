"""
zip() is a built-in Python function that aggregates elements from multiple iterables (like lists or tuples) into tuples,
pairing items together by index.

Syntax

zip(iterable1, iterable2, ..., iterableN)
🔸 Parameters:
iterable1, iterable2, ..., iterableN: Two or more iterables (like lists, tuples, strings, etc.)

🔸 Returns:
An iterator of tuples, where the i-th tuple contains the i-th element from each of the input iterables.


"""

names = ['Alice', 'Bob', 'Charlie']
scores = [85, 92, 78]

zipped = zip(names, scores)

print(list(zipped))  # [('Alice', 85), ('Bob', 92), ('Charlie', 78)]


# 🔹 Common Use Cases
# 1. Looping over multiple lists in parallel

for name, score in zip(names, scores):
    print(f"{name} scored {score}")

# 2. Creating a dictionary from two lists
name_score_dict = dict(zip(names, scores))
print(name_score_dict)  # {'Alice': 85, 'Bob': 92, 'Charlie': 78}

# 3. Unzipping: Convert zipped object back to original lists
zipped = zip(names, scores)
names_unzipped, scores_unzipped = zip(*zipped)
print(names_unzipped)  # ('Alice', 'Bob', 'Charlie')

# 🔹 Handling Iterables of Different Lengths
# By default, zip() stops at the shortest iterable.
a = [1, 2, 3]
b = ['x', 'y']

print(list(zip(a, b)))  # [(1, 'x'), (2, 'y')]

# If you want to zip to the longest iterable, use itertools.zip_longest():
from itertools import zip_longest

print(list(zip_longest(a, b, fillvalue=None)))  # [(1, 'x'), (2, 'y'), (3, None)]

# 🔹 Advanced Example: Zipping Multiple Lists
a = [1, 2, 3]
b = ['a', 'b', 'c']
c = [True, False, True]

for x, y, z in zip(a, b, c):
    print(x, y, z)

"""
🔹 Summary
Feature	Behavior
Input	Two or more iterables
Output	Iterator of tuples
Length	Matches the shortest iterable
Useful with dict()	Yes
Unzip with * operator	Yes (zip(*zipped_data))
Use zip_longest()	To pad to longest iterable
"""