import prambanan
def print_dict(d):
    for name in sorted(iter(d)):
        print "%s: %s" % (name, d[name])

a = {"anu": "3"}
print a["anu"]
c = "anu"
print a[c]
print_dict(a)

a["kutumbaba"] = 5
print_dict(a)

del a["anu"]
print_dict(a)
