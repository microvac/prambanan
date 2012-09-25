var $lib = this.prambanan;

var is_js= true;
var items= function(obj){
    var results = [];
    for (var key in obj){
        results.push([key, obj[key]])
    }
    return results;
}

var get_template = function(type, config){
    var templates = $lib.templates[type];
    if (!templates){
        throw new Error("cannot find template type: "+type)
    }
    return templates.get_template(config);
}

var wrap_on_error = $lib.helpers.wrap_on_error;

$lib.exports("prambanan", {"window": window, "document": document});
