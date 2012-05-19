a = [i for i in range(1, 10)]
print a

a = [i for i in range(1, 20) if i % 2 == 0 if i > 5]
print a

a = [i * 3 for i in range(1, 20) if i % 2 == 0 if i > 5]
print a

a = [(i, i*2) for i in range(1, 20) if i % 2 == 0 if i > 5]
b = [i for (i,j) in a]
c = [j for (i,j) in a]
print b
print c
print i
print j

