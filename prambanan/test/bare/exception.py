try:
    a = 3
except BaseException:
    print "a"

try:
    a = 3
except BaseException as b:
    print a.message

try:
    a = 3
except BaseException as b:
    print b.message
except ValueError as c:
    print c.message

try:
    a = 3
except BaseException as b:
    print b.message
except:
    print "a"

try:
    a = 3
except:
    print "a"

try:
    a = 3
finally:
    print "a"

