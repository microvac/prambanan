import time

t = time.time()
print int(t / 10000)

t = int(time.time() / 10000) * 10000
lt = time.localtime(t)
print time.ctime(t)
print time.asctime(lt)


