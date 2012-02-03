# Copyright 2011 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

class Overlay(object):
    """ Overlay every member of a part on top of a list of other parts """

    def __init__(self, buildout, name, options):
        config = buildout.get(name, {}).copy()
        if config.has_key('recipe'):
            del config['recipe']

        for source in self._resolve_deps(config):
            destinations = self._strip(
                config.get(source, '').splitlines()
            )

            for dest in destinations:
                logger = logging.getLogger(name).debug(
                    'overlaying %s onto %s' % (source, dest)
                )
                keys = buildout._raw.get(source, {})
                for key in keys:
                    if not buildout._raw[dest].has_key(key):
                        buildout._raw[dest][key] = keys[key]

    def _strip(self, options):
        return [item for item in options if not item == '']

    def _resolve_deps(self, config):
        """ Determine the dependencies between parts in the overlay part """
        visited = []
        sorted_keys = []
        only_inherits = []

        # populate only_inherits with parts that aren't inherited by others
        for values in config.itervalues():
            for item in self._strip(values.splitlines()):
                if not item in config.keys() and not item in only_inherits:
                    only_inherits.append(item)

        def applied_to(from_key):
            """ Return a part names that are applied to the given key """
            for key in config:
                if from_key in self._strip(config[key].splitlines()):
                    yield key

        def visit(key):
            """ Recursively process any not-yet-visited part names """
            if not key in visited:
                visited.append(key)
                for part in applied_to(key):
                    visit(part)
                sorted_keys.append(key)

        for key in only_inherits:
            visit(key)

        return sorted_keys

    def install(self):
        return ()

    update = install


class Select(object):

    def __init__(self, buildout, name, options):
        section = buildout[options["case"]]

        for k, v in section.iteritems():
            if k.startswith("_"):
                continue
            options[k] = v

    def install(self):
        return ()

    update = install


class Range(object):

    def __init__(self, buildout, name, options):
        start = int(options.get("start", 0))
        stop = int(options["stop"])
        step = int(options.get("step", 1))

        for key in options.keys():
            if key in ("recipe", "start", "stop", "step"):
                continue

            lst = [options[key].replace("{0}", str(i)).replace("$$", "$") for i in range(start, stop, step)]
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
            name = options["template"].replace("{0}", str(i)).replace("$$", "$")
            config = dict((k, v.replace("{0}", str(i)).replace("$$","$")) for (k, v) in template.iteritems())

            buildout._raw[name] = config

            parts.append(name)

        options["parts"] = "\n".join(parts)

        if options.get("trigger-dependencies", "true").lower() in ("true", "yes", "on"):
            [buildout[part] for part in parts]

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

