class AuthFail(Exception):
    """
    Authentication fails
    """

class DBExists(Exception):
    """
    Database exists
    """

class DBNotExists(Exception):
    """
    Database doesnt exists
    """

class DocNotExists(Exception):
    """
    Document doesnt exists
    """

class DocConflict(Exception):
    """
    Document conflict
    """
