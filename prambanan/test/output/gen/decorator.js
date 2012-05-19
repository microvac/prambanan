(function (prambanan) {
    var __builtin__, _get_varargs, _init_args, add, add2, add3, add_x, always_one, print;
    __builtin__ = prambanan.import('__builtin__');
    print = __builtin__.print;
    _init_args = prambanan.helpers.init_args;
    _get_varargs = prambanan.helpers.get_varargs;
    always_one = function (fn) {
        var res;
        res = function (args) {
            var _args;
            _args = _init_args(arguments);
            args = _get_varargs(0, _args);
            return 1;
        };
        return res;
    };
    add_x = function (x) {
        var res;
        res = function (fn) {
            var wrapped;
            wrapped = function (a, b) {
                return fn(x, b);
            };
            return wrapped;
        };
        return res;
    };
    add = function (x, y) {
        return x + y;
    };
    add2 = function (x, y) {
        return x + y;
    };
    add2 = always_one(add2);
    add3 = function (x, y) {
        return x + y;
    };
    add3 = add_x(10)(add3);
    print(add(3, 4));
    print(add2(3, 4));
    print(add3(5, 4));
    prambanan.exports('', {add: add,add2: add2,add3: add3,add_x: add_x,always_one: always_one});
})(prambanan);