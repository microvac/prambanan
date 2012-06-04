import prambanan.template

__all__ = ["is_js", "items", "get_template"]

is_js = False

def items(d):
    return d.items()

def get_template(type, config):
    providers = prambanan.template.all_providers()
    return providers[type].get_template(config)

