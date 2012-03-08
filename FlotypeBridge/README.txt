==============
Flotype Bridge
==============

This package provides a Python API to the `Flotype Bridge`__ service. It can
be used to write clients and servers that interact over Bridge.

Installation
============

    $ pip install FlotypeBridge

This package supports recent versions of Python 2 and Python 3. It depends
on `tornado <http://www.tornadoweb.org/>`_. 

Usage
=====

Getting started is as simple as;

    from flotype.bridge import Bridge

    bridge = Bridge(api_key='myapikey')

    bridge.ready(lambda: print('Connected to bridge.'))

The examples/ directory contains more sample code. The full Bridge API
reference can be found `here`__. The `getting started tutorial`__ may also
be useful.

__ http://www.flotype.com/
__ http://www.flotype.com/resources/api
__ http://www.flotype.com/resources/gettingstarted
