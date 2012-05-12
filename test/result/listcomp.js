(function (prambanan) {
    var _iter, a;
    _iter = prambanan.helpers.iter;
    a = (function () {
        var _i, _len, _list, _results;
        _results = [];
        _list = _iter(a);
        for (_i = 0, _len = _list.length; _i < _len; _i++) {
            i = _list[_i];
            _results.push(i);
        }
        return _results;
    })();
    a = (function () {
        var _i, _len, _list, _results;
        _results = [];
        _list = _iter(a);
        for (_i = 0, _len = _list.length; _i < _len; _i++) {
            i = _list[_i];
            _results.push(i * 2);
        }
        return _results;
    })();
    a = (function () {
        var _i, _len, _list, _results;
        _results = [];
        _list = _iter(a);
        for (_i = 0, _len = _list.length; _i < _len; _i++) {
            i = _list[_i];
            _results.push(anu(i * 2));
        }
        return _results;
    })();
    a = (function () {
        var _i, _len, _list, _results;
        _results = [];
        _list = _iter(a);
        for (_i = 0, _len = _list.length; _i < _len; _i++) {
            i = _list[_i];
            if (i / 2 === 0) _results.push(i * 2);
        }
        return _results;
    })();
    a = (function () {
        var _i, _len, _list, _results;
        _results = [];
        _list = _iter(a);
        for (_i = 0, _len = _list.length; _i < _len; _i++) {
            i = _list[_i];
            if (i / 2 === 0) _results.push([i, i * 2]);
        }
        return _results;
    })();
    a = (function () {
        var _i, _len, _list, _results;
        _results = [];
        _list = _iter(a);
        for (_i = 0, _len = _list.length; _i < _len; _i++) {
            i = _list[_i];
            if (i / 2 === 0) if (i + 1 > 3) _results.push(i);
        }
        return _results;
    })();
    prambanan.exports('', {
        a: a
    });
})(prambanan);