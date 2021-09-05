==============
 Jaeger Client
==============

Summary
=======

This module provides a function decorator to utilize tracing with the
`Jaeger <https://www.jaegertracing.io>`_ stack.

Prerequisits
============

* jaeger_client and pyyaml python modules are installed
* jaeger agent is up and running beside your odoo

Configuration
=============

The decorator loads configuration file ``~/.config/jaeger.yaml`` at tracer initialization.
If not found it creates it with the default settings:

.. code-block:: yaml

   config:
     logging: true
     sampler:
       param: 1
       type: const
   service_name: odoo

Usage
=====

.. highlight:: python

To instrument your apps, you can use the decorator provided by the module, like this::

   # -*- coding: utf-8 -*-
   from odoo import http
   from odoo.addons.jaeger_tracer import jaeger
   from odoo.addons.website.controllers.main import Website


   class Website(Website):
       n = 42

       @jaeger.span(tags={'fact.n': n})
       def jaeger_test(self, n):
           '''Doing nothing except testing jaeger while counting the factorial of n'''
           fact = 1
           for i in range(1, n+1):
               fact = fact * i
           return fact

       @jaeger.span(tags={'my.tag': 'my_value'})
       @http.route('/', type='http', auth="public", website=True, sitemap=True)
       def index(self, **kw):
           '''Inheriting the basic website controller for testing jaeger'''
           res = super(Website, self).index(**kw)
           self.jaeger_test(self.n)
           return res

.. image:: static/img/jaeger_ui.png

Check out the official documentation for more:

* `Opentracing tutorial <https://github.com/yurishkuro/opentracing-tutorial/tree/master/python>`_
* `Python Jaeger Client documentation <https://github.com/jaegertracing/jaeger-client-python>`_

Authors
=======

* János Gerzson (@grzs)
