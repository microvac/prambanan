var etree = 1;

var getitem = function(econtext, name, dft){
    return econtext[name];
};

var deleteitem = function(econtext, name, backup, dft){
}

var convert_str = function(s){
    return new String(s);
}

var lookup_attr = function(obj, key){
    return obj[key];
}

var el_stack_push = function (tag){
    var child = document.createElement(tag);
    this.current.appendChild(child);
    this.stack.push(this.current)
    this.current = child;
}

var el_stack_pop = function(){
    this.current = this.stack.pop();
}

var el_stack_text = function(text){
    var textNode = document.createTextNode(text);
    this.current.appendChild(textNode);
}

var el_stack_attr = function(name, value){
    if(name == "style"){

    } else {
        this.current.setAttribute(name, value);
    }
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