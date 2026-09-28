"""
Language-aware code parsing.

Python: full `ast`-based extraction (functions, methods, classes, imports,
docstrings, exact line ranges, source segments).

JavaScript/TypeScript/Java/C/C++: best-effort regex-based extraction of
function/class/import declarations. This is intentionally documented as a
*fallback*, not a full parser (the spec's "prefer Tree-sitter" ideal is a
heavy native-binding dependency out of scope for this build pass) - it
still gives useful diffable structure, but is less precise than the Python
path, especially for complex/nested/minified code.

SQL: extracts CREATE TABLE/VIEW/FUNCTION/PROCEDURE statements.
HTML/CSS/JSON/YAML: parsing failures for these fall back to plain text
(the file is still stored, embedded, and diffable - just without
structured entities).

If parsing fails entirely for a file, we NEVER abort the whole upload
pipeline - we catch the error, mark the file with a warning, and continue.
"""
import ast
import re
from dataclasses import dataclass, field
from typing import Optional


LANGUAGE_BY_EXT = {
    "py": "python", "js": "javascript", "jsx": "javascript",
    "ts": "typescript", "tsx": "typescript", "java": "java",
    "c": "c", "h": "c", "cpp": "cpp", "cc": "cpp", "hpp": "cpp",
    "sql": "sql", "html": "html", "htm": "html", "css": "css",
    "json": "json", "yaml": "yaml", "yml": "yaml",
}


@dataclass
class CodeEntityCandidate:
    entity_type: str  # function/method/class/import/route/table
    name: str
    parent: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    signature: Optional[str] = None
    docstring: Optional[str] = None
    source_snippet: Optional[str] = None


class CodeParsingError(Exception):
    pass


def detect_language(filename: str) -> str:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    return LANGUAGE_BY_EXT.get(ext, "unknown")


def parse_code(filename: str, source: str) -> list[CodeEntityCandidate]:
    language = detect_language(filename)
    try:
        if language == "python":
            return _parse_python(source)
        elif language in ("javascript", "typescript", "java", "c", "cpp"):
            return _parse_regex_generic(source)
        elif language == "sql":
            return _parse_sql(source)
        else:
            return []  # html/css/json/yaml: stored + embedded, no structured entities
    except Exception as e:
        raise CodeParsingError(f"Failed to parse {language} source: {e}")


def _segment(source: str, node) -> Optional[str]:
    try:
        return ast.get_source_segment(source, node)
    except Exception:
        return None


def _parse_python(source: str) -> list[CodeEntityCandidate]:
    tree = ast.parse(source)
    entities: list[CodeEntityCandidate] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [n.name for n in node.names]
            module = getattr(node, "module", None)
            label = f"{module}.{','.join(names)}" if module else ",".join(names)
            entities.append(CodeEntityCandidate(
                entity_type="import", name=label,
                start_line=node.lineno, end_line=node.lineno,
            ))

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            entities.append(CodeEntityCandidate(
                entity_type="class", name=node.name,
                start_line=node.lineno, end_line=getattr(node, "end_lineno", node.lineno),
                docstring=ast.get_docstring(node),
                source_snippet=_segment(source, node),
            ))
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    entities.append(CodeEntityCandidate(
                        entity_type="method", name=sub.name, parent=node.name,
                        start_line=sub.lineno, end_line=getattr(sub, "end_lineno", sub.lineno),
                        signature=_function_signature(sub),
                        docstring=ast.get_docstring(sub),
                        source_snippet=_segment(source, sub),
                    ))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            entities.append(CodeEntityCandidate(
                entity_type="function", name=node.name,
                start_line=node.lineno, end_line=getattr(node, "end_lineno", node.lineno),
                signature=_function_signature(node),
                docstring=ast.get_docstring(node),
                source_snippet=_segment(source, node),
            ))

    # Best-effort FastAPI/Flask route detection via decorators
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                route = _decorator_route(dec)
                if route:
                    entities.append(CodeEntityCandidate(
                        entity_type="route", name=f"{route} {node.name}",
                        start_line=node.lineno, end_line=node.lineno,
                    ))
    return entities


def _function_signature(node) -> str:
    args = [a.arg for a in node.args.args]
    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    return f"{prefix} {node.name}({', '.join(args)})"


def _decorator_route(dec) -> Optional[str]:
    try:
        if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
            method = dec.func.attr  # get/post/put/delete
            if method in ("get", "post", "put", "delete", "patch"):
                path = None
                if dec.args and isinstance(dec.args[0], ast.Constant):
                    path = dec.args[0].value
                return f"{method.upper()} {path or ''}".strip()
    except Exception:
        pass
    return None


# ------------------------------------------------------- regex-based fallback

_FUNC_PATTERNS = [
    re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(", re.MULTILINE),
    re.compile(r"^\s*(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>", re.MULTILINE),
    re.compile(r"^\s*(?:public|private|protected|static|\s)*[\w<>\[\],\s]+\s+(\w+)\s*\([^;{]*\)\s*\{", re.MULTILINE),
]
_CLASS_PATTERN = re.compile(r"^\s*(?:export\s+)?class\s+(\w+)", re.MULTILINE)
_IMPORT_PATTERN = re.compile(
    r"^\s*(import\s+.+?;?$|#include\s*[<\"].+?[>\"]|const\s+\w+\s*=\s*require\(.+?\))",
    re.MULTILINE,
)


def _line_of(source: str, pos: int) -> int:
    return source.count("\n", 0, pos) + 1


def _parse_regex_generic(source: str) -> list[CodeEntityCandidate]:
    entities: list[CodeEntityCandidate] = []
    seen_names = set()

    for pattern in _FUNC_PATTERNS:
        for m in pattern.finditer(source):
            name = m.group(1)
            key = (name, m.start())
            if key in seen_names:
                continue
            seen_names.add(key)
            line = _line_of(source, m.start())
            entities.append(CodeEntityCandidate(
                entity_type="function", name=name,
                start_line=line, end_line=line,
                signature=m.group(0).strip()[:200],
            ))

    for m in _CLASS_PATTERN.finditer(source):
        line = _line_of(source, m.start())
        entities.append(CodeEntityCandidate(
            entity_type="class", name=m.group(1), start_line=line, end_line=line,
        ))

    for m in _IMPORT_PATTERN.finditer(source):
        line = _line_of(source, m.start())
        entities.append(CodeEntityCandidate(
            entity_type="import", name=m.group(1).strip()[:200],
            start_line=line, end_line=line,
        ))

    return entities


_SQL_OBJECT_PATTERN = re.compile(
    r"CREATE\s+(?:OR\s+REPLACE\s+)?(TABLE|VIEW|FUNCTION|PROCEDURE|INDEX)\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"\[]?(\w+)",
    re.IGNORECASE,
)


def _parse_sql(source: str) -> list[CodeEntityCandidate]:
    entities = []
    for m in _SQL_OBJECT_PATTERN.finditer(source):
        line = _line_of(source, m.start())
        entities.append(CodeEntityCandidate(
            entity_type=m.group(1).lower(), name=m.group(2),
            start_line=line, end_line=line,
        ))
    return entities
