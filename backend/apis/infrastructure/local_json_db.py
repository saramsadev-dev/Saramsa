"""
Local JSON file-based mock for Azure Cosmos DB SDK.

Drop-in replacement: CosmosDBService talks to these classes instead of the
real CosmosClient / DatabaseProxy / ContainerProxy. Every write is persisted
to backend/local_db/<container>.json so data survives server restarts.

Temporary testing substitute -- not for production use.
"""

import json
import os
import re
import copy
import threading
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Storage directory (resolved relative to this file)
# ---------------------------------------------------------------------------
_LOCAL_DB_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "local_db",
)


# ---------------------------------------------------------------------------
# Exception that mimics azure.cosmos.exceptions.CosmosResourceNotFoundError
# ---------------------------------------------------------------------------
class _CosmosResourceNotFoundError(Exception):
    """Raised when a document is not found (mirrors the real SDK exception)."""

    status_code = 404

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message)
        self.message = message


# ---------------------------------------------------------------------------
# Cosmos SQL mini-parser
# ---------------------------------------------------------------------------

def _resolve_field(doc: dict, path: str) -> Any:
    """Resolve a dotted field path like 'c.metadata.is_personal' on *doc*."""
    parts = path.split(".")
    # Strip leading 'c' alias
    if parts and parts[0] == "c":
        parts = parts[1:]
    obj: Any = doc
    for p in parts:
        if isinstance(obj, dict):
            obj = obj.get(p)
        else:
            return None
    return obj


def _substitute_params(query: str, parameters: Optional[List[Dict[str, Any]]]) -> str:
    """Replace @param placeholders with JSON-encoded literals."""
    if not parameters:
        return query
    # Sort by length descending so @project_id is replaced before @project
    for param in sorted(parameters, key=lambda p: -len(p["name"])):
        name = param["name"]
        value = param["value"]
        # Encode value as JSON literal
        literal = json.dumps(value)
        query = query.replace(name, literal)
    return query


def _parse_value(token: str) -> Any:
    """Parse a literal token into a Python value."""
    token = token.strip()
    if token.lower() == "true":
        return True
    if token.lower() == "false":
        return False
    if token.lower() == "null":
        return None
    # Quoted string
    if (token.startswith("'") and token.endswith("'")) or (
        token.startswith('"') and token.endswith('"')
    ):
        return token[1:-1]
    # Number
    try:
        if "." in token:
            return float(token)
        return int(token)
    except ValueError:
        return token


# ---- Condition evaluation -------------------------------------------------

def _eval_condition(doc: dict, cond: str) -> bool:
    """Evaluate a single WHERE condition like 'c.type = "user"'."""
    cond = cond.strip()

    # IS NOT NULL
    m = re.match(r"([\w.]+)\s+IS\s+NOT\s+NULL", cond, re.IGNORECASE)
    if m:
        val = _resolve_field(doc, m.group(1))
        return val is not None

    # IS NULL
    m = re.match(r"([\w.]+)\s+IS\s+NULL", cond, re.IGNORECASE)
    if m:
        val = _resolve_field(doc, m.group(1))
        return val is None

    # != null  (Cosmos-specific shorthand)
    m = re.match(r"([\w.]+)\s*!=\s*null\b", cond, re.IGNORECASE)
    if m:
        val = _resolve_field(doc, m.group(1))
        return val is not None

    # field != value
    m = re.match(r"([\w.]+)\s*!=\s*(.+)", cond, re.IGNORECASE)
    if m:
        val = _resolve_field(doc, m.group(1))
        expected = _parse_value(m.group(2))
        return val != expected

    # field = value
    m = re.match(r"([\w.]+)\s*=\s*(.+)", cond, re.IGNORECASE)
    if m:
        val = _resolve_field(doc, m.group(1))
        expected = _parse_value(m.group(2))
        return val == expected

    # field > value
    m = re.match(r"([\w.]+)\s*>\s*(.+)", cond, re.IGNORECASE)
    if m:
        val = _resolve_field(doc, m.group(1))
        expected = _parse_value(m.group(2))
        try:
            return val > expected
        except TypeError:
            return False

    # field < value
    m = re.match(r"([\w.]+)\s*<\s*(.+)", cond, re.IGNORECASE)
    if m:
        val = _resolve_field(doc, m.group(1))
        expected = _parse_value(m.group(2))
        try:
            return val < expected
        except TypeError:
            return False

    # field >= value
    m = re.match(r"([\w.]+)\s*>=\s*(.+)", cond, re.IGNORECASE)
    if m:
        val = _resolve_field(doc, m.group(1))
        expected = _parse_value(m.group(2))
        try:
            return val >= expected
        except TypeError:
            return False

    # field <= value
    m = re.match(r"([\w.]+)\s*<=\s*(.+)", cond, re.IGNORECASE)
    if m:
        val = _resolve_field(doc, m.group(1))
        expected = _parse_value(m.group(2))
        try:
            return val <= expected
        except TypeError:
            return False

    # Fallback -- unknown condition, pass everything
    logger.warning(f"LocalJsonDB: unrecognised condition ignored: {cond}")
    return True


