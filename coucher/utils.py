import re

import six
JSON_NEED_DECODE = False
try:
    import simplejson as json
except ImportError:
    import json
    print("Using stdlib json, expect poor performance")
    print("For speedup install simplejson")
    if six.PY3:
        JSON_NEED_DECODE = True

# took from couchdb-python
def encode_view_options(options):
    """
    Encode any items in the options dict that are sent as a JSON string to a
    view/list function.
    """
    retval = {}
    for name, value in options.items():
        if name in ('key', 'startkey', 'endkey') \
                or not isinstance(value, six.string_types):
            value = json.dumps(value)
        retval[name] = value
    return retval

SPECIAL_DB_NAMES = set(['_users'])
VALID_DB_NAME = re.compile(r'^[a-z][a-z0-9_$()+-/]*$')
def validate_dbname(name):
    if name in SPECIAL_DB_NAMES:
        return name
    if not VALID_DB_NAME.match(name):
        raise ValueError('Invalid database name')
    return name

def path_from_name(name, type, db):
    """
    Expand a 'design/foo' style name to its full path as a list of
    segments.
    """

    if name.startswith("_local/"):
        name, design = name[7:].split("/", 1)
        return [name, 'local', db, "_design", design]

    if name.startswith('_'):
        return [db] + name.split('/')
    design, name = name.split('/', 1)
    return [db, '_design', design, type, name]
# /took from couchdb-python
