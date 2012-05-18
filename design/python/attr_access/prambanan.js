(function(){
    var prambanan = this.prambanan = {};

    function t_object(){this.__init__.apply(this, arguments)}
    var object = t_object;
    object.prototype.toString = function(){
        if(this.__str__)
            return this.__str__();
        else
            return Object.prototype.toString.call(this);
    }
    object.extend = Backbone.Model.extend;
    prambanan.object = object;

    prambanan.dict = object.extend({
        "__getitem__": function(name){
            return this[name];
        }
    });

    prambanan.helpers = {
        get_item1: function(obj, name){
            return obj[name];
        },
        get_item2: function(obj, name){
            if (obj.__getitem__){
                return obj.__getitem__(name);
            } else {
                return obj[name];
            }
        }
    };

}).call(this)
