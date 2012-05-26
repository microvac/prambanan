(function(prambanan) {
    var __builtin__, _get_arg, _get_kwargs, _get_varargs, _init_args, _make_kwargs, iter, print, sorted, test1, test2, test3, test4, test5, test6, test7, test8, test9;
    __builtin__ = prambanan.import('__builtin__');
    print = __builtin__.print;
    sorted = __builtin__.sorted;
    iter = __builtin__.iter;
    _init_args = prambanan.helpers.init_args;
    _get_kwargs = prambanan.helpers.get_kwargs;
    _get_arg = prambanan.helpers.get_arg;
    _make_kwargs = prambanan.helpers.make_kwargs;
    _get_varargs = prambanan.helpers.get_varargs;
    test1 = function(a, b) {
        print("%d, %d".__mod__(a, b));
    };
    test1(2, 4);
    test2 = function(a, b) {
        var _args;
        _args = _init_args(arguments);
        b = _get_arg(1, "b", _args, 20);
        print("%d, %d".__mod__(a, b));
    };
    test2(2, 4);
    test2(2);
    test3 = function(args) {
        var _args, _i, _len, _list, a;
        _args = _init_args(arguments);
        args = _get_varargs(0, _args);
        _list = args;
        for (_i = 0, _len = _list.length; _i < _len; _i++) {
            a = _list[_i];
            print(a);
        }
    };
    test3();
    test3(1);
    test3(1, 2, 3, 4, 5, 6);
    test4 = function(i, args) {
        var _args, _i, _len, _list, a;
        _args = _init_args(arguments);
        args = _get_varargs(1, _args);
        _list = args;
        for (_i = 0, _len = _list.length; _i < _len; _i++) {
            a = _list[_i];
            print(a);
        }
    };
    test4(1);
    test4(1, 2, 3, 4, 5, 6);
    test5 = function(i, b, args) {
        var _args, _i, _len, _list, a;
        _args = _init_args(arguments);
        b = _get_arg(1, "b", _args, 77);
        args = _get_varargs(2, _args);
        print(b);
        _list = args;
        for (_i = 0, _len = _list.length; _i < _len; _i++) {
            a = _list[_i];
            print(a);
        }
    };
    test5(5);
    test5(8, 9, 10);
    test5(8, _make_kwargs({b: 20}));
    test6 = function(b, kwargs) {
        var _args, _i, _len, _list, a;
        _args = _init_args(arguments);
        b = _get_arg(0, "b", _args, 99);
        kwargs = _get_kwargs(_args);
        print(b);
        _list = sorted(iter(kwargs));
        for (_i = 0, _len = _list.length; _i < _len; _i++) {
            a = _list[_i];
            print(kwargs.get(a, "none"));
        }
    };
    test6(_make_kwargs({b: 31}));
    test6(_make_kwargs({b: 31,c: 4,e: 5}));
    test7 = function(args, kwargs) {
        var _args, _i, _i1, _len, _len1, _list, _list1, a;
        _args = _init_args(arguments);
        args = _get_varargs(0, _args);
        kwargs = _get_kwargs(_args);
        print("varargs");
        _list = args;
        for (_i = 0, _len = _list.length; _i < _len; _i++) {
            a = _list[_i];
            print(a);
        }
        print("kwargs");
        _list1 = sorted(iter(kwargs));
        for (_i1 = 0, _len1 = _list1.length; _i1 < _len1; _i1++) {
            a = _list1[_i1];
            print(kwargs.get(a, "none"));
        }
    };
    test7(1, 2, 3, _make_kwargs({a: 4,b: 5,c: 6}));
    test8 = function(wew, args, kwargs) {
        var _args, _i, _i1, _len, _len1, _list, _list1, a;
        _args = _init_args(arguments);
        args = _get_varargs(1, _args);
        kwargs = _get_kwargs(_args);
        print(wew);
        print("varargs");
        _list = args;
        for (_i = 0, _len = _list.length; _i < _len; _i++) {
            a = _list[_i];
            print(a);
        }
        print("kwargs");
        _list1 = sorted(iter(kwargs));
        for (_i1 = 0, _len1 = _list1.length; _i1 < _len1; _i1++) {
            a = _list1[_i1];
            print(kwargs.get(a, "none"));
        }
    };
    test8(1, 2, 3, _make_kwargs({a: 4,b: 5,c: 6}));
    test9 = function(kwargs) {
        var _args;
        _args = _init_args(arguments);
        kwargs = _get_kwargs(_args);
        print(kwargs.pop("a", 20));
        print(kwargs.pop("a", 30));
        print(kwargs.pop("b", 40));
    };
    test9(_make_kwargs({a: 4,b: 5,c: 6}));
    prambanan.exports('args', {test1: test1,test2: test2,test3: test3,test4: test4,test5: test5,test6: test6,test7: test7,test8: test8,test9: test9});
})(prambanan);