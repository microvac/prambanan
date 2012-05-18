var gi1 = prambanan.helpers.get_item1;
var gi2 = prambanan.helpers.get_item2;
var o = prambanan.object;
var attr = "name"

var target = {"name": "joko hendrawan"};
var obj_class = prambanan.dict.extend({
    constructor: function(){
        this[attr] = "joko surya";
    }
})
var obj_target = new obj_class();


function test_dot(){
    var res = null;
    for (var i = 0; i < 100; i++){
        res = target.name;
    }
    return res;
}

function test_brace(){
    var res = null;
    for (var i = 0; i < 100; i++){
        res = target[attr];
    }
    return res;
}

function test_gi1(){
    var res = null;
    for (var i = 0; i < 100; i++){
        res = gi1(target, attr);
    }
    return res;
}

function test_gi2(){
    var res = null;
    for (var i = 0; i < 100; i++){
        res = gi2(target, attr);
    }
    return res;
}

function test_gi1_obj(){
    var res = null;
    for (var i = 0; i < 100; i++){
        res = gi1(obj_target, attr);
    }
    return res;
}

function test_gi2_obj(){
    var res = null;
    for (var i = 0; i < 100; i++){
        res = gi2(obj_target, attr);
    }
    return res;
}

function test_get_item(){
    var res = null;
    for (var i = 0; i < 100; i++){
        res = obj_target.__getitem__(attr);
    }
    return res;
}
