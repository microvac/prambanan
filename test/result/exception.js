(function (prambanan) {
    var __builtin__, __py_file__, _ex, _ex1, _ex2, _ex3, _ex4, _throw, a, b, c, print;
    __builtin__ = prambanan.import('__builtin__');
    print = __builtin__.print;
    _throw = prambanan.helpers.throw;
    __py_file__ = 'exception.py';
    try {
        a = 3;
    } catch (_ex) {
        if (_ex instanceof BaseException) {
            print("a");
        } else {
            _throw(_ex, __py_file__, 1);
        }
    }
    try {
        a = 3;
    } catch (_ex1) {
        if (_ex1 instanceof BaseException) {
            b = _ex1;
            print(a.message);
        } else {
            _throw(_ex1, __py_file__, 6);
        }
    }
    try {
        a = 3;
    } catch (_ex2) {
        if (_ex2 instanceof BaseException) {
            b = _ex2;
            print(b.message);
        } else if (_ex2 instanceof ValueError) {
            c = _ex2;
            print(c.message);
        } else {
            _throw(_ex2, __py_file__, 11);
        }
    }
    try {
        a = 3;
    } catch (_ex3) {
        if (_ex3 instanceof BaseException) {
            b = _ex3;
            print(b.message);
        } else {
            print("a");
        }
    }
    try {
        a = 3;
    } catch (_ex4) {
        print("a");
    }
    try {
        a = 3;
    } finally {
        print("a");
    }
    prambanan.exports('', {});
})(prambanan);