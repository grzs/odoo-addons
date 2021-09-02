==============
 Jaeger Client
==============

Summary
=======

This module when installed, initializes the global opentracing.tracer object
for `Jaeger <https://www.jaegertracing.io>`_,
with configuration parameters loaded from file ~/.config/jaeger.yaml. If no config file
exists the init function poplutes it with default values.

Prerequisits
============

* jaeger_client and pyyaml python modules are installed
* jaeger agent is up and running beside your odoo

Usage
=====

To instrument your apps, follow the steps written in the
`opentracing tutorial <https://github.com/yurishkuro/opentracing-tutorial/tree/master/python>`_
or the `Python Jaeger Client documentation <https://github.com/jaegertracing/jaeger-client-python>`_.

Authors
=======

* János Gerzson (@grzs)