def _eval_exists(doc: dict, exists_clause: str) -> bool:
    """
    Handle EXISTS(SELECT VALUE x FROM x IN c.array WHERE ...) patterns.
    """
    m = re.search(
        r"SELECT\s+VALUE\s+\w+\s+FROM\s+(\w+)\s+IN\s+([\w.]+)\s+WHERE\s+(.+)",
        exists_clause,
        re.IGNORECASE,
    )
    if not m:
        return True  # can't parse, be permissive

    alias = m.group(1)
    array_path = m.group(2)
    inner_conds_str = m.group(3).strip().rstrip(")")

    arr = _resolve_field(doc, array_path)
    if not isinstance(arr, list):
        return False

    # Parse inner conditions (AND-joined)
    inner_parts = re.split(r"\s+AND\s+", inner_conds_str, flags=re.IGNORECASE)
    for element in arr:
        all_match = True
        for part in inner_parts:
            # Replace alias with 'c' so _eval_condition can resolve against element
            part_adjusted = part.replace(f"{alias}.", "c.")
            if not _eval_condition(element, part_adjusted):
                all_match = False
                break
        if all_match:
            return True
    return False


def _split_top_level_or(conditions_str: str) -> List[str]:
    """Split a conditions string by top-level OR, respecting parentheses."""
    parts = []
    depth = 0
    current = []
    tokens = re.split(r"(\bOR\b|\(|\))", conditions_str, flags=re.IGNORECASE)
    for tok in tokens:
        if tok == "(":
            depth += 1
            current.append(tok)
        elif tok == ")":
            depth -= 1
            current.append(tok)
        elif tok.strip().upper() == "OR" and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(tok)
    remainder = "".join(current).strip()
    if remainder:
        parts.append(remainder)
    return parts


def _matches_where(doc: dict, where_clause: str) -> bool:
    """Evaluate a full WHERE clause (with AND / OR / EXISTS / parens)."""
    clause = where_clause.strip()
    if not clause:
        return True

    # Handle EXISTS
    exists_match = re.search(r"EXISTS\s*\((.+?)\)", clause, re.IGNORECASE | re.DOTALL)
    exists_result = True
    if exists_match:
        exists_result = _eval_exists(doc, exists_match.group(1))
        # Remove the EXISTS(...) from the clause for remaining processing
        clause = clause[: exists_match.start()] + clause[exists_match.end() :]
        # Clean up leftover AND
        clause = re.sub(r"^\s*AND\s+", "", clause, flags=re.IGNORECASE)
        clause = re.sub(r"\s+AND\s*$", "", clause, flags=re.IGNORECASE)
        clause = clause.strip()

    if not exists_result:
        return False
    if not clause:
        return True

    # Split by top-level OR first
    or_branches = _split_top_level_or(clause)
    if len(or_branches) > 1:
        return any(_matches_where(doc, branch) for branch in or_branches)

    # Single branch -- split by AND
    # Remove outer parens if fully wrapped
    stripped = clause.strip()
    if stripped.startswith("(") and stripped.endswith(")"):
        inner = stripped[1:-1]
        # Make sure the parens actually wrap the whole thing
        depth = 0
        valid = True
        for ch in inner:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            if depth < 0:
                valid = False
                break
        if valid and depth == 0:
            stripped = inner

    and_parts = re.split(r"\s+AND\s+", stripped, flags=re.IGNORECASE)

    for part in and_parts:
        part = part.strip()
        if not part:
            continue

        # Nested OR in parentheses: (a OR b)
        if part.startswith("(") and part.endswith(")"):
            inner = part[1:-1]
            or_subs = _split_top_level_or(inner)
            if len(or_subs) > 1:
                if not any(_matches_where(doc, sub) for sub in or_subs):
                    return False
                continue

        if not _eval_condition(doc, part):
            return False

    return True


