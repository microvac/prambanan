(function (prambanan) {
    var _make_kwargs;
    _make_kwargs = prambanan.helpers.make_kwargs;
    anu(1, 2);
    anu(1, "daa", _make_kwargs({ca: "lala"}));
    anu(_make_kwargs({ca: "lala"}));
    anu(args);
    anu(kwargs);
    anu(_make_kwargs({ca: "lala"}), kwargs);
    prambanan.exports('', {});
})(prambanan);