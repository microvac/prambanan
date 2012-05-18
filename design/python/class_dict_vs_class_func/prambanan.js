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

    function type(ctor, bases, attrs, static_attrs){
        if (ctor){
            attrs.constructor = ctor;
        } else if (attrs.__init__){
            attrs.constructor = attrs.__init__;
        }
        var result = bases[0].extend(attrs);
        return result;
    }

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
        class: function(name, bases, fn){
            var attrs = fn();
            var instance_attrs = attrs[0];
            var static_attrs = attrs[1];
            return type(name, bases, instance_attrs, static_attrs);
        },
    };

}).call(this)