def _parse_query(query: str, parameters: Optional[List[Dict[str, Any]]]) -> dict:
    """
    Parse a Cosmos SQL query into a dict with keys:
      select_fields, select_value_max, top, where, order_by, offset, limit
    """
    q = _substitute_params(query, parameters)
    result: Dict[str, Any] = {
        "select_fields": "*",
        "select_value_max": None,
        "select_top_field": None,
        "top": None,
        "where": "",
        "order_by": [],
        "offset": None,
        "limit": None,
    }

    # SELECT VALUE MAX(c.field)
    m = re.match(
        r"SELECT\s+VALUE\s+MAX\(([\w.]+)\)\s+FROM\s+\w+",
        q,
        re.IGNORECASE,
    )
    if m:
        result["select_value_max"] = m.group(1)

    # SELECT TOP N  (can be 'SELECT TOP 1 *' or 'SELECT TOP 1 c.field')
    m = re.match(r"SELECT\s+TOP\s+(\d+)\s+(.+?)\s+FROM", q, re.IGNORECASE)
    if m:
        result["top"] = int(m.group(1))
        fields = m.group(2).strip()
        if fields != "*":
            result["select_top_field"] = fields

    # WHERE clause -- everything between WHERE and ORDER BY / OFFSET / LIMIT / end
    m = re.search(
        r"WHERE\s+(.+?)(?:\s+ORDER\s+BY|\s+OFFSET|\s+LIMIT|$)",
        q,
        re.IGNORECASE | re.DOTALL,
    )
    if m:
        result["where"] = m.group(1).strip()

    # ORDER BY
    m = re.search(r"ORDER\s+BY\s+(.+?)(?:\s+OFFSET|\s+LIMIT|$)", q, re.IGNORECASE)
    if m:
        parts = [p.strip() for p in m.group(1).split(",")]
        order_list = []
        for part in parts:
            tokens = part.split()
            field = tokens[0]
            direction = "ASC"
            if len(tokens) > 1 and tokens[1].upper() == "DESC":
                direction = "DESC"
            order_list.append((field, direction))
        result["order_by"] = order_list

    # OFFSET x LIMIT y
    m = re.search(r"OFFSET\s+(\d+)\s+LIMIT\s+(\d+)", q, re.IGNORECASE)
    if m:
        result["offset"] = int(m.group(1))
        result["limit"] = int(m.group(2))

    return result


def _execute_query(
    docs: List[dict],
    query: str,
    parameters: Optional[List[Dict[str, Any]]] = None,
) -> List[Any]:
    """Run a parsed Cosmos SQL query against an in-memory list of documents."""
    parsed = _parse_query(query, parameters)

    # Filter
    filtered = [d for d in docs if _matches_where(d, parsed["where"])]

    # ORDER BY
    for field, direction in reversed(parsed["order_by"]):
        reverse = direction == "DESC"
        filtered.sort(
            key=lambda d: (_resolve_field(d, field) or ""),
            reverse=reverse,
        )

    # TOP
    if parsed["top"] is not None:
        filtered = filtered[: parsed["top"]]

    # OFFSET / LIMIT
    if parsed["offset"] is not None:
        filtered = filtered[parsed["offset"] :]
    if parsed["limit"] is not None:
        filtered = filtered[: parsed["limit"]]

    # SELECT VALUE MAX
    if parsed["select_value_max"] is not None:
        field = parsed["select_value_max"]
        values = [_resolve_field(d, field) for d in filtered if _resolve_field(d, field) is not None]
        if values:
            return [max(values)]
        return [None]

    # SELECT specific field (e.g. SELECT TOP 1 c.version)
    if parsed["select_top_field"] is not None and parsed["select_top_field"] != "*":
        field = parsed["select_top_field"].strip()
        results = []
        for d in filtered:
            val = _resolve_field(d, field)
            if val is not None:
                # Return as dict with field name stripped of 'c.'
                fname = field.split(".")[-1] if "." in field else field
                results.append({fname: val})
            else:
                results.append({})
        return results

    return [copy.deepcopy(d) for d in filtered]


