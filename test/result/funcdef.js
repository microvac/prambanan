(function (prambanan) {
    var __builtin__, _class, _get_arg, _get_kwargs, _get_varargs, _init_args, anu, anu2, anu3, anu5, c, object;
    __builtin__ = prambanan.import('__builtin__');
    object = __builtin__.object;
    _init_args = prambanan.helpers.init_args;
    _get_kwargs = prambanan.helpers.get_kwargs;
    _class = prambanan.helpers.class;
    _get_arg = prambanan.helpers.get_arg;
    _get_varargs = prambanan.helpers.get_varargs;
    anu = function (a, b) {
        return a;
    };
    anu2 = function (a, b) {
        var _args;
        _args = _init_args(arguments);
        b = _get_arg(1, "b", _args, 3);
        c = 4 * 5;
        return a;
    };
    anu5 = function (a, b, c, e) {
        var _args;
        _args = _init_args(arguments);
        b = _get_arg(1, "b", _args, 3);
        c = _get_arg(2, "c", _args, 4);
        e = _get_arg(3, "e", _args, 5);
        c = 4 * 5;
        return a;
    };
    anu3 = function (a, b, args, kwargs) {
        var _args;
        _args = _init_args(arguments);
        b = _get_arg(1, "b", _args, 3);
        args = _get_varargs(2, _args);
        kwargs = _get_kwargs(_args);
        c = 4 * 5;
        return a;
    };

    function t__c_() {
        this.__init__.apply(this, arguments);
    }
    c = _class(t__c_, [object], function () {
        var anu2;
        anu2 = function (self, a, b) {
            var _args, self;
            _args = _init_args(arguments);
            b = _get_arg(2, "b", _args, 3);
            self = this;
            return self;
        };
        return [{anu2: anu2}, {}, {}]
    });
    prambanan.exports('', {anu: anu,anu2: anu2,anu3: anu3,anu5: anu5,c: c});
})(prambanan);