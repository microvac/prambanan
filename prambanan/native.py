import prambanan.template

is_js = False

def items(d):
    return d.items()

def get_template(type, config):
    providers = prambanan.template.all_providers()
    return providers[type].get(config)

