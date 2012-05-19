a = [1,2,3]
print a

a.append(4)
print a

print a[1]
print a[-1]
print a[1:2]

a.extend([4,5,6,7,8])
a.extend(a)
print a

print a[1::3]
print a[1:7:3]

del a[2]
print a
del a[2]
print a
del a[2:5]
print a

b = a.pop()
print a
print b

b = a.pop(2)
print a
print b

a.insert(3, 10)
print a

