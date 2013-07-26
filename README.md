prambanan
=========

Yet another Python to Javascript Compiler, it uses logilab astng for parsing python ast. The resulting javascript will have dependencies to underscore.js and small prambanan runtime.

It will be ideal if prambanan:
 1. generate code with small size
 2. generate fast code
 3. supports all python feature

Of course there's conflict in those requirement, So prambanan will choose to not support a python feature if by supporting it make code much bigger / much slower. But by doing that, prambanan will have no easy exact specification, and need to define it in future.

Currently prambanan is used by single page application framework [borobudur](https://github.com/microvac/borobudur)

There's also a collection of prambanan python-javascript libraries to be used at [pramjs](https://github.com/microvac/pramjs)
