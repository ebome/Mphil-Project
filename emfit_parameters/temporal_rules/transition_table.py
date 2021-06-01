"""
Transition table is 2D matrix coded as dictionary with tuples as keys.

r - one of 3 my-defined temporal relations ('e','j','i'), which corresponds to 
Allen's ('<','m','o')

Key: (A r B, B r C) ... Value: List of possible relations A r C

(A r B) ∧ (B r C) ==> A {r1, r2, ...} C
"""

transition_table = {
    ('e', 'e'): ['e'],
    ('e', 'j'): ['e'],
    ('e', 'i'): ['e'],
    # ('<', 'c'): ['<'],
    # ('<', 'f'): ['<'],
    # ('<', '='): ['<'],
    # ('<', 's'): ['<'],

    ('j', 'e'): ['e'],
    ('j', 'j'): ['e'],
    ('j', 'i'): ['e'],
    # ('m', 'c'): ['<'],
    # ('m', 'f'): ['<'],
    # ('m', '='): ['m'],
    # ('m', 's'): ['m'],

    ('i', 'e'): ['e'],
    ('i', 'j'): ['e'],
    ('i', 'i'): ['e', 'j', 'i'],
    # ('o', 'c'): ['<', 'm', 'o', 'c', 'f'],
    # ('o', 'f'): ['<', 'm', 'o'],
    # ('o', '='): ['o'],
    # ('o', 's'): ['o'],

    # ('c', '<'): ['<', 'm', 'o', 'c', 'f'],
    # ('c', 'm'): ['o', 'c', 'f'],
    # ('c', 'o'): ['o', 'c', 'f'],
    # ('c', 'c'): ['c'],
    # ('c', 'f'): ['c'],
    # ('c', '='): ['c'],
    # ('c', 's'): ['o', 'c', 'f'],

    # ('f', '<'): ['<'],
    # ('f', 'm'): ['m'],
    # ('f', 'o'): ['o'],
    # ('f', 'c'): ['c'],
    # ('f', 'f'): ['f'],
    # ('f', '='): ['f'],
    # ('f', 's'): ['o'],

    # ('=', '<'): ['<'],
    # ('=', 'm'): ['m'],
    # ('=', 'o'): ['o'],
    # ('=', 'c'): ['c'],
    # ('=', 'f'): ['f'],
    # ('=', '='): ['='],
    # ('=', 's'): ['s'],

    # ('s', '<'): ['<'],
    # ('s', 'm'): ['<'],
    # ('s', 'o'): ['<', 'm', 'o'],
    # ('s', 'c'): ['<', 'm', 'o', 'c', 'f'],
    # ('s', 'f'): ['<', 'm', 'o'],
    # ('s', '='): ['s'],
    # ('s', 's'): ['s']
}


