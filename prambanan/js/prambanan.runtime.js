(function(){
    var root = this;
    var prambanan = root.prambanan = {};
    var helpers = prambanan.helpers = {};
    function Module(){};
    var builtins = new Module();
    var slice = Array.prototype.slice;
    prambanan.templates = {}
    /*
     Module import and exports
     */
    _.extend(prambanan, (function(){
        var modules = {};
        var dotNotateModule = function(s){
            var splitted = s.split(".");
            var current = modules;
            for(var i = 0; i < splitted.length; i++){
                var key = splitted[i];
                if(_.isUndefined(modules[key])){
                    modules[key] = new Module();
                }
                current = modules[key];
            }
            return current;

        }

        return {
            import: function(ns){
                return dotNotateModule(ns);
            },
            exports: function(ns, values){
                var m = dotNotateModule(ns);
                for(key in values){
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
     Compiler helpers
     */
    var subscriptFunctions = {
        l: {
            i: function(obj, index){
                if (obj.__getitem__)
                    return obj.__getitem__(index);
                return obj[index];
            },
            s: function(list, start, stop, step){
                if(step == null){
                    return list.slice(start, stop);
                }
                else {
                    var result = [];
                    if(start == null)
                        start = 0;
                    if(stop == null)
                        stop = list.length;
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

    _isSubClass= function(child, parent){
        if(!_.isFunction(parent))
            return false;
        if (child == parent)
            return true;
        if(child.__super__ ){
            if (_isSubClass(child.__super__.constructor, parent)){
                return true;
            }
        }
        if(child.__mixins__){
            for(var i = 0; i < child.__mixins__.length; i++){
                if (_isSubClass(child.__mixins__[i].constructor, parent)){
                    return true;
                }
            }
            return false;
        }
        return false;
    }

    function KwArgs(items){
        this.items = items || {};
    }
    KwArgs.prototype.get = function(name, dft){
        if(_.has(this.items, name))
            return this.items[name];
        return dft;
    }
    KwArgs.prototype.pop = function(name, dft){
        if(_.has(this.items, name)){
            var result = this.items[name];
            delete this.items[name]
            return result;
        }
        return dft;
    }


    _.extend(helpers, {
        subscript: subscriptFunctions,
        pow: Math.pow,
        _:_,
        throw:function(obj, file, lineno){
            obj.file = file;
            obj.lineno = lineno;
            throw obj;
        },
        iter: function(obj){
            return builtins.iter(obj);
        },
        super: function(obj, attr){
            return _.bind((obj.constructor.__super__)[attr], obj)
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
        isinstance : function (obj, cls){
            if (obj instanceof cls)
                return true;
            if (!obj.constructor)
                return false;
            return _isSubClass(obj.constructor, cls);
        },
        in: function(item, col){
            if (_.isArray(col)){
                return _.contains(col, item)
            }
            return _.has(col, item)
        },
        make_kwargs: function(items){
            return new KwArgs(items);
        },
        init_args: function(args){
            return slice.call(args,0);
        },
        get_arg : function(index, name, args, dft){
            var arg;
            if(index < args.length){
                arg = args[index];
                if (! (arg instanceof KwArgs))
                    return arg;
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
            return slice.call(args, start, end);
        },
        get_kwargs:function(args){
            var arg  = args[args.length - 1];
            return arg instanceof KwArgs ? arg : new KwArgs();

        }
    });


    /*
     builtins module
     */
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

        max: Math.max,
        min: Math.min,
        abs: Math.abs,
        round: Math.round,

        all: function(l){
            return _.all(l, function(c){return c === true; })
        },
        any: function(l){
            return _.any(l, function(c){return c === true; })
        },
        len: function(obj){
            return _.isArray(obj) || _.isString(obj) ? obj.length : _.keys(obj).length;
        },
        reverse: function (a) {
            return a.reverse();
        },
        sorted: function(l, key){
            key = helpers.get_arg(1, "key", arguments, function(i){return i;});
            return _.sortBy(l, key);
        },
        enumerate: function(o){
            return _.map(o, function(i, idx){return [idx, i]})
        },
        set:_.uniq,

        zip:_.zip,
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

        range: _.range,
        xrange:_.range,

        print: function(s){
            var _s = builtins.str(s)
            if (typeof console != "undefined"){
                console.log(_s);
                return;
            }
            else if (typeof print != "undefined"){
                print(_s)
                return;
            }
        },

        isinstance: function(obj, type){
            return prambanan.helpers.isinstance(obj, type);
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
                for (var i = 1; i < bases.length; i++){
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

            return result;
        },
        __import__: function(ns){
            return prambanan.import(ns);
        },
        super: function(cls, self){
        },
        iter: function(o){
            if(_.isArray(o))
                return o;
            if(o instanceof KwArgs){
                return _.keys(o.items);
            }
            if(_.isObject(o))
                return _.keys(o)
            return o;
        },
        None: null
    });


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
    prambanan.exports("__builtin__", builtins);


    /*
     Monkey Paaaaatches
     make some objects to behave like python
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
                for (var i = 0; i < this.length; i++){
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

    function sprintf () {
        // http://kevin.vanzonneveld.net
        // +   original by: Ash Searle (http://hexmen.com/blog/)
        // + namespaced by: Michael White (http://getsprink.com)
        // +    tweaked by: Jack
        // +   improved by: Kevin van Zonneveld (http://kevin.vanzonneveld.net)
        // +      input by: Paulo Freitas
        // +   improved by: Kevin van Zonneveld (http://kevin.vanzonneveld.net)
        // +      input by: Brett Zamir (http://brett-zamir.me)
        // +   improved by: Kevin van Zonneveld (http://kevin.vanzonneveld.net)
        // *     example 1: sprintf("%01.2f", 123.1);
        // *     returns 1: 123.10
        // *     example 2: sprintf("[%10s]", 'monkey');
        // *     returns 2: '[    monkey]'
        // *     example 3: sprintf("[%'#10s]", 'monkey');
        // *     returns 3: '[####monkey]'
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

    (function(){
        var name = "python.String";

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
            join: function(col){
                var result = "";
                for (var i = 0; i < col.length; i++){
                    result+=col[i];
                    if(i != col.length - 1)
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
