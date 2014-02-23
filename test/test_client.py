import six

import pytest

from coucher import client, excepts
from .utils import get_auth_and_host

auth, host = get_auth_and_host()

test_db_name = "coucher_tests_temporal_db"

@pytest.fixture(scope="module")
def server():
    """
    Creates a server and remove the testing db if exists
    """

    server = client.Server(host=host, auth=auth)
    try:
        server.delete_db(test_db_name)
    except excepts.DBNotExists:
        pass
    return server

def test_connect(server):
    """
    Test if can connect to the server
    """
    assert server

def test_create(server):
    """
    Creates a database
    """

    db = server.create_db(test_db_name)
    server.delete_db(db)

def test_missing(server):
    """
    Test if raise DBNotExists trying to access a non existing database
    """

    assert "non_existing_database" not in server
    with pytest.raises(excepts.DBNotExists):
        server["non_existing_database"]

def test_exists(server):
    """
    Test if the db exist in the server
    """

    db = server.create_db(test_db_name)
    assert test_db_name in server
    assert db in server
    assert server[test_db_name]
    server.delete_db(db)
    assert test_db_name not in server

def test_create_delete_db(server):
    """
    Test if raise error when delete a database that exists
    and if don't raise and error when delete a database that don't exists
    """

    db = server.create_db(test_db_name)

    with pytest.raises(excepts.DBExists):
        db = server.create_db(test_db_name)

    server.delete_db(db)

    with pytest.raises(excepts.DBNotExists):
        server.delete_db(db)

    db = server.create_db(test_db_name)
    db.delete()

    with pytest.raises(excepts.DBNotExists):
        db.delete()

def test_len_server(server):
    """
    Test number of databases in server
    """

    start_len = len(server)

    dba = server.create_db(test_db_name + "a")
    dbb = server.create_db(test_db_name + "b")
    assert len(server) == start_len + 2
    server.delete_db(dba)
    server.delete_db(dbb)

def test_uuids(server):
    """
    Test server generated uuids
    """

    assert len(server.uuids()) == 1
    assert len(server.uuids(10)) == 10
    assert isinstance(server.uuids()[0], six.string_types)

def test_version(server):
    """
    Test server generated uuids
    """

    assert isinstance(server.version(), six.string_types)

def test_server_iterate(server):
    db = server.create_db(test_db_name)

    databases = []
    for database in server:
        databases.append(database.name)
    assert test_db_name in databases

    server.delete_db(db)
    databases = []
    for database in server:
        databases.append(database.name)
    assert test_db_name not in databases
