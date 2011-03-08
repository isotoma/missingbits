
class Echo(object):

    def __init__(self, buildout, name, options):
        self.options = options

    def install(self):
        print self.options["echo"]
        return ()

    update = install

