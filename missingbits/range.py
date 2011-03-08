
class Range(object):

    def __init__(self, buildout, name, options):
        start = int(options.get("start", 0))
        stop = int(options.get("stop", 0))
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

