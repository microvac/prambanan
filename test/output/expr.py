a = 3
b = 8
print a + 5
print a * 5
print a - b
print "eaaaa"+"aduuuh"

print "tada %s" % "hmmm"

print "tada %s - %d" % ("hmmm", 4)
print 6 / 3
print 16 << 2
print 2 >> 5
print 2**3

e, f = (5, 3)
print e
print f

print 2**3*3+4-20*10-18

a = 5
b = 7

i = [0]
def get_b():
    a = i[0]
    i[0] = a+1
    a = i[0]
    return a

if a > b > 10:
    print "daaa"
else:
    print "maca"

d = "kutumbaba" if a > b > 10 else "hulahula"

if -1 < get_b() < 2:
    print "daaa"
else:
    print "maca"
print get_b()

while -1 < get_b() < -1000:
    print "daaa"
print get_b()

