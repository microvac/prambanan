def test1(a, b):
    print "%d, %d" % (a, b)

test1(2, 4)

def test2(a, b=20):
    print "%d, %d" % (a, b)

test2(2, 4)
test2(2)

def test3(*args):
    for a in args:
        print a

test3()
test3(1)
test3(1,2,3,4,5,6)

def test4(i, *args):
    for a in args:
        print a
test4(1)
test4(1,2,3,4,5,6)

def test5(i, b=77, *args):
    print b
    for a in args:
        print a
test5(5)
test5(8,9,10)
test5(8,b=20)

def test6(b=99, **kwargs):
    print b
    for a in sorted(iter(kwargs)):
        print kwargs.get(a, "none")


test6(b=31)
test6(b=31, c=4, e=5)

def test7(*args, **kwargs):
    print "varargs"
    for a in args:
        print a
    print "kwargs"
    for a in sorted(iter(kwargs)):
        print kwargs.get(a, "none")

test7(1,2,3,a=4,b=5,c=6)

def test8(wew,*args, **kwargs):
    print wew
    print "varargs"
    for a in args:
        print a
    print "kwargs"
    for a in sorted(iter(kwargs)):
        print kwargs.get(a, "none")

test8(1,2,3,a=4,b=5,c=6)

def test9(**kwargs):
    print kwargs.pop("a",20)
    print kwargs.pop("a",30)
    print kwargs.pop("b",40)

test9(a=4,b=5,c=6)

