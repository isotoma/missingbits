
from zc.buildout import UserError
from zc.buildout.buildout import Options

def get_bool(self, name):
    value = self[name].strip().lower()
    if value not in ('true', 'on', 'yes', '1', 'false', 'off', 'no', '0'):
        raise zc.buildout.UserError(
            'Invalid value for %s option: %s' % (name, value))
    else:
        return value in ('true', 'on', 'yes', '1')

Options.get_bool = get_bool


def get_list(self, name):
    value = self[name].strip().splitlines()
    retval = []
    for line in value:
        line = line.strip()
        if not line:
            continue
        retval.append(line)
    return retval

Options.get_list = get_list

