a = [i for i in a]
a = [i * 2 for i in a]
a = [anu(i * 2) for i in a]
a = [i * 2 for i in a if i / 2 == 0]
a = [(i, i * 2) for i in a if i / 2 == 0]
a = [i for i in a if i / 2 == 0 if i + 1 > 3]

