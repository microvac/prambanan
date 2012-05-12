(function (prambanan) {
    var __builtin__, _extend, _get_arg, _get_kwargs, _get_varargs, anu, anu2, anu3, anu5, c, object, t__c_;
    __builtin__ = prambanan.import('__builtin__');
    object = __builtin__.object;
    _get_varargs = prambanan.helpers.get_varargs;
    _get_kwargs = prambanan.helpers.get_kwargs;
    _get_arg = prambanan.helpers.get_arg;
    _extend = prambanan.helpers.extend;
    anu = function (a, b) {
        return a;
    };
    anu2 = function (a, b) {
        var _args, c;
        _args = arguments;
        b = _get_arg(1, "b", _args, 3);
        c = 4 * 5;
        return a;
    };
    anu5 = function (a, b, c, e) {
        var _args;
        _args = arguments;
        b = _get_arg(1, "b", _args, 3);
        c = _get_arg(2, "c", _args, 4);
        e = _get_arg(3, "e", _args, 5);
        c = 4 * 5;
        return a;
    };
    anu3 = function (a, b, args, kwargs) {
        var _args, c;
        _args = arguments;
        b = _get_arg(1, "b", _args, 3);
        args = _get_varargs(2, _args);
        kwargs = _get_kwargs(_args);
        c = 4 * 5;
        return a;
    };

    function t__c_() {
        this.__init__.apply(this, arguments);
    }
    c = _extend([object], t__c_, {
        anu2: function (a, b) {
            var _args, self;
            _args = arguments;
            b = _get_arg(2, "b", _args, 3);
            self = this;
            return self;
        }
    });
    prambanan.exports('', {
        anu: anu,
        anu2: anu2,
        anu3: anu3,
        anu5: anu5,
        c: c
    });
})(prambanan);