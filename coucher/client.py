import ijson
import json

from requests import Session

from utils import validate_dbname, encode_view_options, path_from_name
from utils import ijson_items

import excepts

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
    def __init__(self, host="http://localhost:5984", auth=None):
        self.host = host
        self.session = Session()
        self.session.auth = auth
        self.session.headers = {"Content-Type": "application/json"}

    def __getitem__(self, name):
        return Database(name, server=self, create=False)

    def __delitem__(self, name):
        self.delete_db(name)

    def uuids(self, count=1):
        """
        Returns a a lists of "count" uuids generated in the server
        """

        request = self.session.get(self.host + "/_uuids",
                params={"count": count})
        return request.json()["uuids"]
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
            raise Exception, request.status_code

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
            self.iterator = ijson_items(ijson.parse(response.raw),
                    ['total_rows', 'offset', 'rows.item'])

            try:
                for t in ("total_rows", "offset"):
                    _type, item = next(self.iterator)
                    if _type == t:
                        setattr(self, t, item)
                    else:
                        self._prefetched_items.append(item)
            except StopIteration:
                pass
        else:
            raise Exception, response.status_code

    def __iter__(self):
        while self._prefetched_items:
            yield self._prefetched_items.pop(0)
        for _type, item in self.iterator:
            # this should never happend
            if _type != "rows.item":
                print "Invalid Row Type", _type
                continue
            yield item

class Database(object):
    def __init__(self, name, server=None, create=False):
        validate_dbname(name)
        self.server = server or Server()
        self.session = server.session
        self.name = name
        self.database = server.host + "/" + name
        if create:
            self.create()
        else:
            response = self.session.head(self.database)
            if not response.ok:
                if response.status_code == 404:
                    raise excepts.DBNotExists
                raise Exception, response.status_code

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
            raise Exception, request.status_code

        response = request.json()
        ok = response.get("ok", False)
        if not ok:
            raise Exception, response


    def delete_doc(self, doc):
        """
        Removes a document
        """

        if isinstance(doc, basestring):
            doc = self[doc]

        response = self.session.delete(self.database + "/" + doc["_id"],
                params=dict(rev=doc["_rev"]))
        if response.ok:
            return response.json()

    def changes(self, feed="continuous", include_docs=False, yield_beats=False,
            **opts):
        opts.update(dict(feed=feed, include_docs=include_docs))
        opts = encode_view_options(opts)

        if feed == "continuous":
            response = self.session.get(self.database + "/_changes",
                    params=opts, stream=True)
            if not response.ok:
                raise Exception, response.status_code

            for line in response.iter_lines(chunk_size=1):
                if line:
                    yield json.loads(line)
                elif yield_beats:
                    yield {}
        else:
            raise NotImplementedError, "feed '%s' is not implemented" % feed

    def delete(self):
        """
        Delete the database
        """

        self.server.delete_db(self.name)

    def save(self, doc, **options):
        """
        Creates or Updates a document
        """

        response = self.session.post(self.database,
                data=json.dumps(doc), params=options)
        if response.ok:
            return response.json()

        if response.status_code == 409:
            raise excepts.DocConflict, "_id: %s" % doc["_id"]

        raise Exception, "Can't save doc '%s' error '%s'" % (doc,
                response.status_code)

    def update(self, docs, **options):
        options.update(docs=docs)
        response = self.session.post(self.database + "/_bulk_docs",
                data=json.dumps(options))

        if response.ok:
            return response.json()
        raise Exception, "Error updating docs %s" % response.status_code

    def view(self, name, **options):
        return View(name, self, **options)

    def get_doc(self, docid, default=None):
        """
        Returns the a document
        """

        response = self.session.get(self.database + "/" + docid)
        if not response.ok:
            if response.status_code == 404:
                if default:
                    return default
                raise excepts.DocNotExists
            raise Exception, response.status_code

        return Document(response.json())

    def __repr__(self):
        return "<Database %s>" % self.name
