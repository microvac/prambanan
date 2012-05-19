(function (prambanan) {
    var __builtin__, _iter, a, b, c, print, range;
    __builtin__ = prambanan.import('__builtin__');
    print = __builtin__.print;
    range = __builtin__.range;
    _iter = prambanan.helpers.iter;
    a = (function () {
        var _i, _len, _list, _results;
        _results = [];
        _list = _iter(range(1, 10));
        for (_i = 0, _len = _list.length; _i < _len; _i++) {
            i = _list[_i];
            _results.push(i);
        }
        return _results;
    })();
    print(a);
    a = (function () {
        var _i, _len, _list, _results;
        _results = [];
        _list = _iter(range(1, 20));
        for (_i = 0, _len = _list.length; _i < _len; _i++) {
            i = _list[_i];
            if (i.__mod__(2) === 0) if (i > 5) _results.push(i);
        }
        return _results;
    })();
    print(a);
    a = (function () {
        var _i, _len, _list, _results;
        _results = [];
        _list = _iter(range(1, 20));
        for (_i = 0, _len = _list.length; _i < _len; _i++) {
            i = _list[_i];
            if (i.__mod__(2) === 0) if (i > 5) _results.push(i * 3);
        }
        return _results;
    })();
    print(a);
    a = (function () {
        var _i, _len, _list, _results;
        _results = [];
        _list = _iter(range(1, 20));
        for (_i = 0, _len = _list.length; _i < _len; _i++) {
            i = _list[_i];
            if (i.__mod__(2) === 0) if (i > 5) _results.push([i, i * 2]);
        }
        return _results;
    })();
    b = (function () {
        var _i, _len, _list, _results;
        _results = [];
        _list = _iter(a);
        for (_i = 0, _len = _list.length; _i < _len; _i++) {
            i = _list[_i][0];
            j = _list[_i][1];
            _results.push(i);
        }
        return _results;
    })();
    c = (function () {
        var _i, _len, _list, _results;
        _results = [];
        _list = _iter(a);
        for (_i = 0, _len = _list.length; _i < _len; _i++) {
            i = _list[_i][0];
            j = _list[_i][1];
            _results.push(j);
        }
        return _results;
    })();
    print(b);
    print(c);
    print(i);
    print(j);
    prambanan.exports('', {});
})(prambanan);