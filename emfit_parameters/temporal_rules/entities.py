"""
List of dictionaries, each representing one entity (e.g. patient).
Keys of each entity are symbols and value of specific symbol is a list of tuples,
where each tuple represents one time interval of this symbol.
"""

# 4 entities
entity_list_4 = [
    {
        'A': [(2, 6), (12, 16)],
        'B': [(4, 13)],
        'C': [(4, 9), (12, 16)],
        'D': [(6, 19)],
        'E': [(8, 11), (14, 19)]
    },
    {
        'A': [(4, 8)],
        'B': [(2, 6)],
        'C': [(7, 14), (16, 19)],
        'D': [(5, 11)],
        'E': [(9, 16)]
    },
    {
        'A': [(3, 8)],
        'B': [(6, 10)],
        'C': [(6, 10), (12, 15)],
        'E': [(3, 12), (15, 18)]
    },
    {
        'B': [(3, 8), (12, 17)],
        'C': [(5, 10)],
        'D': [(5, 10), (14, 19)]
    }
]



entity_list = entity_list_4

