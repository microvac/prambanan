class BaseException(object): 
    def __init__(self, message):
        if Error.captureStackTrace:
            Error.captureStackTrace(self);
        self.message = message;

class Exception(BaseException): pass

class StandardError(Exception): pass

class AttributeError(StandardError): pass
class TypeError(StandardError): pass
class ValueError(StandardError): pass
class NameError(StandardError): pass
class SystemError(StandardError): pass

class LookupError(StandardError): pass
class KeyError(LookupError): pass
class IndexError(LookupError): pass

class ArithmeticError(StandardError): pass
class ZeroDivisionError(ArithmeticError): pass

class RuntimeError(StandardError): pass
class NotImplementedError(RuntimeError): pass
