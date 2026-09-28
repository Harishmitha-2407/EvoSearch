from app.services.code_analysis_service import parse_code, detect_language, CodeParsingError

SAMPLE_V1 = '''
import hashlib

def login(username, password):
    """Authenticate a user."""
    if password == stored_password(username):
        return True
    return False


class UserController:
    def register(self, username, password):
        pass
'''

SAMPLE_V2 = '''
import bcrypt

def login(username, password):
    """Authenticate a user using bcrypt."""
    return bcrypt.checkpw(password.encode(), stored_hash(username))

def refresh_token(token):
    return new_token(token)

def logout(session_id):
    pass


class UserController:
    def register(self, username, password):
        pass
'''


def test_detect_language():
    assert detect_language("auth.py") == "python"
    assert detect_language("app.js") == "javascript"
    assert detect_language("styles.css") == "css"


def test_parse_python_extracts_functions_and_classes():
    entities = parse_code("auth.py", SAMPLE_V1)
    names = {(e.entity_type, e.name) for e in entities}
    assert ("function", "login") in names
    assert ("class", "UserController") in names
    assert ("method", "register") in names
    assert ("import", "hashlib") in names


def test_parse_python_invalid_syntax_raises():
    try:
        parse_code("broken.py", "def foo(:\n    pass")
        assert False, "expected CodeParsingError"
    except CodeParsingError:
        pass
