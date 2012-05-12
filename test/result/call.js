(function (prambanan) {
    var _make_kwargs;
    _make_kwargs = prambanan.helpers.make_kwargs;
    anu(1, 2);
    anu(1, "daa", _make_kwargs({
        pa: "lala",
        ca: "lala"
    }));
    anu(_make_kwargs({
        pa_pa: "lala",
        ca: "lala"
    }));
    anu(args);
    anu(kwargs);
    anu(kwargs, _make_kwargs({
        pa_pa: "lala",
        ca: "lala"
    }));
    prambanan.exports('', {});
})(prambanan);