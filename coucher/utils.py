import re
import json

from ijson.common import ObjectBuilder

# took from couchdb-python
def encode_view_options(options):
    """
    Encode any items in the options dict that are sent as a JSON string to a
    view/list function.
    """
    retval = {}
    for name, value in options.items():
        def is_string():
            try:
                return isinstance(value, basestring)
            except NameError:
                return isinstance(value, str)

        if name in ('key', 'startkey', 'endkey') \
                or not is_string():
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

# ijson.common.items with support of more than one prefix
def ijson_items(prefixed_events, prefixes):
    '''
    An iterator returning native Python objects constructed from the events
    under a given prefix.
    '''

    prefixed_events = iter(prefixed_events)
    try:
        while True:
            current, event, value = next(prefixed_events)
            if current in prefixes:
                current_prefix = current
                if event in ('start_map', 'start_array'):
                    builder = ObjectBuilder()
                    end_event = event.replace('start', 'end')
                    while (current, event) != (current_prefix, end_event):
                        builder.event(event, value)
                        current, event, value = next(prefixed_events)
                    yield current_prefix, builder.value
                else:
                    yield current_prefix, value
    except StopIteration:
        pass
