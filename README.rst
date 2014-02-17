Coucher
=======

.. image:: https://secure.travis-ci.org/Roger/coucher.png?branch=master
   :target: http://travis-ci.org/Roger/coucher
.. image:: https://coveralls.io/repos/Roger/coucher/badge.png :target: https://coveralls.io/r/Roger/coucher 

A simple python couchdb api client library

Why another library?
--------------------

* Because I needed something simpler
* I didn't want object mapping, i prefer using `json-schema <http://json-schema.org/>`_ and validate when needed
* I wanted to use ijson, to reduce memory usage in big view responses

Features
--------

* Small and simple
* Uses the well tested `requests library <http://www.python-requests.org/>`_
* View iterators(big view responses with small memory footprint, only one doc in memory for iteration)


TODO
----

This is alpha software, use at your own risk, i'm not responsible for your dead kittens

* complete couchdb api
* design documents
* tests
* etc..
