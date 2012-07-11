var getitem = function(econtext, name, dft){
    return econtext[name];
};

var deleteitem = function(econtext, name, backup, dft){
}

var convert_str = function(s){
    return new String(s);
}

var lookup_attr = function(obj, key){
    var res = obj[key];
    if (!res && obj.__getitem__){
        try{
            res = obj.__getitem__(key);
        }
        catch(e){
            return;
        }
    }
    return (typeof res == "function") ? _.bind(res, obj) : res;
}

var remove_el = function(el){
    $(el).remove();
}

var el_stack_push = function (tag){
    var child = document.createElement(tag);
    this.current.appendChild(child);
    this.stack.push(this.current)
    this.current = child;
}

var el_stack_node = function (node){
    try{
        var child = node;
        this.current.appendChild(child);
        this.stack.push(this.current)
        this.current = child;
    }
    catch(e){
        console.log(e);
    }
}

var el_stack_pop = function(){
    this.current = this.stack.pop();
}

var el_stack_text = function(text){
    var textNode = document.createTextNode(text);
    this.current.appendChild(textNode);
}

var el_stack_replay = function(tag){
    this.current = []
    var child = document.createElement(tag);
    $(this.replay_el).replaceWith(child);
    this.current = child;
    this.replay_el = child;
}

var el_stack_attr = function(name, value){
    this.current.setAttribute(name, value);
}

var __templates = window.prambanan.templates
if (! __templates.zpt){
    __templates.zpt = {
        templates: {},
        get_template: function(template_config){
            return this.templates[template_config[0]][template_config[1]];
        },
        export: function(namespace, path, render){
            var pack = this.templates[namespace] || (this.templates[namespace] = {})
            pack[path] = new PageTemplate(render);
        }
    }
}