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

import os, copy, sys
from zc.buildout.buildout import _update, _open, _unannotate, _print_annotate
from zc.buildout import UserError
import zc.buildout.easy_install
import pkg_resources
import logging


def sibpath(module, path):
    __import__(module)
    mod = sys.modules[module]
    return os.path.join(os.path.dirname(mod.__file__), path)

def split(var):
    var = var.strip().split("\n")
    for itm in var:
        itm = itm.strip()
        if not itm:
            continue
        yield itm


class Stack(object):

    def __init__(self, name, buildout):
        """
        ``name`` is the name of the module that is providing a stack. It is used
        for the logger, locating files within the stack egg and to namespace the
        various debug commands.

        ``buildout`` is a buildout object as passed by the ``load`` extension
        entrypoint.
        """
        self.name = name
        self.buildout = buildout

        self.log = logging.getLogger(self.name)

        self.ensure_section(self.name)
        config = buildout[self.name]
        config['path'] = sibpath(self.name, "")

        self.original = copy.deepcopy(self.buildout._annotated)
        self.data = copy.deepcopy(self.buildout._annotated)

        self._reset_data()

        # Build a set of extensions defined already
        self.previous_keys = set(buildout['buildout'].keys())
        self.previous_extensions = set(split(buildout['buildout'].get('extensions', '')))

    def ensure_section(self, name):
        """ Ensure that a section exists, even if it is empty """
        self.buildout._raw.setdefault(name, {})

    def _reset_data(self):
        '''
        This method controversially deletes any already-resolved parts from
        buildout._data, excluding the buildout and versions parts, both of
        which are dealt with separately.

        The logic behind doing this is that after the stack has been applied
        to the configuration dictionary, the original non-stack buildout is
        re-applied, so ultimately no configuration is lost.
        '''
        excludes = (
            self.name,
            'buildout',
            self.buildout['buildout'].get('versions', '')
        )

        for k in self.buildout._data.keys():
            if not k in excludes:
                del self.buildout._data[k]

    def load(self, path, optional=False):
        config_file = sibpath(self.name, path)
        if not os.path.exists(config_file):
            if not optional:
                raise UserError("Could not load '%s'" % path)
            return

        self.log.debug("Loading '%s' from stack" % config_file)
        override = {}
        _update(self.data, _open(os.path.dirname(config_file), config_file, [],
                               self.data['buildout'].copy(), override)) #, set()))

    def peek_unloaded(self, path, section, key):
        """ Peek inside a buildout.cfg without applying it to the active buildout state """
        config_file = sibpath(self.name, path)
        if not os.path.exists(config_file):
            raise UserError("Could not peek in '%s'" % config_file)
        from ConfigParser import ConfigParser
        c = ConfigParser()
        c.read(config_file)
        value = c.get(section, key)
        if "${" in value:
            raise UserError("%s cannot peek at ${%s:%s} because it uses variable substitution or escaping." % (self.name, section, key))
        return value

    def peek(self, section, key):
        """
        Peek at the current state of self.data

        This will throw an exception in the following cases:

          * The section isn't currently loaded
          * The key could not be found in the section
          * The value contains buildout substitutions - peeking should not cause the state to be modified
        """

        __doing__ = "Peeking into section '${%s:}'" % section
        if not section in self.data:
            raise UserError("There is no section %s currently loaded" % section)

        __doing__ = "Peeking into key %s in section '%s'" % (section, key)
        s = self.data[section]
        if not key in s:
            raise UserError("Could not peek at ${%s:%s}" % (section, key))

        __doing__ = "Checking whether ${%s:%s} is safe to peek" % (section, key)
        value = s[key][0]
        if "${" in value:
            raise UserError("${%s:%s} uses variable substitutions and cannot be accessed" % (section, key))

        return value

    def apply(self):
        """
        Actually apply the config changes to the running buildout.
        """
        self.before_apply = _unannotate(copy.deepcopy(self.data))

        # Reinject the original buildout so it can overlay and extend the one from the stack
        _update(self.data, self.buildout._annotated)

        self.buildout._annotated = copy.deepcopy(self.data)
        self.buildout._raw = _unannotate(self.data)

        self.determine_cwd()
        self.update_buildout_options()
        self.update_versions()
        self.load_extensions()

        self.run_commands()

    def substitute(self, section, key):
        """
        Force the evaluation of a ``key`` in a ``section``
        """
        if not section in self.buildout._data:
            # Section hasn't been resolved at all, so leave it till later
            return
        if key in self.buildout._data[section]:
            del self.buildout._data[section][key]
        self.buildout[section]._dosub(key, self.buildout._raw[section][key])

    def update_versions(self):
        """
        Reconfigure easy_install with new version pinnings obtained from the stack
        """
        del self.buildout._data['versions']
        zc.buildout.easy_install.default_versions(self.buildout["versions"])

    def update_buildout_options(self):
        """
        Some values in [buildout] cannot safely be changed after they are set in the main buildout.

        We white list some that can:
         * 'parts' has to be refreshed or the parts the stack creates are never used
         * Any variables that were added to the buildout object by the stack are allowed
        """
        self.substitute('buildout', 'parts')

        keys = set(self.buildout._raw['buildout'].keys()) - self.previous_keys
        for key in keys:
            self.substitute('buildout', key)

    def determine_cwd(self):
        """
        This horror reverse engineers cwd by finding all buildouts loaded
        and working out a common prefix.

        This is needed because setting ``${buildout:directory}`` changes
        the cwd and buildout doesn't keep track of the original cwd.

        This should hopefully be a reasonable default, but it isn't absolute
        and can be overriden in buildouts.
        """
        def find_buildouts(buildout):
            default_buildout = os.path.expanduser('~/.buildout/default.cfg')
            for section in buildout.values():
                for key, value in section.items():
                    for v in value[1].split("[-]"):
                        s = v.strip()
                        if s and os.path.exists(s) and s != default_buildout:
                            yield os.path.dirname(s)

        self.buildout._raw['buildout']['cwd'] = os.path.commonprefix(set(find_buildouts(self.original)))
        self.substitute('buildout', 'cwd')

    def load_extensions(self):
        """
        Determine which extensions need installing

        We look at the ${buildout:extensions} variable as .apply() is called,
        rather than after the overrides from the invoking buildout have been applied
        """

        # Work out the list of extensions the stack requested
        current_extensions = set(split(self.before_apply['buildout'].get('extensions','')))
        extensions = current_extensions - self.previous_extensions

        self.log.info("Installing %d extensions requested by stack" % len(extensions))

        if not extensions:
            return

        path = [self.buildout['buildout']['develop-eggs-directory']]

        if self.buildout['buildout']['offline'] == 'true':
            dest = None
            path.append(self.buildout['buildout']['eggs-directory'])
        else:
            dest = self.buildout['buildout']['eggs-directory']
            if not os.path.exists(dest):
                self.log.info('Creating directory %r.' % dest)
                os.mkdir(dest)

        zc.buildout.easy_install.install(
            extensions, dest, path=path,
            working_set=pkg_resources.working_set,
            links = self.buildout['buildout'].get('find-links', '').split(),
            index = self.buildout['buildout'].get('index'),
            newest=self.buildout.newest, allow_hosts=self.buildout._allow_hosts,
        )

        # Clear cache because extensions might now let us read pages we
        # couldn't read before.
        zc.buildout.easy_install.clear_index_cache()

    def run_commands(self):
        if not self.name in self.buildout._raw:
            return

        if self.buildout._raw[self.name].get("dbg.annotate", None):
            _print_annotate(self.buildout._annotated)
            sys.exit(0)

        elif self.buildout._raw[self.name].get("dbg.dump", None):
            for name in sorted(self.buildout._raw.keys()):
                section = self.buildout._raw[name]
                print "[%s]" % name

                if "recipe" in section:
                    print "recipe", "=", section["recipe"]

                for key in section.keys():
                    if key != "recipe":
                        if "\n" in section[key]:
                            print key, "="
                            for line in section[key].split("\n"):
                                if line.strip():
                                    print "   %s" % line.strip()
                        else:
                            print key, "=", section[key]

                print ""

            sys.exit(0)

        elif self.buildout._raw[self.name].get("dbg.versions", None):
            print "[versions]"
            pkgs = sorted(self.buildout["versions"].keys())
            for pkg in pkgs:
                print pkg, "=", self.buildout["versions"][pkg]
            sys.exit(0)


