(function(){
    var prambanan = this.prambanan = {};
    var builtins = {};
    var helpers = prambanan.helpers = {};
    var slice = Array.prototype.slice;
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
                    modules[key] = {}
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
                m = dotNotateModule(ns);
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
            i: function(list, index){
                return index >= 0
                    ? list[index]
                    : list[list.length + index]
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
            i: function(list, index){
                list.remove(index);
            },
            s: function(list, start, stop, step){
                if(step != null){
                    throw new Error("delete slice with step not implemented");
                }
                list.remove(start, stop);
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
            return builtins.type(ctor, bases, instance_attrs, static_attrs);
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
        int: Number,
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
        sorted: function(l){
            return _.sortBy(l, function(i){return i;});
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

    /* object, generated  from builtins.py */
    var ArithmeticError, AttributeError, BaseException, Exception, IndexError, KeyError, LookupError, NameError,
        NotImplementedError, RuntimeError, StandardError, SystemError, TypeError, ValueError, ZeroDivisionError;


    function t___builtin___BaseException(){
        this.__init__.apply(this, arguments);
    }
    BaseException = object.extend({constructor: t___builtin___BaseException,
        __init__: function (message) {
            if(Error.captureStackTrace)
                Error.captureStackTrace(this);
            this.message = message;
        }
    });

    function t___builtin___Exception(){ this.__init__.apply(this, arguments); }
    Exception = BaseException.extend({constructor: t___builtin___Exception/* pass */
    });

    function t___builtin___StandardError(){ this.__init__.apply(this, arguments); }
    StandardError = Exception.extend({constructor: t___builtin___StandardError/* pass */
    });

    function t___builtin___AttributeError(){ this.__init__.apply(this, arguments); }
    AttributeError = StandardError.extend({constructor: t___builtin___AttributeError/* pass */
    });

    function t___builtin___TypeError(){ this.__init__.apply(this, arguments); }
    TypeError = StandardError.extend({constructor: t___builtin___TypeError/* pass */
    });

    function t___builtin___ValueError(){ this.__init__.apply(this, arguments); }
    ValueError = StandardError.extend({constructor: t___builtin___ValueError/* pass */
    });

    function t___builtin___NameError(){ this.__init__.apply(this, arguments); }
    NameError = StandardError.extend({constructor: t___builtin___NameError/* pass */
    });

    function t___builtin___SystemError(){ this.__init__.apply(this, arguments); }
    SystemError = StandardError.extend({constructor: t___builtin___SystemError/* pass */
    });

    function t___builtin___LookupError(){ this.__init__.apply(this, arguments); }
    LookupError = StandardError.extend({constructor: t___builtin___LookupError/* pass */
    });

    function t___builtin___KeyError(){ this.__init__.apply(this, arguments); }
    KeyError = LookupError.extend({constructor: t___builtin___KeyError/* pass */
    });

    function t___builtin___IndexError(){ this.__init__.apply(this, arguments); }
    IndexError = LookupError.extend({constructor: t___builtin___IndexError/* pass */
    });

    function t___builtin___ArithmeticError(){ this.__init__.apply(this, arguments); }
    ArithmeticError = StandardError.extend({constructor: t___builtin___ArithmeticError/* pass */
    });

    function t___builtin___ZeroDivisionError(){ this.__init__.apply(this, arguments); }
    ZeroDivisionError = ArithmeticError.extend({constructor: t___builtin___ZeroDivisionError/* pass */
    });

    function t___builtin___RuntimeError(){ this.__init__.apply(this, arguments); }
    RuntimeError = StandardError.extend({constructor: t___builtin___RuntimeError/* pass */
    });

    function t___builtin___NotImplementedError(){ this.__init__.apply(this, arguments); }
    NotImplementedError = RuntimeError.extend({constructor: t___builtin___NotImplementedError/* pass */
    });

    prambanan.exports('__builtin__',{
        ArithmeticError: ArithmeticError,
        AttributeError: AttributeError,
        BaseException: BaseException,
        Exception: Exception,
        IndexError: IndexError,
        KeyError: KeyError,
        LookupError: LookupError,
        NameError: NameError,
        NotImplementedError: NotImplementedError,
        RuntimeError: RuntimeError,
        StandardError: StandardError,
        SystemError: SystemError,
        TypeError: TypeError,
        ValueError: ValueError,
        ZeroDivisionError: ZeroDivisionError
    });

    /*
     Monkey Paaaaatches
     make some objects to behave like python
     */

    (function(){
        var name = "python.Array";

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
            remove: function(from, to) {
                var rest = this.slice((to - 1 || from) + 1 || this.length);
                this.length = from < 0 ? this.length + from : from;
                return this.push.apply(this, rest);
            },
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
            }
        });
        prambanan.patch(name);
    })();

    (function(){
        var name = "python.String";

        var sprintfWrapper = {
            init : function () {
                var string = arguments[0];
                var exp = new RegExp(/(%([%]|(\-)?(\+|\x20)?(0)?(\d+)?(\.(\d)?)?([bcdfosxX])))/g);
                var matches = new Array();
                var strings = new Array();
                var convCount = 0;
                var stringPosStart = 0;
                var stringPosEnd = 0;
                var matchPosEnd = 0;
                var newString = '';
                var match = null;
                var substitution = null;

                while ((match = exp.exec(string))) {
                    if (match[9])
                        convCount += 1;

                    stringPosStart = matchPosEnd;
                    stringPosEnd = exp.lastIndex - match[0].length;
                    strings[strings.length] = string.substring(stringPosStart, stringPosEnd);

                    matchPosEnd = exp.lastIndex;
                    matches[matches.length] = {
                        match: match[0],
                        left: match[3] ? true : false,
                        sign: match[4] || '',
                        pad: match[5] || ' ',
                        min: match[6] || 0,
                        precision: match[8],
                        code: match[9] || '%',
                        negative: parseInt(arguments[convCount]) < 0 ? true : false,
                        argument: String(arguments[convCount])
                    };
                }
                strings[strings.length] = string.substring(matchPosEnd);

                if (matches.length == 0)
                    return string;

                var code = null;
                var match = null;
                var i = null;

                for (i=0; i<matches.length; i++) {
                    if (matches[i].code == '%') { substitution = '%' }
                    else if (matches[i].code == 'b') {
                        matches[i].argument = String(Math.abs(parseInt(matches[i].argument)).toString(2));
                        substitution = sprintfWrapper.convert(matches[i], true);
                    }
                    else if (matches[i].code == 'c') {
                        matches[i].argument = String(String.fromCharCode(parseInt(Math.abs(parseInt(matches[i].argument)))));
                        substitution = sprintfWrapper.convert(matches[i], true);
                    }
                    else if (matches[i].code == 'd') {
                        matches[i].argument = String(Math.abs(parseInt(matches[i].argument)));
                        substitution = sprintfWrapper.convert(matches[i]);
                    }
                    else if (matches[i].code == 'f') {
                        matches[i].argument = String(Math.abs(parseFloat(matches[i].argument)).toFixed(matches[i].precision ? matches[i].precision : 6));
                        substitution = sprintfWrapper.convert(matches[i]);
                    }
                    else if (matches[i].code == 'o') {
                        matches[i].argument = String(Math.abs(parseInt(matches[i].argument)).toString(8));
                        substitution = sprintfWrapper.convert(matches[i]);
                    }
                    else if (matches[i].code == 's') {
                        matches[i].argument = matches[i].argument.substring(0, matches[i].precision ? matches[i].precision : matches[i].argument.length)
                        substitution = sprintfWrapper.convert(matches[i], true);
                    }
                    else if (matches[i].code == 'x') {
                        matches[i].argument = String(Math.abs(parseInt(matches[i].argument)).toString(16));
                        substitution = sprintfWrapper.convert(matches[i]);
                    }
                    else if (matches[i].code == 'X') {
                        matches[i].argument = String(Math.abs(parseInt(matches[i].argument)).toString(16));
                        substitution = sprintfWrapper.convert(matches[i]).toUpperCase();
                    }
                    else {
                        substitution = matches[i].match;
                    }

                    newString += strings[i];
                    newString += substitution;
                }

                newString += strings[i];
                return newString;
            },
            convert : function(match, nosign){
                if (nosign)
                    match.sign = '';
                else
                    match.sign = match.negative ? '-' : match.sign;

                var l = match.min - match.argument.length + 1 - match.sign.length;
                var pad = new Array(l < 0 ? 0 : l).join(match.pad);
                if (!match.left) {
                    if (match.pad == "0" || nosign)
                        return match.sign + pad + match.argument;
                    else
                        return pad + match.sign + match.argument;
                } else {
                    if (match.pad == "0" || nosign)
                        return match.sign + match.argument + pad.replace(/0/g, ' ');
                    else
                        return match.sign + match.argument + pad;
                }
            }
        };

        prambanan.registerPrototypePatch(name, String.prototype, {
            __mod__: function () {
                args = Array.prototype.slice.call(arguments, 0);
                args.splice(0, 0, this);
                return sprintfWrapper.init.apply(this, args);
            },
            startswith: function (s) {
                return this.slice(0,s.length) == s;
            },
            endswith: function (s) {
                return this.slice(this.length-s.length) == s;
            },
            join: function(col){
                result = "";
                for (var i = 0; i < col.length; i++){
                    result+=col[i];
                    if(i != col.length - 1)
                        result+=this;
                }
                return result;
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

}).call(this)
