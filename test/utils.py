import os
import re

def get_auth_and_host():
    """
    Get auth and host from env or use defaults
    """
    uri = os.environ.get("COUCHER_URI") or "http://localhost:5984"

    uri_re = re.compile("(?P<proto>https?://)((?P<user>[a-zA-Z]*?)"\
            "(:(?P<pass>.*?))?@)?(?P<host>.*)")

    groups = uri_re.match(uri).groupdict(default=None)
    auth = []
    user = groups.get("user")
    passwd = groups.get("pass")

    user and auth.append(user)
    passwd and auth.append(passwd)

    host = "{proto}{host}".format(**groups)
    return (auth, host)
