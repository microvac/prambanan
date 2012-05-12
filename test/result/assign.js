(function (prambanan) {
    var a, b, c;
    a = "string";
    a = b = 3;
    (function (_source) {
        a = _source[0];
        b = _source[1];
    })(c);
    c = [a, b];
    prambanan.exports('', {
        a: a,
        c: c
    });
})(prambanan);