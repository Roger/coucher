Coucher
=======

A simple python couchdb api client library

Why another library?:
---------------------

* Because i needed something simple
* I don't wanted object mapping, i prefer to use `json-schema <http://json-schema.org/>`_ and validate when needed
* I wanted to use ijson, to reduce memory usage in big view responses

Features
--------

* Small and simple
* Uses the well tested `requests library <http://www.python-requests.org/>`_
* `ijson <https://github.com/isagalaev/ijson>`_ view iterators(big view responses with small memory footprint)


TODO
----

This is alpha software, use at your own risk, i'm not responsable of your dead kittens

* complete couchdb api
* design documents
* tests
* etc..
