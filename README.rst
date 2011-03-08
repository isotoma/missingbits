MissingThings
=============

This package provides several recipes you can use if you find your self duplicating
lots of config. It also has echo, which turned out to be useful for testing.

It was created for a site which uses 1, 3 or 9 zopes depending on a set of conditions.

missingthings:range
-------------------

This recipe takes a string and will make a list out of it. For example, where as you
could write:

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

You can write:

    [buildout]
    parts = cluster

    [zopes]
    recipe = missingthings:range
    stop = 6
    cluster-start = ${buildout:bin-directory}/zope{0} start
    cluster-stop = ${buildout:bin-directory}/zope{0} stop

    [cluster]
    recipe = plone.recipe.cluster
    start = ${zopes:cluster-start.forward}
    stop = ${zopes:cluster-stop.reverse}

This is most useful when the number of zopes might vary for different builds of
the same site.


missingthings:clone
-------------------

A site with 4 zopes might look something like this:

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
could do this instead:

    [buildout]
    parts = ${zope-factory:parts}

    [zope{0}]
    <= instance
    http-address = ${hosts:zope}:${ports:zope{0}}
    event-log = /var/log/zope/www.foo.bar.zope{0}.event.log
    z2-log = /var/log/zope/www.foo.bar.zope{0}.Z2.log

    [zope-factory]
    recipe = missingthings:clone
    template = zope{0}
    count = 4


missingthings:echo
------------------

While testing these recipes it was handy to have a no-op recipe that just printed
some text. This is that recipe.

You can print text from your buildout like so:

    [buildout]
    parts = echo

    [echo]
    recipe = missingthings:echo
    echo = Any text you want here

