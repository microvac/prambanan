import colander

class Anu(object):
    kenapa="lalala"
    def peci(self):
        print "anu"

class Kutumbaba(colander.MappingSchema):
    anu=colander.SchemaNode(colander.Int)

tada = Kutumbaba()
print tada