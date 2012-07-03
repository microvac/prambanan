class Class1(object):
    """
    doc doc
    """

    def __init__(self):
        print "init 1"

    def method1(self, b):
        b = 3
        self = 3
        print "method1"

class Class2(Class1):

    def __init__(self):
        print "init 2"
        super(Class2, self).__init__()

    def method2(self):
        print "method2"

class Class3(Class2, Class1):


    def method3(self):
        print "method3"

class Class4(Class3):

    def method2(self):
        print "method2-4"

    def method4(self):
        print "method4"

class Class5(object):

    def __init__(self):
        print "init 1"

    def method4(self):
        print "method4-5"

    def method5(self):
        print "method5"

class Class6(Class4, Class5):

    def __init__(self):
        print "init 3"

    def method1(self):
        print "method1-5"

    def method6(self):
        print "method6"

    def method7(self, a):
        print "method 7 with arg % s" % a

a = Class1()
b = Class2()
c = Class3()
d = Class4()
e = Class5()
f = Class6()

print isinstance(a, Class1)
print isinstance(a, Class2)
print isinstance(a, Class3)

print isinstance(b, Class1)
print isinstance(b, Class2)
print isinstance(b, Class3)

print isinstance(c, Class3)
print isinstance(c, Class2)
print isinstance(c, Class1)

f.method1()
f.method2()
f.method3()
f.method4()
f.method5()
f.method6()
f.method7("lalala")

print isinstance(f, Class5)


class ClassMethod1(object):
    l = [1,2,3]

    @classmethod
    def get_l(cls):
        return cls.l

class ClassMethod2(ClassMethod1):
    l = [1,2,3, 4]

print ClassMethod1.get_l()
print ClassMethod2.get_l()

