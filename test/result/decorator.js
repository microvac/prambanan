(function (prambanan) {
    var Anu, _class, _make_kwargs, cache, cache2, cached_method, cached_method2, cached_method3, cached_method4, cached_method5;
    _class = prambanan.helpers.class;
    _make_kwargs = prambanan.helpers.make_kwargs;
    cache = function (fn) {
        return fn;
    };
    cache2 = function (fn, anu) {
        return fn;
    };
    cached_method = function (i) {
        return i * 4;
    };
    cached_method = cache(cached_method);
    cached_method2 = function (i) {
        return i * 4;
    };
    cached_method2 = cache()(cached_method2);
    cached_method3 = function (i) {
        return i * 4;
    };
    cached_method3 = cache2(3)(cached_method3);
    cached_method4 = function (i) {
        return i * 4;
    };
    cached_method4 = cache(cache2(3)(cache(cache2(3)(cached_method4))));
    cached_method5 = function (i) {
        return i * 4;
    };

    function t__Anu_() {
        this.__init__.apply(this, arguments);
    }
    Anu = _class(t__Anu_, [obj], function () {
        i = 4;
        return [{}, {}, {}]
    });
    Anu = cache2(_make_kwargs({}))(Anu);
    prambanan.exports('', {Anu: Anu,cache: cache,cache2: cache2,cached_method: cached_method,cached_method2: cached_method2,cached_method3: cached_method3,cached_method4: cached_method4,cached_method5: cached_method5});
})(prambanan);