# ---------------------------------------------------------------------------
# LocalJsonContainer -- mimics azure.cosmos ContainerProxy
# ---------------------------------------------------------------------------

class LocalJsonContainer:
    """Thread-safe, JSON-file-backed container that implements the Cosmos SDK
    container interface used by CosmosDBService."""

    def __init__(self, name: str, db_dir: str = _LOCAL_DB_DIR):
        self._name = name
        self._lock = threading.Lock()
        self._db_dir = db_dir
        os.makedirs(self._db_dir, exist_ok=True)
        self._file = os.path.join(self._db_dir, f"{name}.json")
        self._docs: List[dict] = self._load()

    # ---- persistence -------------------------------------------------------

    def _load(self) -> List[dict]:
        if os.path.exists(self._file):
            try:
                with open(self._file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
            except (json.JSONDecodeError, OSError):
                return []
        return []

    def _reload_if_changed(self) -> None:
        """Reload from disk if the file was modified by another process
        (e.g. Celery worker writing while Django reads)."""
        try:
            if os.path.exists(self._file):
                mtime = os.path.getmtime(self._file)
                if not hasattr(self, "_last_mtime") or mtime != self._last_mtime:
                    self._docs = self._load()
                    self._last_mtime = mtime
        except OSError:
            pass

    def _save(self) -> None:
        tmp = self._file + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._docs, f, indent=2, default=str)
        # Atomic-ish rename
        if os.path.exists(self._file):
            os.replace(tmp, self._file)
        else:
            os.rename(tmp, self._file)
        # Track mtime so _reload_if_changed skips our own writes
        try:
            self._last_mtime = os.path.getmtime(self._file)
        except OSError:
            pass

    # ---- SDK interface -----------------------------------------------------

    def create_item(self, body: dict, **kwargs) -> dict:
        with self._lock:
            self._reload_if_changed()
            doc_id = body.get("id")
            if doc_id is not None:
                for d in self._docs:
                    if d.get("id") == doc_id:
                        raise Exception(
                            f"Document with id '{doc_id}' already exists in '{self._name}'"
                        )
            doc = copy.deepcopy(body)
            self._docs.append(doc)
            self._save()
            return copy.deepcopy(doc)

    def read_item(self, item: str, partition_key: Any, **kwargs) -> dict:
        with self._lock:
            self._reload_if_changed()
            for d in self._docs:
                if d.get("id") == item:
                    return copy.deepcopy(d)
        raise _CosmosResourceNotFoundError(
            f"Document '{item}' not found in '{self._name}'"
        )

    def upsert_item(self, body: dict, **kwargs) -> dict:
        with self._lock:
            self._reload_if_changed()
            doc_id = body.get("id")
            doc = copy.deepcopy(body)
            if doc_id is not None:
                for i, d in enumerate(self._docs):
                    if d.get("id") == doc_id:
                        self._docs[i] = doc
                        self._save()
                        return copy.deepcopy(doc)
            self._docs.append(doc)
            self._save()
            return copy.deepcopy(doc)

    def replace_item(self, item: str, body: dict, **kwargs) -> dict:
        with self._lock:
            self._reload_if_changed()
            for i, d in enumerate(self._docs):
                if d.get("id") == item:
                    doc = copy.deepcopy(body)
                    self._docs[i] = doc
                    self._save()
                    return copy.deepcopy(doc)
        raise _CosmosResourceNotFoundError(
            f"Document '{item}' not found in '{self._name}'"
        )

    def delete_item(self, item: str, partition_key: Any, **kwargs) -> None:
        with self._lock:
            self._reload_if_changed()
            for i, d in enumerate(self._docs):
                if d.get("id") == item:
                    self._docs.pop(i)
                    self._save()
                    return
        raise _CosmosResourceNotFoundError(
            f"Document '{item}' not found in '{self._name}'"
        )

    def patch_item(
        self, item: str, partition_key: Any, patch_operations: list, **kwargs
    ) -> dict:
        with self._lock:
            self._reload_if_changed()
            for i, d in enumerate(self._docs):
                if d.get("id") == item:
                    doc = self._docs[i]
                    for op in patch_operations:
                        op_type = op.get("op", "").lower()
                        path = op.get("path", "").lstrip("/")
                        value = op.get("value")
                        parts = path.split("/")
                        target = doc
                        for p in parts[:-1]:
                            target = target.setdefault(p, {})
                        key = parts[-1]
                        if op_type in ("set", "replace", "add"):
                            target[key] = value
                        elif op_type == "remove":
                            target.pop(key, None)
                        elif op_type == "incr":
                            target[key] = target.get(key, 0) + value
                    self._save()
                    return copy.deepcopy(doc)
        raise _CosmosResourceNotFoundError(
            f"Document '{item}' not found in '{self._name}'"
        )

    def query_items(
        self,
        query: str,
        parameters: Optional[List[Dict[str, Any]]] = None,
        enable_cross_partition_query: bool = False,
        **kwargs,
    ) -> List[dict]:
        with self._lock:
            self._reload_if_changed()
            return _execute_query(self._docs, query, parameters)

    def read(self, **kwargs) -> dict:
        """Return minimal container properties (used by get_container_stats)."""
        self._reload_if_changed()
        return {
            "id": self._name,
            "partitionKey": {"paths": ["/id"]},
        }


