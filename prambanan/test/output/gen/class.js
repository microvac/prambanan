(function(prambanan) {
    var Class1, Class2, Class3, Class4, Class5, Class6, __builtin__, _class, a, b, c, d, e, f, isinstance, object, print;
    __builtin__ = prambanan.import('__builtin__');
    print = __builtin__.print;
    object = __builtin__.object;
    isinstance = __builtin__.isinstance;
    _class = prambanan.helpers.class;

    function t_class_Class1() {
        this.__init__.apply(this, arguments);
    }
    /**
     * doc doc
     */
    Class1 = _class(t_class_Class1, [object], function() {
        var __init__, method1;
        __init__ = function(self) {
            var self;
            self = this;
            print("init 1");
        };
        method1 = function(self, b) {
            var self;
            self = this;
            b = 3;
            self = 3;
            print("method1");
        };
        return [{__init__: __init__,method1: method1}, {}, {}]
    });

    function t_class_Class2() {
        this.__init__.apply(this, arguments);
    }
    Class2 = _class(t_class_Class2, [Class1], function() {
        var __init__, method2;
        __init__ = function(self) {
            var self;
            self = this;
            print("init 2");
        };
        method2 = function(self) {
            var self;
            self = this;
            print("method2");
        };
        return [{__init__: __init__,method2: method2}, {}, {}]
    });

    function t_class_Class3() {
        this.__init__.apply(this, arguments);
    }
    Class3 = _class(t_class_Class3, [Class2, Class1], function() {
        var method3;
        method3 = function(self) {
            var self;
            self = this;
            print("method3");
        };
        return [{method3: method3}, {}, {}]
    });

    function t_class_Class4() {
        this.__init__.apply(this, arguments);
    }
    Class4 = _class(t_class_Class4, [Class3], function() {
        var method2, method4;
        method2 = function(self) {
            var self;
            self = this;
            print("method2-4");
        };
        method4 = function(self) {
            var self;
            self = this;
            print("method4");
        };
        return [{method2: method2,method4: method4}, {}, {}]
    });

    function t_class_Class5() {
        this.__init__.apply(this, arguments);
    }
    Class5 = _class(t_class_Class5, [object], function() {
        var __init__, method4, method5;
        __init__ = function(self) {
            var self;
            self = this;
            print("init 1");
        };
        method4 = function(self) {
            var self;
            self = this;
            print("method4-5");
        };
        method5 = function(self) {
            var self;
            self = this;
            print("method5");
        };
        return [{__init__: __init__,method4: method4,method5: method5}, {}, {}]
    });

    function t_class_Class6() {
        this.__init__.apply(this, arguments);
    }
    Class6 = _class(t_class_Class6, [Class4, Class5], function() {
        var __init__, method1, method6;
        __init__ = function(self) {
            var self;
            self = this;
            print("init 3");
        };
        method1 = function(self) {
            var self;
            self = this;
            print("method1-5");
        };
        method6 = function(self) {
            var self;
            self = this;
            print("method6");
        };
        return [{__init__: __init__,method1: method1,method6: method6}, {}, {}]
    });
    a = new Class1();
    b = new Class2();
    c = new Class3();
    d = new Class4();
    e = new Class5();
    f = new Class6();
    print(isinstance(a, Class1));
    print(isinstance(a, Class2));
    print(isinstance(a, Class3));
    print(isinstance(b, Class1));
    print(isinstance(b, Class2));
    print(isinstance(b, Class3));
    print(isinstance(c, Class3));
    print(isinstance(c, Class2));
    print(isinstance(c, Class1));
    f.method1();
    f.method2();
    f.method3();
    f.method4();
    f.method5();
    f.method6();
    print(isinstance(f, Class5));
    prambanan.exports('class', {Class1: Class1,Class2: Class2,Class3: Class3,Class4: Class4,Class5: Class5,Class6: Class6});
})(prambanan);