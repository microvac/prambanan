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

    prambanan.helpers = {
        extend_dict: function(bases, ctor, instance_attrs, static_attrs){
            var mixins = [];
            if (ctor){
                instance_attrs.constructor = ctor;
            } else if (instance_attrs.__init__){
                instance_attrs.constructor = instance_attrs.__init__;
            }
            var result = bases[0].extend(instance_attrs, static_attrs);
            return result;
        },
        extend_func: function(bases, ctor, fn){
            var mixins = [];
            var instance_attrs = {};
            if (ctor){
                instance_attrs.constructor = ctor;
            } else if (instance_attrs.__init__){
                instance_attrs.constructor = instance_attrs.__init__;
            }
            var result = bases[0].extend(instance_attrs);
            fn(result);
            return result;
        },
    };

}).call(this)
