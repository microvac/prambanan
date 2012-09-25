(function(){
    var root = this;
    var prambanan = root.prambanan = {};
    prambanan.Error = root.Error;

    function Module(){};

    var helpers = prambanan.helpers = {};
    var modules = prambanan.modules = {};
    var builtins = prambanan.builtins = new Module();
    var templates = prambanan.templates = {}

    prambanan.modules["__builtin__"] = builtins;

    var arraySlice = Array.prototype.slice;

    prambanan.has_error = false;
    _.extend(prambanan, {
        load: function(file, fn){
            if (prambanan.has_error)
                return;
            prambanan.current_file = file;
            try {
                helpers.wrap_on_error(fn)(prambanan);
            } catch(e){
                prambanan.has_error = true;
                throw e;
            }

        }
    });

    /*
     Module import and exports
     */
    _.extend(prambanan, (function(){
        var dotNotateModule = function(s){
            var splitted = s.split(".");
            var current = modules;
            for(var i = 0, len = splitted.length; i < len; i++){
                var key = splitted[i];
                current = current[key] || (current[key] = new Module());
            }
            return current;

        }

        return {
            import: function(ns){
                return dotNotateModule(ns);
            },
            exports: function(ns, values){
                var m = dotNotateModule(ns);
                for(var key in values){
                    m[key] = values[key];
                }
            }
        }
    })());

    /*
     Monkey patching mechanism
     */
    _.extend(prambanan, (function(){
        var patches = {};
        return {
            patch: function(name){
                var patch = patches[name];
                if(!patch.applied){
                    patch.patch();
                    patch.applied = true;
                }
            },
            unpatch: function(name){
                var patch = patches[name];
                if(patch.applied){
                    patch.unpatch();
                    patch.applied = false;
                }
            },
            registerPatch: function(name, callback){
                patches[name] = callback;
            },
            registerPrototypePatch: function(name, prototype, patches){
                var original = {};
                var originalExists = {};
                _.each(_.keys(patches), function(key){
                    original[key] = prototype[key]
                    originalExists[key]= _.has(prototype, key);
                });
                this.registerPatch(name, {
                    patch: function(){
                        _.each(_.keys(patches), function(k){
                            prototype[k] = patches[k];
                        });
                    },
                    unpatch: function(){
                        _.each(_.keys(patches), function(k){
                            if(originalExists[k]){
                                prototype[k] = original[k];
                            }
                            else {
                                delete prototype[k];
                            }
                        });
                    }
                });
            }
        }
    })());

    /*
     Helpers Functions
     it is a function that is used by compiler
    */

    /* subscripts helper */
    var subscript = {
        l: {
            i: function(obj, index){
                var res;
                if (obj.__getitem__)
                    res = obj.__getitem__(index);
                else
                    res = obj[index];
                if (_.isUndefined(res)){
                    var err_type = _.isArray(obj) ? builtins.IndexError : builtins.KeyError;
                    helpers.throw(new err_type(index), prambanan.current_file, null, new Error());
                }
                return res;
            },
            s: function(list, start, stop, step){
                if(start == null)
                    start = 0;
                if(stop == null)
                    stop = list.length;

                if(step == null){
                    return list.slice(start, stop);
                }
                else {
                    var result = [];
                    for(var i = start; i < stop; i+=step){
                        result.push(list[i])
                    }
                    return result;
                }
            }
        },
        d: {
            i: function(obj, index){
                if (obj.__delitem__){
                    obj.__delitem__(index)
                } else {
                    delete obj[index]
                }
            },
            s: function(list, start, stop, step){
                if(step != null){
                    for (var i = start; i < stop; i+= step){
                        this.i(list, i);
                    }
                }
                list.remove(start, stop);
            }
        },
        s: {
            i: function(obj, index, value){
                if(obj.__setitem__){
                    obj.__setitem__(index, value);
                }else{
                    obj[index] = value;
                }
            },
            s: function(list, start, stop, step, value){
                if (step == null){
                    step = 1;
                }
                for (var i = start, j = 0; i < stop; i+= step, j++){
                    this.i(list, i, value[j])
                }
            }
        }
    }


    /* Keyword arguments type */
    function KwArgs(items){
        this.items = items || {};
    }
    _.extend(KwArgs.prototype, {
       get:  function(name, dft){
           if(_.has(this.items, name))
               return this.items[name];
           return dft;
       },
       pop: function(name, dft){
        if(_.has(this.items, name)){
            var result = this.items[name];
            delete this.items[name]
            return result;
        }
        return dft;
        }
    });

    function print_exception(e){
        window.e = e;
        if (e.stack){
            //chrome
            console.error("%s: %o. on file: '%s' line: %s\n%o %o", e.__class__.name, e.__str__(), e.file, e.lineno, e, e.stack);
        }
        else {
            //firefox
            console.group(e);
            console.error(e.stacks[e.stacks.length-1]);
            console.groupEnd();
        }
    }

    _.extend(helpers, {
        subscript: subscript,
        pow: Math.pow,
        _:_,
        throw:function(obj, file, lineno, err){
            obj.file = file;
            obj.lineno = lineno;
            if (!obj.stacks){
                obj.stacks = [];
            }
            obj.stacks.unshift(err);
            return obj;
        },
        iter: function(obj){
            return builtins.iter(obj);
        },
        super: function(cls, obj, attr){
            return _.bind((cls.__super__)[attr], obj)
        },
        class: function(ctor, bases, fn){
            var attrs = fn();
            var instance_attrs = attrs[0];
            var static_attrs = attrs[1];
            var all_attrs = attrs[2];

            for (var prop in all_attrs) {
                instance_attrs[prop] = all_attrs[prop];
                static_attrs[prop] = all_attrs[prop];
            }
            var creator = all_attrs.__metaclass__ || bases[0].prototype.__metaclass__ || builtins.type;
            return creator(ctor, bases, instance_attrs, static_attrs);
        },
        in: function(item, col){
            if (!_.isUndefined(col) && col.__contains__){
                return col.__contains__(item);
            }
            if (_.isArray(col)){
                return _.contains(col, item)
            }
            if (_.isString(col)){
                return col.indexOf(item) != -1
            }
            return _.has(col, item)
        },
        make_kwargs: function(items){
            return new KwArgs(items);
        },
        init_args: function(args){
            return arraySlice.call(args,0);
        },
        get_arg : function(index, name, args, dft){
            var arg;
            if(index < args.length){
                arg = args[index];
                if (! (arg instanceof KwArgs)){
                    if(_.isUndefined(arg))
                        return dft;
                    return arg;
                }
                return arg.pop(name, dft);
            }

            arg = args[args.length - 1];
            if (arg instanceof KwArgs)
                return arg.pop(name, dft);
            return dft;
        },
        get_varargs: function(index, args){
            var result = [];
            var start = index;
            var end = args[args.length - 1] instanceof KwArgs ? args.length - 1 : args.length;
            return arraySlice.call(args, start, end);
        },
        get_kwargs:function(args){
            var arg  = args[args.length - 1];
            return arg instanceof KwArgs ? arg : new KwArgs();

        },
        wrap_on_error: function(fn){
            if (console && console.error){
                var wrapped = function(){
                    try{
                        fn.apply(this, arguments);
                    }
                    catch(e){
                        if(e.__str__){
                            print_exception(e);
                        } else {
                            throw e;
                        }
                    }
                }
                return wrapped;
            }
            else {
                return fn;
            }
        }
    });

    /* Builtins Module */

    /* Builtins function that also acted as type */
    _.extend(builtins, {
        bool: function(i) {return !!i;},
        int: function(i){
            return Math.round(Number(i));
        },
        float: Number,
        str: function(o){
            if (!_.isUndefined(o) && o.__str__){
                return o.__str__();
            }
            if(_.isBoolean(o))
                return o ? "True" : "False";
            return String(o);
        },
        basestring: String,
        unicode: String,
        dict: function(o){
            if (o instanceof KwArgs)
                return _.extend({}, o.items);
            return _.extend({}, o);
        },
        list: function(o){
            if (_.isArray(o))
                return o;
            if (o.__iter__)
                return o.__iter__();
            throw new Error("not implemented");
        },
        tuple: function(o){
            throw new Error("not implemented");
        },
        set:_.uniq
    });

    // map of their builtins function type to javascript's type
    var builtin_types = {
        bool: Boolean,
        int: Number,
        float: Number,
        str: String,
        basestring: String,
        unicode: String,
        dict: Object,
        list: Array,
        tuple: Array,
        set: Array
    };

    // save it in __jstype__ attributes (used by __builtins__.isinstance)
    for(var typ in builtin_types){
        builtins[typ].__jstype__ = builtin_types[typ];
    }


    _.extend(builtins, {
        // python's None -> javascript's null
        None: null,

        // imports delegate to prambanan import but only pass its first dotted name
        __import__: function(ns){
            return prambanan.import(ns.split(".")[0]);
        },

        /* Methods can be delegated to Math */
        max: Math.max,
        min: Math.min,
        abs: Math.abs,
        round: Math.round,

        /* Attributes Methods */
        getattr: function(obj, name, dft){
            var res = obj[name];
            if (_.isUndefined(res))
                return dft
            return res
        },
        hasattr: function(obj, name){
            return !_.isUndefined(obj[name]);
        },
        setattr: function(obj, name, value){
            obj[name] = value;
        },
        dir: function(obj){
            results = [];
            for (var key in obj)
                results.push(key);
            return results;
        },

        /*
        Array functions, delegate to underscore
        most of these have reversed arguments
        */
        zip:_.zip,
        range: _.range,
        xrange:_.range,

        iter: function(o){
            if(_.isArray(o))
                return o;
            if(o instanceof KwArgs){
                return _.keys(o.items);
            }
            if(_.isObject(o)){
                if (o.__iter__){
                    return o.__iter__();
                }
                return _.keys(o)
            }
            return o;
        },

        all: function(l){
            return _.all(l, function(c){return c === true; })
        },
        any: function(l){
            return _.any(l, function(c){return c === true; })
        },
        len: function(obj){
            if(obj.__len__){
                return obj.__len__()
            }
            return _.isArray(obj) || _.isString(obj) ? obj.length : _.keys(obj).length;
        },
        reversed: function (a) {
            return a.slice(0).reverse();
        },
        sorted: function(l, key){
            key = helpers.get_arg(1, "key", arguments, function(i){return i;});
            return _.sortBy(l, key);
        },
        enumerate: function(o){
            return _.map(o, function(i, idx){return [idx, i]})
        },
        map: function(f, l){
            return _.map(l, f);
        },
        filter: function(f, l){
            return _.filter(l, f);
        },
        reduce: function(f, l, i){
            return _.reduce(l, function(memo, num){f(num, memo)}, i);
        },
        sum: function(f, l, i){
            return _.reduce(l, function(memo, num){f(num + memo)}, i);
        },

        /* Object Utilites */


        super: function(cls, self){
            throw new Error("super is not implemented, use super in helpers instead");
        },
        isinstance : function (obj, cls){
            if (obj === null)
                return false;
            if(cls.__jstype__)
                return obj.constructor == cls.__jstype__;
            if (obj instanceof cls)
                return true;
            if (!obj.constructor)
                return false;
            return builtins.issubclass(obj.constructor, cls);
        },
        issubclass: function(child, parent){
            if(!_.isFunction(parent))
                return false;
            if (child == parent)
                return true;
            if(child.__super__ ){
                if (builtins.issubclass(child.__super__.constructor, parent)){
                    return true;
                }
            }
            if(child.__mixins__){
                for(var i = 0; i < child.__mixins__.length; i++){
                    if (builtins.issubclass(child.__mixins__[i].constructor, parent)){
                        return true;
                    }
                }
                return false;
            }
            return false;
        },
        type:  function(ctor, bases, attrs, static_attrs){
            if (arguments.length == 1)
                return ctor.constructor;

            if (ctor){
                attrs.constructor = ctor;
            } else if (attrs.__init__){
                attrs.constructor = attrs.__init__;
            }
            var result = bases[0].extend(attrs, static_attrs)
            var mixins = [];
            if(bases.length > 1){
                for (var i = 1, len = bases.length; i < len; i++){
                    var current = bases[i];
                    for(var key in current){
                        if(!(_.has(result, key)))
                            result[key] = current[key];
                    }
                    for(var key in current.prototype){
                        if(!(key in result.__super__))
                            result.prototype[key] = current.prototype[key];
                    }
                    mixins.push(current.prototype);
                }
            }
            result.__mixins__ = mixins;
            result.prototype.__class__ = result.prototype.constructor;

            return result;
        }
    });

    /*
        delegate builtin print to global.console or global.print
    */
    if (root.console){
        builtins.print = root.console.log.bind(console)
    }
    else {
        builtins.print = function(s){
            var _s = builtins.str(s)
            if (typeof print != "undefined"){
                print(_s)
            }
        }
    }

    /*
    __builtins__.object
    that one class to base them all
    */
    function t_object(){this.__init__.apply(this, arguments)}
    var object = builtins.object = t_object;
    _.extend(object.prototype, {
        toString: function(){
            if(this.__str__)
                return this.__str__();
            else
                return Object.prototype.toString.call(this);
        },
        __init__: function(){}
    })
    object.extend = Backbone.Model.extend;



    /*
     Monkey Patches definition
     make some prototypes have python equivalent attributes
     */

    (function(){
        var name = "python.Array";

        var arrayRemove = function(from, to) {
            var rest = this.slice((to - 1 || from) + 1 || this.length);
            this.length = from < 0 ? this.length + from : from;
            return this.push.apply(this, rest);
        };

        prambanan.registerPrototypePatch(name, Array.prototype,  {
            insert: function(index, object){
                this.splice(index, 0, object);
            },
            append: function (object) {
                this[this.length] = object;
            },
            extend: function (list) {
                this.push.apply(this, list);
            },
            remove: arrayRemove,
            __delitem__: arrayRemove,
            pop: function (index) {
                if (_.isUndefined(index))
                    index = this.length-1;

                if (index == -1 || index >= this.length)
                    return undefined;

                var elt = this[index];
                this.splice(index, 1);
                return elt;
            },
            __str__: function(){
                var result = "[";
                for (var i = 0, len = this.length; i < len; i++){
                    if (i != 0)
                        result+=", ";
                    result += builtins.str(this[i]);
                }
                result += "]";
                return result;
            },
            __setitem__: function(index, value){
                this[index] = value;
            },
            __getitem__: function(index){
                return index < 0
                    ? this[this.length + index]
                    : this[index];
            }
        });
        prambanan.patch(name);
    })();

    (function(){
        var name = "python.String";

        function sprintf () {
            // http://kevin.vanzonneveld.net
            var regex = /%%|%(\d+\$)?([-+\'#0 ]*)(\*\d+\$|\*|\d+)?(\.(\*\d+\$|\*|\d+))?([scboxXuidfegEG])/g;
            var a = arguments,
                i = 0,
                format = a[i++];

            // pad()
            var pad = function (str, len, chr, leftJustify) {
                if (!chr) {
                    chr = ' ';
                }
                var padding = (str.length >= len) ? '' : Array(1 + len - str.length >>> 0).join(chr);
                return leftJustify ? str + padding : padding + str;
            };

            // justify()
            var justify = function (value, prefix, leftJustify, minWidth, zeroPad, customPadChar) {
                var diff = minWidth - value.length;
                if (diff > 0) {
                    if (leftJustify || !zeroPad) {
                        value = pad(value, minWidth, customPadChar, leftJustify);
                    } else {
                        value = value.slice(0, prefix.length) + pad('', diff, '0', true) + value.slice(prefix.length);
                    }
                }
                return value;
            };

            // formatBaseX()
            var formatBaseX = function (value, base, prefix, leftJustify, minWidth, precision, zeroPad) {
                // Note: casts negative numbers to positive ones
                var number = value >>> 0;
                prefix = prefix && number && {
                    '2': '0b',
                    '8': '0',
                    '16': '0x'
                }[base] || '';
                value = prefix + pad(number.toString(base), precision || 0, '0', false);
                return justify(value, prefix, leftJustify, minWidth, zeroPad);
            };

            // formatString()
            var formatString = function (value, leftJustify, minWidth, precision, zeroPad, customPadChar) {
                if (precision != null) {
                    value = value.slice(0, precision);
                }
                return justify(value, '', leftJustify, minWidth, zeroPad, customPadChar);
            };

            // doFormat()
            var doFormat = function (substring, valueIndex, flags, minWidth, _, precision, type) {
                var number;
                var prefix;
                var method;
                var textTransform;
                var value;

                if (substring == '%%') {
                    return '%';
                }

                // parse flags
                var leftJustify = false,
                    positivePrefix = '',
                    zeroPad = false,
                    prefixBaseX = false,
                    customPadChar = ' ';
                var flagsl = flags.length;
                for (var j = 0; flags && j < flagsl; j++) {
                    switch (flags.charAt(j)) {
                        case ' ':
                            positivePrefix = ' ';
                            break;
                        case '+':
                            positivePrefix = '+';
                            break;
                        case '-':
                            leftJustify = true;
                            break;
                        case "'":
                            customPadChar = flags.charAt(j + 1);
                            break;
                        case '0':
                            zeroPad = true;
                            break;
                        case '#':
                            prefixBaseX = true;
                            break;
                    }
                }

                // parameters may be null, undefined, empty-string or real valued
                // we want to ignore null, undefined and empty-string values
                if (!minWidth) {
                    minWidth = 0;
                } else if (minWidth == '*') {
                    minWidth = +a[i++];
                } else if (minWidth.charAt(0) == '*') {
                    minWidth = +a[minWidth.slice(1, -1)];
                } else {
                    minWidth = +minWidth;
                }

                // Note: undocumented perl feature:
                if (minWidth < 0) {
                    minWidth = -minWidth;
                    leftJustify = true;
                }

                if (!isFinite(minWidth)) {
                    throw new Error('sprintf: (minimum-)width must be finite');
                }

                if (!precision) {
                    precision = 'fFeE'.indexOf(type) > -1 ? 6 : (type == 'd') ? 0 : undefined;
                } else if (precision == '*') {
                    precision = +a[i++];
                } else if (precision.charAt(0) == '*') {
                    precision = +a[precision.slice(1, -1)];
                } else {
                    precision = +precision;
                }

                // grab value using valueIndex if required?
                value = valueIndex ? a[valueIndex.slice(0, -1)] : a[i++];

                switch (type) {
                    case 's':
                        return formatString(String(value), leftJustify, minWidth, precision, zeroPad, customPadChar);
                    case 'c':
                        return formatString(String.fromCharCode(+value), leftJustify, minWidth, precision, zeroPad);
                    case 'b':
                        return formatBaseX(value, 2, prefixBaseX, leftJustify, minWidth, precision, zeroPad);
                    case 'o':
                        return formatBaseX(value, 8, prefixBaseX, leftJustify, minWidth, precision, zeroPad);
                    case 'x':
                        return formatBaseX(value, 16, prefixBaseX, leftJustify, minWidth, precision, zeroPad);
                    case 'X':
                        return formatBaseX(value, 16, prefixBaseX, leftJustify, minWidth, precision, zeroPad).toUpperCase();
                    case 'u':
                        return formatBaseX(value, 10, prefixBaseX, leftJustify, minWidth, precision, zeroPad);
                    case 'i':
                    case 'd':
                        number = (+value) | 0;
                        prefix = number < 0 ? '-' : positivePrefix;
                        value = prefix + pad(String(Math.abs(number)), precision, '0', false);
                        return justify(value, prefix, leftJustify, minWidth, zeroPad);
                    case 'e':
                    case 'E':
                    case 'f':
                    case 'F':
                    case 'g':
                    case 'G':
                        number = +value;
                        prefix = number < 0 ? '-' : positivePrefix;
                        method = ['toExponential', 'toFixed', 'toPrecision']['efg'.indexOf(type.toLowerCase())];
                        textTransform = ['toString', 'toUpperCase']['eEfFgG'.indexOf(type) % 2];
                        value = prefix + Math.abs(number)[method](precision);
                        return justify(value, prefix, leftJustify, minWidth, zeroPad)[textTransform]();
                    default:
                        return substring;
                }
            };

            return format.replace(regex, doFormat);
        }

        prambanan.registerPrototypePatch(name, String.prototype, {
            __mod__: function () {
                var args = Array.prototype.slice.call(arguments, 0);
                args.splice(0, 0, this);
                return sprintf.apply(this, args);
            },
            startswith: function (s) {
                return this.slice(0,s.length) == s;
            },
            endswith: function (s) {
                return this.slice(this.length-s.length) == s;
            },
            lower: String.prototype.toLowerCase,
            upper: String.prototype.toUpperCase,
            title: String.prototype.toUpperCase,
            strip: String.prototype.trim,
            join: function(col){
                var result = "";
                for (var i = 0, len = col.length; i < len; i++){
                    result+=col[i];
                    if(i != len - 1)
                        result+=this;
                }
                return result;
            },
            reverse: function(){
                var s = "";
                var i = this.length;
                while (i>0) {
                    s += this.substring(i-1,i);
                    i--;
                }
                return s;
            }
        });
        prambanan.patch(name);

        prambanan.registerPrototypePatch(name, Number.prototype, {
            __mod__: function (value) {
                return this % value;
            }
        });
        prambanan.patch(name);
    })();

}).call(this);
