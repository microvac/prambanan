var extend_dict = prambanan.helpers.extend_dict;
var extend_func = prambanan.helpers.extend_func;
var extend_class = prambanan.helpers.class;
var o = prambanan.object;

function test_dict(){
    var ctor = function(){};
    kutumbaba1 = extend_dict([o], ctor, {
        "a": function(){
            return 1;
        },
        "b": function(a, b){
            return a+b;
        },
        "c": function(a, b, c){
            return a+b+c;
        }
    },
    {
        "s1": function(a, b, c){
            return a+b+c;
        }
    });
}

function test_func(){
    var ctor = function(){};
    kutumbaba2 = extend_func([o], ctor, function(cls){
        var proto = cls.prototype;
        proto.a = function(){
            return 1;
        };
        proto.b = function(a, b){
            return a+b;
        };
        proto.c = function(a, b, c){
            return a+b+c;
        };
        cls.s1= function(a, b, c){
            return a+b+c;
        };
   });
}

function test_func_1(){
    var ctor = function(){};
    kutumbaba3 = extend_func([o], ctor, function(cls){
        var a, b, c, s1, e;
        var proto = cls.prototype;
        e = 4+3;
        a = function(){
            return 1;
        };
        b = function(a, b){
            return a+b;
        };
        c = function(a, b, c){
            return a+b+c;
        };
        s1= function(a, b, c){
            return a+b+c;
        };
        proto.a = a;
        proto.b = b;
        proto.c = c;
        cls.e = proto.e = e;
        cls.s1 = s1;
   });
}

function test_func_2(){
    var ctor = function(){};
    kutumbaba4 = extend_func([o], ctor, function(cls){
        var a, b, c, s1;
        var proto = cls.prototype;
        a = function(){
            return 1;
        };
        b = function(a, b){
            return a+b;
        };
        c = function(a, b, c){
            return a+b+c;
        };
        s1= function(a, b, c){
            return a+b+c;
        };
        _.extend(proto, {
            "a": a,
            "b": b,
            "c": c,
        });
        _.extend(cls, {
            "s1": s1,
        });
   });
}

function test_class(){
    function ctor(){};
    kutumbaba4 = extend_class(ctor, [o], function(){
        var a, b, c, s1;
        a = function(){
            return 1;
        };
        b = function(a, b){
            return a+b;
        };
        c = function(a, b, c){
            return a+b+c;
        };
        s1= function(a, b, c){
            return a+b+c;
        };
        return [
            {
            "a": a,
            "b": b,
            "c": c
            },
            {"s1": s1}
        ]
   });
}
