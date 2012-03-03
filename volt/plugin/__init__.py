# -*- coding: utf-8 -*-
"""
-----------
volt.plugin
-----------

Base Volt plugin classes and functions.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>

"""

from functools import partial

from volt.util import grab_class


class Plugin(object):

    """Plugin base class.

    Volt plugins are subclasses of Plugin that perform a set of operations
    to ``Unit`` objects of a given engine. They are executed after all
    Engines finish parsing their units and before any output files are
    written. Plugin execution is handled by the ``Generator`` object in
    ``volt.gen``.

    During a ``Generator`` run, Volt tries first to look up a given plugin
    in the ``plugins`` directory in the project's root folder. Failing that,
    Volt will try to load the plugin from ``volt.plugin``.

    Default settings for a ``Plugin`` object should be stored as a class
    attribute dictionary named ``DEFAULT_ARGS``. They are then accessed from
    the ``CONFIG`` object from ``volt.config``, to allow for the Volt user
    to override them. Users can override any values in ``DEFAULT_ARGS``
    by instantiating a ``Config`` object named ``PLUGINS`` in ``voltconf.py``
    with the desired overrides.

    """

    # Set empty DEFAULT_ARGS to prevent generator from complaining
    # in case the plugin subclass does not define DEFAULT_ARGS
    # DEFAULT_ARGS is supposed to hold all values that a user might want to
    # change for any given plugin through his/her voltconf
    DEFAULT_ARGS = dict()


class Processor(Plugin):
    """Processor plugin base class.

    Processors are a type of Volt plugins that performs manipulation on units
    of a given gene. They might or might not output files during their
    execution. Two processor examples are included in the default Volt
    installation: the ``Markdown`` and ``SyntaxHighlighter`` processors. Both
    of these processors manipulate the content field of their target engines.

    Processors must implement a ``process`` function. This function is the entry
    point for processor execution by the ``Generator`` object.
    """
    def process(self):
        """Runs the processor."""
        raise NotImplementedError("Processor plugins must implement a process() method.")


get_processor = partial(grab_class, cls=Processor)