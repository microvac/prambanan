var Prambanan = window.Prambanan = {};

/*
    Module import and exports
 */
_.extend(Prambanan, (function(){
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
_.extend(Prambanan, (function(){
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
_.extend(Prambanan, (function(){
    var subscriptFunctions = {
        load: function(){
            var functions = {
                index: function(list, index){
                    return list[index];
                },
                slice: function(list, start, stop, step){
                    if(_.isUndefined(step))
                        return list.slice(start, stop);
                    //todo: stepping
                }
            };
        },
        del: function(){
        },
        assign: function(){
        }
    }
    return {
        subscript: function(contextType, list, methodType, start, stop, step){
            return subscriptFunctions[contextType](list, methodType, start, stop, step);
        }
    }
})());

/*
    builtins module
 */
(function(){
    var builtins = {
        bool: function(i) {return !!i;},
        int: Number,
        float: Number,
        str: String,
        basestring: String,
        unicode: String,

        max: Math.max,
        min: Math.min,
        abs: Math.abs,
        round: Math.round,

        all: function(l){ return _.all(l, function(c){return c === true; })},
        any: function(l){ return _.any(l, function(c){return c === true; })},
        len: _.size,
        reverse: function (a) {return a.reverse(); },

        zip:_.zip,
        map: function(f, l){ return _.map(l, f); },
        filter: function(f, l){ return _.filter(l, f); },
        reduce: function(f, l, i){ return _.reduce(l, function(memo, num){f(num, memo)}, i); },
        sum: function(f, l, i){ return _.reduce(l, function(memo, num){f(num + memo)}, i); },

        range: _.range,
        xrange:_.range,

        print: function(s){
            if(console && console.log)
                console.log(s);
        },

        isinstance: function(obj, type){
            return obj instanceof type;
        },
        __import__: function(ns){
            return Prambanan.import(ns);
        },
        super: function(cls, self){
        },
        None: null
    }


    builtins.object = function(){};
    builtins.object.extend = Backbone.Model.extend;

    builtins.Error = builtins.object.extend();

    Prambanan.exports("__builtin__", builtins);
})();


/*
    Monkey Paaaaatches
    make some objects to behave like python
*/

(function(){
    var name = "python.Array";

    Prambanan.registerPrototypePatch(name, Array.prototype,  {
        insert: function(index, object){
            this.splice(index, 0, object);
        },
        append: function (object) {
            this[this.length] = object;
        },
        pop: function (index) {
            if (_.isUndefined(index))
                index = this.length-1;

            if (index == -1 || index >= this.length)
                return undefined;

            var elt = this[index];
            this.splice(index, 1);
            return elt;
        }
    });
    Prambanan.patch(name);
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

    Prambanan.registerPrototypePatch(name, String.prototype, {
        sprintf: function () {
            args = Array.prototype.slice.call(arguments, 0);
            args.splice(0, 0, this);
            return sprintfWrapper.init.apply(this, args);
        },
        startswith: function (s) {
            return this.slice(0,s.length) == s;
        },
        endswith: function (s) {
            return this.slice(this.length-s.length) == s;
        }
    });
    Prambanan.patch(name);
})();

