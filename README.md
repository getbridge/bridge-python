bridge-python
=============

Ref Structures
-> {Local,Remote}Ref should remain distinct.
-> bridge.children should point to an instance of Ref.
-> LocalRefs should have attached services.
-> RemoteRefs serve only as proxies.

0. To Do

	- Docs
	- More rigid data validation.
	- Exception handling in connection.py.

1. Installation

	bridge-python depends on [tornado](http://www.tornadoweb.org/) and can make good use of [simplejson](http://pypi.python.org/pypi/simplejson/), though the latter is not strictly necessary.
