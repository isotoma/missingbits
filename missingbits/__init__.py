
from zc.buildout.buildout import Options


class Range(object):

    def __init__(self, buildout, name, options):
        start = int(options.get("start", 0))
        stop = int(options["stop"])
        step = int(options.get("step", 1))

        for key in options.keys():
            if key in ("recipe", "start", "stop", "step"):
                continue

            lst = [options[key].format(i) for i in range(start, stop, step)]
            options[key + ".forward"] = "\n".join(lst)

            lst.reverse()
            options[key + ".reverse"] = "\n".join(lst)

    def install(self):
        return ()

    update = install


class Cloner(object):

    def __init__(self, buildout, name, options):
        template = buildout._raw[options["template"]]

        start = int(options.get("start", 0))
        stop = int(options["stop"])
        step = int(options.get("step", 1))

        parts = []
        for i in range(start, stop, step):
            name = options["template"].format(i)
            o = Options(buildout, name, template)

            buildout._data[name] = o
            o._initialize()

            parts.append(name)
        print parts
        options["parts"] = "\n".join(parts)

    def install(self):
        return ()

    update = install



class Echo(object):

    def __init__(self, buildout, name, options):
        self.options = options

    def install(self):
        print self.options["echo"]
        return ()

    update = install

