(function(prambanan) {
    var __builtin__, _i, _i1, _i2, _len, _len1, _len2, _list, _list1, _list2, i, j, map, print, range;
    __builtin__ = prambanan.import('__builtin__');
    print = __builtin__.print;
    map = __builtin__.map;
    range = __builtin__.range;
    _list = range(1, 10);
    for (_i = 0, _len = _list.length; _i < _len; _i++) {
        i = _list[_i];
        print(i);
    }
    _list1 = map(function(i) {
        return [i, i * 2];
    }, range(1, 10));
    for (_i1 = 0, _len1 = _list1.length; _i1 < _len1; _i1++) {
        i = _list1[_i1][0];
        j = _list1[_i1][1];
        print(("%d - %d").__mod__(i, j));
    }
    _list2 = range(1, 10);
    for (_i2 = 0, _len2 = _list2.length; _i2 < _len2; _i2++) {
        i = _list2[_i2];
        print(i);
    }
    if (_i2 == _len2) {
        print("else");
        print(i);
    }
    i = 0;
    while (i < 20) {
        print(("i ne: %d").__mod__(i));
        i = i + 1;
    }
    prambanan.exports('loop', {});
})(prambanan);