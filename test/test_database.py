import six

from six.moves import xrange

import pytest

from coucher import client, excepts
from .utils import get_auth_and_host


auth, host = get_auth_and_host()
test_db_name = "coucher_tests_temporal_db"

@pytest.fixture(scope="function")
def database(request):
    """
    Creates a database for testing
    """

    server = client.Server(host=host, auth=auth)
    database = server.create_db(test_db_name)

    def finalizer():
        try:
            server.delete_db(database)
        except:
            pass
    request.addfinalizer(finalizer)
    return database

def test_add_doc(database):
    """
    Try to create a new doc
    """

    # test with id
    doc = database.save({"_id": "testid", "a": "test"})
    assert doc.id == "testid"

    # test without id
    doc = database.save({"a": "test"})
    assert doc.id and doc.rev

def test_get_doc(database):
    """
    Try to get doc
    """

    doc = database.save({"a": "test"})
    new_doc1 = database[doc.id]

    # test caching
    new_doc2 = database[doc.id]
    assert doc == new_doc1 == new_doc2

    # test geting not existing doc
    with pytest.raises(excepts.DocNotExists):
        database["NOTEXISTINGID"]

    default_doc = {"a": "default doc"}
    doc = database.get_doc("NOTEXISTINGID", default=default_doc)
    assert doc == default_doc

def test_doc_conflict(database):
    """
    Test document conflicts
    """

    doc = {"_id": "testid", "a": "test"}
    database.save(doc)
    with pytest.raises(excepts.DocConflict):
        database.save(doc)

def test_del_doc(database):
    """
    Test if can delete documents and if they raise erroes when don't exists
    """

    ddoc = {"_id": "testid", "a": "test"}
    doc = database.save(ddoc)
    del database[doc]

    with pytest.raises(excepts.DocNotExists):
        del database[doc]

    doc = database.save(ddoc)
    del database[doc.id]

def test_view_all_docs(database):
    # sorted by id
    docs = [{"_id": "id_%02d" % i, "test": "doc %s" % i} for i in xrange(42)]
    database.update(docs)
    view = database.view("_all_docs", include_docs=True)
    assert view.total_rows == 42

    iter_view = iter(view)
    for i in xrange(view.total_rows):
        assert next(iter_view)["doc"]["test"] == "doc %s" % i

    keys = [doc["_id"] for doc in docs[:10]]
    view = database.view("_all_docs", include_docs=True, keys=keys)
    docs = []
    for row in view:
        docs.append(row["doc"]["_id"])
    assert docs == keys

def test_changes(database):
    docs = [{"_id": "id_%02d" % i, "test": "doc %s" % i} for i in xrange(42)]
    database.update(docs)

    new_docs = []
    for row in database.changes(include_docs=True, yield_beats=True,
                                heartbeat=4, timeout=4):
        if not row:
            break
        doc = row["doc"]
        del doc["_rev"]
        new_docs.append(doc)
    assert docs == new_docs

def test_db_info(database):
    assert database.info()["db_name"] == test_db_name

def test_db_repr(database):
    assert repr(database) == "<Database %s>" % test_db_name
