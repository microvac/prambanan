from collections import OrderedDict
import collections
class Parent1(object):

    def visit_a(self):
        print "parent 1 a"

    def get_visitor(self, cls):
        visitor = getattr(cls, "visit_a", None)
        if visitor is not None:
            return visitor

    def visit(self, node):
        visitors = OrderedDict()
        classes = [self.__class__]
        while len(classes) > 0:
            cls = classes.pop(0)
            for base in cls.__bases__:
                classes.append(base)
            visitor = self.get_visitor(cls)
            if visitor is not None and cls not in visitors:
                visitors[cls] = visitor

        for cls, visitor in visitors.items():
            visitor(self)

class Parent2(Parent1):

    def visit_a(self):
        print "parent 2 a"

class Parent3(Parent1):

    def visit_a(self):
        print "parent 3 a"

class Parent4(Parent2, Parent3):

    def visit_a(self):
        print "parent 4 a"


test = Parent4()
test.visit("a")
