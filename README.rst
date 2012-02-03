missingbits
===========

This package provides several recipes you can use if you find your self duplicating
lots of config. It also has echo, which turned out to be useful for testing.

It was created for a site which uses 1, 3 or 9 zopes depending on a set of conditions.


missingbits:range
-------------------

This recipe takes a string and will make a list out of it. For example, where as you
could write::

    [buildout]
    parts = cluster

    [cluster]
    recipe = plone.recipe.cluster
    start =
        ${buildout:bin-directory}/zope0 start
        ${buildout:bin-directory}/zope1 start
        ${buildout:bin-directory}/zope2 start
        ${buildout:bin-directory}/zope3 start
        ${buildout:bin-directory}/zope4 start
        ${buildout:bin-directory}/zope5 start
    stop =
        ${buildout:bin-directory}/zope5 stop
        ${buildout:bin-directory}/zope4 stop
        ${buildout:bin-directory}/zope3 stop
        ${buildout:bin-directory}/zope2 stop
        ${buildout:bin-directory}/zope1 stop
        ${buildout:bin-directory}/zope0 stop

You can write::

    [buildout]
    parts = cluster

    [zopes]
    recipe = missingbits:range
    stop = 6
    cluster-start = ${{buildout:bin-directory}}/zope{0} start
    cluster-stop = ${{buildout:bin-directory}}/zope{0} stop

    [cluster]
    recipe = plone.recipe.cluster
    start = ${zopes:cluster-start.forward}
    stop = ${zopes:cluster-stop.reverse}

This is most useful when the number of zopes might vary for different builds of
the same site.

Parameters
~~~~~~~~~~

start
    Number to start the range at (Default: 0, Optional)
stop
    Number to stop at, but not including. So start of 0 and stop of 6 will get you [0,1,2,3,4,5]. (Mandatory).
step
    Number to increment by. (Default: +1, Optional)
foo
    Foo is any variable you choose to set on the recipe. A number of duplicates will be made of it and
    a newline seperated list placed in an output variable. Any occurence of {0} will be replaced with
    a number for the item in the range we are up to. You can delay evaluation of any buildout variables
    you are using by escaping them ({{ and }}). If you don't do this, buildout will have to evaluate them
    before it evaluates this recipe and you might change the order the parts run in.
foo.forward
    If you set a variable called foo on the recipe, it will make a foo.forward. This contains the list
    in ascending order.
foo.reverse
    If you set a variable called foo on the recipe, it will make a foo.reverse. This contains the list
    in descending order.


missingbits:clone
-------------------

I don't like copying and pasting things in buildout, i tend to make mistakes. So I clone instead.

A site with 4 zopes might look something like this::

    [buildout]
    parts =
        zope0
        zope1
        zope2
        zope3

    [zope0]
    <= instance
    http-address = ${hosts:zope}:${ports:zope0}
    event-log = /var/log/zope/www.foo.bar.zope0.event.log
    z2-log = /var/log/zope/www.foo.bar.zope0.Z2.log

    [zope1]
    <= instance
    http-address = ${hosts:zope}:${ports:zope1}
    event-log = /var/log/zope/www.foo.bar.zope1.event.log
    z2-log = /var/log/zope/www.foo.bar.zope1.Z2.log

    [zope2]
    <= instance
    http-address = ${hosts:zope}:${ports:zope2}
    event-log = /var/log/zope/www.foo.bar.zope2.event.log
    z2-log = /var/log/zope/www.foo.bar.zope2.Z2.log

    [zope3]
    <= instance
    http-address = ${hosts:zope}:${ports:zope3}
    event-log = /var/log/zope/www.foo.bar.zope3.event.log
    z2-log = /var/log/zope/www.foo.bar.zope3.Z2.log

When the number of zopes can change, we really need to make this more manageable. We
could do this instead::

    [buildout]
    parts = zope-factory

    [zope{0}]
    <= instance
    http-address = ${{hosts:zope}}:${{ports:zope{0}}}
    event-log = /var/log/zope/www.foo.bar.zope{0}.event.log
    z2-log = /var/log/zope/www.foo.bar.zope{0}.Z2.log

    [zope-factory]
    recipe = missingbits:clone
    template = zope{0}
    count = 4

Parameters
~~~~~~~~~~

template
    A part to use as a base for cloning. It should not be referenced in parts and it should not be
    reference by other parts, especially if it has a recipe. Any buildout variables it has will
    need to be escaped by using {{ and }}. Any occurences of {0} will be replaced by the number of
    the clone we are on.
start
    Number to start the range at (Default: 0, Optional)
stop
    Number to stop at, but not including. So start of 0 and stop of 6 will get you [0,1,2,3,4,5]. (Mandatory).
step
    Number to increment by. (Default: +1, Optional)
parts
    This variable is set by the recipe and contains a list of the parts that were generated. You can
    pass it to any recipe taking a list of parts, but you cannot pass it to ${buildout:parts} as
    the buildout part is evaluated too early.


missingbits:select
------------------

This recipe can be used to change what configuration is used base on other
variables. For example, it is most excellent when combined with
isotoma.recipe.facts::

    [facts]
    recipe = isotoma.recipe.facts

    [host-lucid]
    somesetting = 1

    [host-karmic]
    somesetting = 2

    [host]
    recipe = missingbits:select
    case = ${facts:lsb.codename}

With this example, you would be able to use ``${host:somesetting}`` and know
that it is suitable for the environment you are in.


missingbits:echo
------------------

While testing these recipes it was handy to have a no-op recipe that just printed
some text. This is that recipe.

You can print text from your buildout like so::

    [buildout]
    parts = echo

    [echo]
    recipe = missingbits:echo
    echo = Any text you want here


Repository
----------

This software is available from our `recipe repository`_ on github.

.. _`recipe repository`: http://github.com/isotoma/missingbits


License
-------

Copyright 2011 Isotoma Limited

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


