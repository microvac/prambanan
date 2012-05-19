(function (prambanan) {
    var __builtin__, _op, _op1, _pow, a, b, d, e, f, get_b, i, print;
    __builtin__ = prambanan.import('__builtin__');
    print = __builtin__.print;
    _pow = prambanan.helpers.pow;
    a = 3;
    b = 8;
    print(a + 5);
    print(a * 5);
    print(a - b);
    print("eaaaa" + "aduuuh");
    print("tada %s".__mod__("hmmm"));
    print("tada %s - %d".__mod__("hmmm", 4));
    print(6 / 3);
    print(16 << 2);
    print(2 >> 5);
    print(_pow(2, 3));
    (function (_source) {
        e = _source[0];
        f = _source[1];
    })([5, 3]);
    print(e);
    print(f);
    print(_pow(2, 3) * 3 + 4 - 20 * 10 - 18);
    a = 5;
    b = 7;
    i = [0];
    get_b = function () {
        var a;
        a = i[0];
        i[0] = a + 1;
        a = i[0];
        return a;
    };
    if ((a > b) && (b > 10)) {
        print("daaa");
    } else{print("maca");}
    d = (a > b) && (b > 10) ? "kutumbaba" : "hulahula";
    _op = get_b();
    if ((-1 < _op) && (_op < 2)) {
        print("daaa");
    } else{print("maca");}
    print(get_b());
    _op1 = get_b();
    while ((-1 < _op1) && (_op1 < -1000)) {
        print("daaa");
    }
    print(get_b());
    prambanan.exports('', {get_b: get_b});
})(prambanan);