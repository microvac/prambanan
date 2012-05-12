(function (prambanan) {
    var _subscript, a;
    _subscript = prambanan.helpers.subscript;
    a[1] = 3;
    a = a[2];
    _subscript('del', a, index, 1);
    a = _subscript('load', a, 'slice', 1, 2, null);
    a = _subscript('load', a, 'slice', 1, 2, 3);
    _subscript('del', a, 'slice', 1, 2, null);
    a["tadaa"] = 5;
    a[" paa"] = 4;
    a["pa pa"] = 5;
    _subscript('store', a, index, b, 4);
    _subscript('del', a, index, "pa");
    _subscript('load', a, 'slice', "pa pa", "papa", null);
    prambanan.exports('', {
        a: a
    });
})(prambanan);