import copy
try:
    import simplejson as json
except ImportError:
    import json
    print("Using stdlib json, expect poor performance")
    print("For speedup install simplejson")
import six

from requests import Session
from repoze.lru import LRUCache

from .utils import encode_view_options, path_from_name

from . import excepts


class Document(dict):
    @property
    def id(self):
        return self["_id"]

    @property
    def rev(self):
        return self["_rev"]

    def __repr__(self):
        return "<Document id=%s rev=%s>" % (self.id, self.rev)


class Server(object):
    def __init__(self, host="http://localhost:5984", auth=None,
                 trust_env=False):
        self.host = host
        self.session = Session()
        # trust env make use of get_netrc that is soooo slow
        self.session.trust_env = trust_env
        self.session.auth = auth
        self.session.headers = {"Content-Type": "application/json"}

    def __getitem__(self, name):
        return Database(name, server=self, create=False)

    def __len__(self):
        return len(self.get_databases())

    def __nonzero__(self):
        """
        Returns if server is available
        """

        try:
            self.session.head(self.host)
            return True
        except:
            return False

    def __delitem__(self, name):
        self.delete_db(name)

    def __contains__(self, db_or_name):
        """
        Tests if the database exists
        """

        name = db_or_name
        if isinstance(db_or_name, Database):
            name = db_or_name.name

        request = self.session.head(self.host + "/" + name)
        if request.status_code == 404:
            return False
        return True

    def __iter__(self):
        """
        Iterates over all the databases and returns Database instances
        """

        return (Database(name, server=self) for name in self.get_databases())

    def uuids(self, count=1):
        """
        Returns a a lists of "count" uuids generated in the server
        """

        request = self.session.get(self.host + "/_uuids",
                params={"count": count})
        return request.json()["uuids"]

    def get_databases(self):
        request = self.session.get(self.host + "/_all_dbs")
        return request.json()

    def version(self):
        request = self.session.get(self.host)
        return request.json()["version"]

    def create_db(self, name):
        """
        Try to create a new database or raise error

        Posible Errors: DBExists, AuthFail
        """

        return Database(name, server=self, create=True)

    def delete_db(self, db_or_name):
        """
        Try to delete database or raise error

        Posible Errors: DBNotExists, AuthFail
        """

        name = db_or_name
        if isinstance(db_or_name, Database):
            name = db_or_name.name

        request = self.session.delete(self.host + "/" + name)
        if not request.ok:
            if request.status_code == 401:
                raise excepts.AuthFail
            elif request.status_code == 404:
                raise excepts.DBNotExists
            raise Exception(request.status_code)

class View(object):
    def __init__(self, name, db, **options):
        path = "/".join(path_from_name(name, "_view", db.name))
        view = db.server.host + "/" + path
        params = encode_view_options(options)

        self.total_rows = self.offset = None
        self._prefetched_items = []

        if "keys" in options:
            data = json.dumps({"keys": options.pop("keys")})
            response = db.session.post(view, stream=True,
                                            data=data, params=params)
        else:
            response = db.session.get(view, stream=True, params=params)

        if response.ok:
            self.iterator = response.iter_lines(chunk_size=2048)
        else:
            raise Exception(response.status_code)
        first_line = next(self.iterator)
        first_line += b"]}"
        header = json.loads(first_line)
        self.total_rows = header["total_rows"]
        self.offset = header["offset"]

    def __iter__(self):
        for item in self.iterator:
            if item == b"]}" or not item:
                continue
            if item.endswith(b","):
                item = item[:-1]
            yield json.loads(item)


class Database(object):
    def __init__(self, name, server=None, create=False):
        self.server = server or Server()
        self.session = server.session
        self.name = name
        self.database = server.host + "/" + name

        self.cache = LRUCache(100)

        if create:
            self.create()
        else:
            response = self.session.head(self.database)
            if not response.ok:
                if response.status_code == 404:
                    raise excepts.DBNotExists
                raise Exception(response.status_code)

    def __getitem__(self, docid):
        """
        Returns a document by _id
        """

        return self.get_doc(docid)

    def __delitem__(self, docid):
        self.delete_doc(docid)

    def create(self):
        """
        Try to create a new database or raise error

        Posible Errors: DBExists, AuthFail
        """

        request = self.session.put(self.database)
        if not request.ok:
            if request.status_code == 401:
                raise excepts.AuthFail
            elif request.status_code == 412:
                raise excepts.DBExists
            raise Exception(request.status_code)

        response = request.json()
        ok = response.get("ok", False)
        if not ok:
            raise Exception(response)


    def delete_doc(self, doc):
        """
        Removes a document
        """

        if isinstance(doc, six.string_types):
            doc = self[doc]

        response = self.session.delete(self.database + "/" + doc["_id"],
                params=dict(rev=doc["_rev"]))
        if response.ok:
            return response.json()

        if response.status_code == 404:
            raise excepts.DocNotExists

    def changes(self, feed="continuous", include_docs=False, yield_beats=False,
            **opts):
        opts.update(dict(feed=feed, include_docs=include_docs))
        opts = encode_view_options(opts)

        if feed == "continuous":
            response = self.session.get(self.database + "/_changes",
                    params=opts, stream=True)
            if not response.ok:
                raise Exception(response.status_code)

            for line in response.iter_lines(chunk_size=1):
                if line:
                    yield json.loads(line)
                elif yield_beats:
                    yield {}
        else:
            raise NotImplementedError("feed '%s' is not implemented" % feed)

    def delete(self):
        """
        Delete the database
        """

        self.server.delete_db(self.name)

    def save(self, doc, **options):
        """
        Creates or Updates a document
        """

        request = self.session.post(self.database,
                data=json.dumps(doc), params=options)
        if request.ok:
            response = request.json()
            doc = copy.copy(doc)
            doc["_id"] = response.get("id")
            doc["_rev"] = response.get("rev")
            if isinstance(doc, dict):
                doc = Document(doc)
            return doc

        if request.status_code == 409:
            raise excepts.DocConflict("_id: %s" % doc["_id"])

        raise Exception("Can't save doc '%s' error '%s'" % (doc,
                request.status_code))

    def update(self, docs, **options):
        options.update(docs=docs)
        response = self.session.post(self.database + "/_bulk_docs",
                data=json.dumps(options))

        if response.ok:
            return response.json()
        raise Exception("Error updating docs %s" % response.status_code)

    def view(self, name, **options):
        return View(name, self, **options)

    def get_doc(self, docid, default=None):
        """
        Returns the a document
        """

        old_doc = self.cache.get(docid, None)
        headers = None
        if old_doc:
            headers = {'If-None-Match': old_doc[0]}

        response = self.session.get(self.database + "/" + docid,
                                    headers=headers)
        if not response.ok:
            if response.status_code == 404:
                if default:
                    return default
                raise excepts.DocNotExists
            raise Exception(response.status_code)

        if old_doc and response.headers["etag"] == old_doc[0]:
            doc = old_doc[1]
        else:
            doc = Document(response.json())
            self.cache.put(docid, (response.headers["etag"], doc))
        return doc

    def __repr__(self):
        return "<Database %s>" % self.name
