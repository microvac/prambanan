(function(prambanan) {
    var __builtin__, _subscript, a, b, print;
    __builtin__ = prambanan.import('__builtin__');
    print = __builtin__.print;
    _subscript = prambanan.helpers.subscript;
    a = [1, 2, 3];
    print(a);
    a.append(4);
    print(a);
    print(_subscript.l.i(a, 1));
    print(_subscript.l.i(a, -1));
    print(_subscript.l.s(a, 1, 2, null));
    a.extend([4, 5, 6, 7, 8]);
    a.extend(a);
    print(a);
    print(_subscript.l.s(a, 1, null, 3));
    print(_subscript.l.s(a, 1, 7, 3));
    _subscript.d.i(a, 2);
    print(a);
    _subscript.d.i(a, 2);
    print(a);
    _subscript.d.s(a, 2, 5, null);
    print(a);
    b = a.pop();
    print(a);
    print(b);
    b = a.pop(2);
    print(a);
    print(b);
    a.insert(3, 10);
    print(a);
    prambanan.exports('list', {});
})(prambanan);