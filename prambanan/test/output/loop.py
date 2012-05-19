for i in range(1, 10):
    print i

for i,j in map(lambda i: (i, i* 2), range(1, 10)):
    print "%d - %d" % (i, j)

for i in range(1, 10):
    print i
else:
    print "else"
    print i

i = 0
while(i < 20):
    print "i ne: %d" % i
    i = i + 1
