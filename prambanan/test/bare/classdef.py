import colander

class Anu(object):
    pass

class Anuu(object):
    lala=3
    def anu(self):
        self.anu = 4

class Anu2(object):
    @staticmethod
    def anu(self):
        self.anu = 4
    @staticmethod
    def anu3(self):
        self.anu = 4

class Anu3(Anu, Anu2):
    lala=3
    def anu(self):
        self.anu = 4
    @staticmethod
    def anu3(self):
        self.anu = 4

class Anu5(Anu, Anu2):
    """
    tada da da
    """
    lala=3
    def anu(self):
        self.anu = 4
    @staticmethod
    def anu3(self):
        self.anu = 4

class Anu6(Anu, Anu2, Anu5):
    """
    tada da da
    """
    @staticmethod
    def anu3(self):
        self.anu = 4
    lala=3
    def anu(self):
        self.anu = 4