# ---------------------------------------------------------------------------
# LocalJsonDatabase -- mimics azure.cosmos DatabaseProxy
# ---------------------------------------------------------------------------

class LocalJsonDatabase:
    """Mimics the Cosmos DatabaseProxy."""

    def __init__(self, db_name: str, db_dir: str = _LOCAL_DB_DIR):
        self._name = db_name
        self._db_dir = db_dir
        self._containers: Dict[str, LocalJsonContainer] = {}
        self._lock = threading.Lock()

    @property
    def id(self) -> str:  # noqa: A003 -- matches SDK attribute name
        return self._name

    def create_container_if_not_exists(
        self, id: str, partition_key: Any = None, **kwargs  # noqa: A002
    ) -> LocalJsonContainer:
        with self._lock:
            if id not in self._containers:
                self._containers[id] = LocalJsonContainer(id, self._db_dir)
            return self._containers[id]

    def get_container_client(self, container: str, **kwargs) -> LocalJsonContainer:
        with self._lock:
            if container not in self._containers:
                self._containers[container] = LocalJsonContainer(
                    container, self._db_dir
                )
            return self._containers[container]


# ---------------------------------------------------------------------------
# LocalJsonClient -- mimics azure.cosmos CosmosClient
# ---------------------------------------------------------------------------

class LocalJsonClient:
    """Mimics the top-level CosmosClient."""

    def __init__(self, db_dir: str = _LOCAL_DB_DIR):
        self._db_dir = db_dir
        self._databases: Dict[str, LocalJsonDatabase] = {}
        self._lock = threading.Lock()

    def create_database_if_not_exists(
        self, id: str, **kwargs  # noqa: A002
    ) -> LocalJsonDatabase:
        with self._lock:
            if id not in self._databases:
                self._databases[id] = LocalJsonDatabase(id, self._db_dir)
            return self._databases[id]

    def get_database_client(self, database: str, **kwargs) -> LocalJsonDatabase:
        with self._lock:
            if database not in self._databases:
                self._databases[database] = LocalJsonDatabase(database, self._db_dir)
            return self._databases[database]
