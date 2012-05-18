var extend_dict = prambanan.helpers.extend_dict;
var extend_func = prambanan.helpers.extend_func;
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
