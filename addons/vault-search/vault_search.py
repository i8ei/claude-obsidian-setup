#!/usr/bin/env python3
"""vault_search.py — SQLite full-text index for an Obsidian Vault, for AI agents.

The markdown notes are the source of truth; the SQLite DB is a disposable
derived layer, fully regenerated on each `build`. Query subcommands are the
AI-facing API:

  build                    rebuild the index
  map [--folder X] [--lifecycle X]
                           path <TAB> description for every note
  search <q> [--k N]       FTS5 search; hides superseded/archive/internal by default
                           (--all / --include-retired / --include-internal widen)
                           --scope memory|all also searches VAULT_SEARCH_MEMORY_DIR
  links <note>             outgoing wikilinks of a note
  backlinks <note>         notes linking to a note
  orphans                  notes with no incoming links
  check                    broken links, missing desc, [要確認], bad frontmatter, dup titles
  scan <folder>            read-only inventory of files to import

Configuration (flags override environment variables):

  --vault / VAULT_SEARCH_VAULT   Vault root (required, fallback: KURA_VAULT)
  --db / VAULT_SEARCH_DB         index path (default: per-user data dir, fallback: KURA_DB)
  --memory-dir / ..._MEMORY_DIR  optional extra notes searchable via --scope
  --exclude / ..._EXCLUDE        comma-separated top-level folders to skip
                                 (default: Templates)

Requires Python 3.9+ and SQLite 3.34+ (FTS5 trigram tokenizer).
"""

import argparse
import difflib
import hashlib
import os
import re
import sqlite3
import sys
import unicodedata
from datetime import date, datetime
from pathlib import Path

# Set by configure() before any command runs
VAULT: Path = Path()
DB: Path = Path()
MEMORY_DIR = None
INDEX_EXEMPT_DIRS = {"Templates"}
# memory notes are indexed for search only, under this path prefix. They stay
# out of the link graph and out of map/orphans/check, which describe Vault
# health; `search` keeps its Vault-only default.
MEMORY_PREFIX = "memory/"


def nfc(s: str) -> str:
    # macOS filenames are NFD while wikilink text in note bodies is NFC;
    # normalize everything to NFC or dakuten names never resolve
    return unicodedata.normalize("NFC", s)


def nfkc(s: str) -> str:
    # For full-text search indexing and querying: normalize fullwidth/halfwidth
    # forms (e.g. 'ＡＩ' -> 'AI', '１２３' -> '123') so queries match variations.
    return unicodedata.normalize("NFKC", s)


def default_db_path(vault: Path) -> Path:
    """Per-user data dir, keyed by the Vault path so several Vaults can coexist.

    Kept outside the Vault so sync tools (iCloud, Obsidian Sync, git) never
    copy a derived binary file.
    """
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    key = hashlib.sha256(str(vault.resolve()).encode("utf-8")).hexdigest()[:8]
    return base / "vault-search" / f"{nfc(vault.name)}-{key}.db"


# Embeds/links to non-note assets are not graph edges
ASSET_EXT = {
    ".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif", ".pdf",
    ".mp3", ".mp4", ".mov", ".wav", ".m4a",
    ".canvas", ".base", ".xlsx", ".csv", ".json", ".geojson", ".docx", ".zip",
    ".html", ".htm",
}
# target = up to first '#' (heading) or '|' (alias); '\|' in tables leaves a trailing '\'
WIKILINK = re.compile(r"\[\[([^\]|#]+?)(?:[#|][^\]]*)?\]\]")
FENCED_CODE = re.compile(r"```.*?```|~~~.*?~~~", re.DOTALL)
INLINE_CODE = re.compile(r"`[^`\n]*`")

# Hub and instruction notes are expected to have no incoming links
ORPHAN_EXEMPT = re.compile(r"(^CLAUDE$|^HOME$|^AGENTS$|^README|^00_INDEX|MOC$)")
# Agent instruction files are not knowledge notes
INDEX_EXEMPT_PATHS = {"AGENTS.md", "CLAUDE.md"}
# Retired/archive prefixes hidden from search by default until --include-retired
DEFAULT_LIFECYCLE_BY_PREFIX = (
    (MEMORY_PREFIX + "archive/", "archive"),
    ("inbox/archive/", "archive"),
)

# Controlled frontmatter vocabularies (check() flags anything outside these)
VALID_LIFECYCLE = {"active", "reference", "raw", "superseded", "archive"}
VALID_VISIBILITY = {"public", "internal"}
VALID_ORPHAN_STATUS = {"intentional"}
SEARCH_QUOTES = str.maketrans({'"': " ", "\u201c": " ", "\u201d": " "})
UNVERIFIED_PATTERN = re.compile(r"[\[［]要確認[\]］]")


def parse_scalar_property(text: str, name: str):
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    for line in text[3:end].splitlines():
        m = re.match(rf"{re.escape(name)}:\s*(.*)", line.strip())
        if m:
            return m.group(1).strip().strip("\"'") or None
    return None


def parse_property_values(text: str, name: str) -> list[str]:
    """Return a frontmatter property's values, handling scalar and YAML lists.

    Supports `name: value`, flow lists `name: [a, b]`, and block lists with
    `  - item` on the following lines (used by superseded_by with multiple
    successors).
    """
    if not text.startswith("---"):
        return []
    end = text.find("\n---", 3)
    if end == -1:
        return []
    lines = text[3:end].splitlines()
    for i, line in enumerate(lines):
        m = re.match(rf"{re.escape(name)}:\s*(.*)", line.strip())
        if not m:
            continue
        inline = m.group(1).strip()
        if inline.startswith("[") and inline.endswith("]"):
            body = inline[1:-1]
            return [v.strip().strip("\"'") for v in body.split(",") if v.strip()]
        if inline:
            return [inline.strip("\"'")]
        values = []
        for follow in lines[i + 1:]:
            stripped = follow.strip()
            if not stripped:
                break
            item = re.match(r"-\s+(.*)", stripped)
            if not item:
                break  # reached the next key
            values.append(item.group(1).strip().strip("\"'"))
        return values
    return []


def linkable_markdown(text: str) -> str:
    """Remove code regions that Obsidian does not interpret as wikilinks."""
    return INLINE_CODE.sub("", FENCED_CODE.sub("", text))


def normalize_search_query(query: str) -> str:
    """Normalize AI/user query syntax; terms are NFKC normalized and quoted internally for FTS5."""
    return " ".join(nfkc(query).translate(SEARCH_QUOTES).split())


def like_pattern(term: str) -> str:
    """Build a literal contains pattern for SQLite LIKE."""
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def fts_phrase(term: str) -> str:
    """Quote one literal phrase for an FTS5 MATCH expression."""
    return f'"{term.replace(chr(34), chr(34) * 2)}"'


def iter_notes():
    for p in sorted(VAULT.rglob("*.md")):
        rel = p.relative_to(VAULT)
        if any(part.startswith(".") for part in rel.parts):
            continue  # .obsidian / .trash / .git
        if rel.parts and rel.parts[0] in INDEX_EXEMPT_DIRS:
            continue  # Templater sources are generators, not knowledge notes
        rel_nfc = nfc(rel.as_posix())
        if rel_nfc in INDEX_EXEMPT_PATHS:
            continue  # Runtime instructions are not Vault knowledge notes
        yield p, rel_nfc, "vault"


def iter_memory_notes():
    """Optional VAULT_SEARCH_MEMORY_DIR entries, indexed under the memory/ path prefix."""
    if MEMORY_DIR is None or not MEMORY_DIR.exists():
        return
    for p in sorted(MEMORY_DIR.rglob("*.md")):
        yield p, MEMORY_PREFIX + nfc(p.relative_to(MEMORY_DIR).as_posix()), "memory"


def previous_vault_count():
    """Vault notes in the DB currently on disk, or None if there is no usable DB."""
    if not DB.exists():
        return None
    try:
        con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
        try:
            return con.execute("SELECT count(*) FROM notes WHERE source='vault'").fetchone()[0]
        finally:
            con.close()
    except sqlite3.Error:
        return None


def build(force=False):
    DB.parent.mkdir(parents=True, exist_ok=True)
    tmp = DB.with_suffix(".db.tmp")
    tmp.unlink(missing_ok=True)
    con = sqlite3.connect(tmp)
    con.executescript(
        """
        CREATE TABLE notes(
            path TEXT PRIMARY KEY, title TEXT, folder TEXT,
            description TEXT, lifecycle TEXT, visibility TEXT,
            orphan_status TEXT, superseded_by TEXT, mtime TEXT, size INTEGER,
            source TEXT);
        CREATE TABLE links(src TEXT, dst_title TEXT, dst_path TEXT);
        CREATE VIRTUAL TABLE notes_fts USING fts5(
            path UNINDEXED, title, description, body, tokenize='trigram');
        CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);
        """
    )

    notes, fts_entries = [], []
    by_title = {}
    vault_bodies = {}
    max_mtime_ts = 0.0
    for p, rel, source in (*iter_notes(), *iter_memory_notes()):
        try:
            raw_bytes = p.read_bytes()
            text = nfc(raw_bytes.decode("utf-8", errors="replace"))
            st = p.stat()
            if source == "vault" and st.st_mtime > max_mtime_ts:
                max_mtime_ts = st.st_mtime
        except OSError as e:
            print(f"skip {rel}: {e}", file=sys.stderr)
            continue
        title = nfc(p.stem)
        folder = rel.split("/")[0] if "/" in rel else "."
        desc = parse_scalar_property(text, "description")
        lifecycle = parse_scalar_property(text, "lifecycle")
        visibility = parse_scalar_property(text, "visibility")
        orphan_status = parse_scalar_property(text, "orphan_status")
        superseded_by = "\n".join(parse_property_values(text, "superseded_by")) or None
        if lifecycle is None:
            lifecycle = next(
                (value for prefix, value in DEFAULT_LIFECYCLE_BY_PREFIX if rel.startswith(prefix)),
                None,
            )
        mtime = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d")
        notes.append(
            (
                rel, title, folder, desc, lifecycle, visibility,
                orphan_status, superseded_by, mtime, len(text), source,
            )
        )
        # For FTS, store NFKC-normalized text so search matches half/full-width variants
        fts_entries.append((rel, nfkc(title), nfkc(desc or ""), nfkc(text)))
        if source != "vault":
            continue  # memory entries are searchable, but not graph nodes
        vault_bodies[rel] = text
        # Obsidian resolves by basename; on collision prefer the shorter path
        if title not in by_title or len(rel) < len(by_title[title]):
            by_title[title] = rel

    links = []
    for rel, text in vault_bodies.items():
        for m in WIKILINK.finditer(linkable_markdown(text)):
            target = m.group(1).strip().rstrip("\\").strip()
            if not target or Path(target).suffix.lower() in ASSET_EXT:
                continue
            base = target[:-3] if target.endswith(".md") else target
            dst = None
            if (VAULT / (base + ".md")).exists():  # path-style link
                dst = base + ".md"
            else:
                dst = by_title.get(base.split("/")[-1])
            links.append((rel, base.split("/")[-1], dst))

    n_memory = sum(1 for n in notes if n[10] == "memory")
    n_vault = len(notes) - n_memory

    con.executemany("INSERT INTO notes VALUES(?,?,?,?,?,?,?,?,?,?,?)", notes)
    con.executemany("INSERT INTO links VALUES(?,?,?)", links)
    con.executemany("INSERT INTO notes_fts VALUES(?,?,?,?)", fts_entries)
    con.executemany(
        "INSERT INTO meta VALUES(?,?)",
        [
            ("vault_count", str(n_vault)),
            ("max_mtime", str(max_mtime_ts)),
            ("built_at", datetime.now().isoformat()),
        ],
    )
    con.commit()
    con.close()

    # Guard: a transient read failure on the Vault (macOS EPERM, unmounted disk,
    # permissions) makes iter_notes() come back empty. Replacing the DB then wipes
    # a working index and search silently returns nothing. Keep the old DB instead.
    prev = previous_vault_count()
    reason = None
    if n_vault == 0:
        reason = "found 0 vault notes"
    elif prev and n_vault < prev * 0.5:
        reason = f"vault notes dropped {prev} -> {n_vault} (more than half gone)"
    if reason and not force:
        tmp.unlink(missing_ok=True)
        print(
            f"ABORTED: {reason}. Kept the existing index at {DB}.\n"
            f"  Check the Vault is readable: ls '{VAULT}'\n"
            f"  If the drop is real (mass deletion), rerun with: vault_search.py build --force",
            file=sys.stderr,
        )
        return 1

    tmp.replace(DB)
    print(
        f"built: {n_vault} notes, {len(links)} links, "
        f"{n_memory} memory -> {DB}"
    )
    return 0


def connect():
    if not DB.exists():
        print(f"error: {DB} not found. Run: vault_search.py build", file=sys.stderr)
        sys.exit(1)
    con = sqlite3.connect(DB)
    check_freshness(con)
    return con


def check_freshness(con):
    """Warn on stderr if the Vault has changed since the last build (approx. 0.1s)."""
    try:
        rows = dict(con.execute("SELECT key, value FROM meta").fetchall())
        exp_count = int(rows.get("vault_count", -1))
        exp_mtime = float(rows.get("max_mtime", -1.0))
    except sqlite3.Error:
        return
    if exp_count < 0 or exp_mtime < 0:
        return

    cur_count = 0
    cur_max_mtime = 0.0
    for p, _, _ in iter_notes():
        cur_count += 1
        try:
            mt = p.stat().st_mtime
            if mt > cur_max_mtime:
                cur_max_mtime = mt
        except OSError:
            pass
    if cur_count != exp_count or cur_max_mtime > exp_mtime + 0.001:
        print("WARNING: index is stale. Run: vault_search.py build", file=sys.stderr)


def configure(args) -> None:
    global VAULT, DB, MEMORY_DIR, INDEX_EXEMPT_DIRS
    vault = args.vault or os.environ.get("VAULT_SEARCH_VAULT") or os.environ.get("KURA_VAULT")
    if not vault:
        print(
            "error: set --vault or VAULT_SEARCH_VAULT to your Obsidian Vault path",
            file=sys.stderr,
        )
        sys.exit(2)
    VAULT = Path(vault).expanduser()
    if not VAULT.is_dir():
        print(f"error: Vault not found: {VAULT}", file=sys.stderr)
        sys.exit(2)
    db = args.db or os.environ.get("VAULT_SEARCH_DB") or os.environ.get("KURA_DB")
    DB = Path(db).expanduser() if db else default_db_path(VAULT)
    memory = (
        args.memory_dir
        or os.environ.get("VAULT_SEARCH_MEMORY_DIR")
        or os.environ.get("KURA_MEMORY_DIR")
    )
    MEMORY_DIR = Path(memory).expanduser() if memory else None
    exclude = (
        args.exclude
        if args.exclude is not None
        else (os.environ.get("VAULT_SEARCH_EXCLUDE") or os.environ.get("KURA_EXCLUDE"))
    )
    if exclude is not None:
        INDEX_EXEMPT_DIRS = {nfc(d.strip().strip("/")) for d in exclude.split(",") if d.strip()}


def check_sqlite() -> None:
    try:
        con = sqlite3.connect(":memory:")
        con.execute("CREATE VIRTUAL TABLE t USING fts5(x, tokenize='trigram')")
        con.close()
    except sqlite3.Error as e:
        print(
            f"error: this Python's SQLite ({sqlite3.sqlite_version}) lacks the FTS5 "
            f"trigram tokenizer (needs 3.34+): {e}",
            file=sys.stderr,
        )
        sys.exit(2)


def resolve(con, note: str):
    """Accept a title or a vault-relative path; return the note's path."""
    note = nfc(note)
    base = note[:-3] if note.endswith(".md") else note
    row = con.execute(
        "SELECT path FROM notes WHERE (path = ? OR title = ?) AND source = 'vault' "
        "ORDER BY length(path) LIMIT 1",
        (base + ".md", base.split("/")[-1]),
    ).fetchone()
    if not row:
        print(f"error: note not found: {note}", file=sys.stderr)
        sys.exit(1)
    return row[0]


def cmd_map(args):
    con = connect()
    q = "SELECT path, coalesce(description,'') FROM notes"
    conditions = ["source = 'vault'"]  # map is the Vault's note map
    params = []
    if args.folder:
        conditions.append("folder = ?")
        params.append(nfc(args.folder))
    if args.lifecycle == "unclassified":
        conditions.append("lifecycle IS NULL")
    elif args.lifecycle:
        conditions.append("lifecycle = ?")
        params.append(args.lifecycle)
    if conditions:
        q += " WHERE " + " AND ".join(conditions)
    for path, desc in con.execute(q + " ORDER BY path", params):
        print(f"{path}\t{desc}")


def cmd_search(args):
    con = connect()
    q = normalize_search_query(args.q)
    if not q:
        print("error: search query is empty after normalization", file=sys.stderr)
        raise SystemExit(2)
    include_retired = args.include_all or args.include_retired
    include_internal = args.include_all or args.include_internal
    filters = []
    if args.scope != "all":
        filters.append(f"n.source = '{args.scope}'")
    if not include_retired:
        filters.append(
            "coalesce(n.lifecycle, 'active') NOT IN ('superseded', 'archive')"
        )
    if not include_internal:
        filters.append("coalesce(n.visibility, '') != 'internal'")
    search_filter = "".join(f" AND {condition}" for condition in filters)
    lifecycle_order = (
        "CASE WHEN n.lifecycle = 'active' THEN 0 "
        "WHEN n.lifecycle IS NULL OR n.lifecycle = 'reference' THEN 1 "
        "WHEN n.lifecycle = 'raw' THEN 2 ELSE 3 END"
    )
    # space-separated terms => AND by default (--any switches the whole query to OR).
    terms = [t for t in q.split() if t]
    op = "OR" if getattr(args, "any", False) else "AND"
    if terms and all(len(t) >= 3 for t in terms):
        joiner = " OR " if op == "OR" else " "  # space = implicit AND in FTS5
        match = joiner.join(fts_phrase(t) for t in terms)
        q_like = like_pattern(q)
        rows = con.execute(
            "SELECT notes_fts.path, snippet(notes_fts, 3, '[', ']', '…', 24) "
            "FROM notes_fts JOIN notes n ON n.path = notes_fts.path "
            f"WHERE notes_fts MATCH ?{search_filter} "
            "ORDER BY CASE WHEN notes_fts.title = ? THEN 0 ELSE 1 END, "
            f"{lifecycle_order}, "
            "CASE WHEN notes_fts.title LIKE ? ESCAPE '\\' THEN 0 "
            "WHEN notes_fts.description LIKE ? ESCAPE '\\' THEN 1 ELSE 2 END, "
            "bm25(notes_fts, 0.0, 8.0, 4.0, 1.0) LIMIT ?",
            (match, q, q_like, q_like, args.k),
        ).fetchall()
    else:
        needles = terms or [q]
        where = f" {op} ".join(
            "(notes_fts.title LIKE ? ESCAPE '\\' "
            "OR notes_fts.description LIKE ? ESCAPE '\\' "
            "OR notes_fts.body LIKE ? ESCAPE '\\')" for _ in needles
        )
        params = []
        for t in needles:
            pattern = like_pattern(t)
            params += [pattern, pattern, pattern]
        score = " + ".join(
            "(CASE WHEN notes_fts.title LIKE ? ESCAPE '\\' THEN 8 ELSE 0 END + "
            "CASE WHEN notes_fts.description LIKE ? ESCAPE '\\' THEN 4 ELSE 0 END + "
            "CASE WHEN notes_fts.body LIKE ? ESCAPE '\\' THEN 1 ELSE 0 END)"
            for _ in needles
        )
        score_params = []
        for t in needles:
            pattern = like_pattern(t)
            score_params += [pattern, pattern, pattern]
        query_params = score_params + params + [q, args.k]
        rows = []
        for path, title, desc, body, _hit_score in con.execute(
            "SELECT notes_fts.path, notes_fts.title, notes_fts.description, "
            "notes_fts.body, "
            f"({score}) AS hit_score FROM notes_fts "
            "JOIN notes n ON n.path = notes_fts.path "
            f"WHERE ({where}){search_filter} "
            "ORDER BY CASE WHEN notes_fts.title = ? THEN 0 ELSE 1 END, "
            f"{lifecycle_order}, hit_score DESC, "
            "length(notes_fts.title) LIMIT ?",
            query_params,
        ):
            i = body.find(needles[0])
            ctx = body[max(0, i - 24):i + 24].replace("\n", " ") if i >= 0 else (desc or title)
            rows.append((path, f"…{ctx}…"))
    for path, snip in rows:
        print(f"{path}\t{' '.join(snip.split())}")
    if not rows:
        print("(no hits)", file=sys.stderr)


def cmd_links(args):
    con = connect()
    src = resolve(con, args.note)
    for title, dst in con.execute(
        "SELECT dst_title, dst_path FROM links WHERE src = ? ORDER BY dst_path", (src,)
    ):
        print(f"{dst or '(broken: ' + title + ')'}")


def cmd_backlinks(args):
    con = connect()
    dst = resolve(con, args.note)
    for (src,) in con.execute(
        "SELECT DISTINCT src FROM links WHERE dst_path = ? ORDER BY src", (dst,)
    ):
        print(src)


def cmd_orphans(_args):
    con = connect()
    rows = con.execute(
        "SELECT path, title FROM notes "
        "WHERE path NOT IN (SELECT dst_path FROM links WHERE dst_path IS NOT NULL) "
        "AND coalesce(orphan_status, '') != 'intentional' AND source = 'vault' "
        "ORDER BY path"
    ).fetchall()
    n = 0
    for path, title in rows:
        if ORPHAN_EXEMPT.search(title):
            continue
        print(path)
        n += 1
    print(f"-- {n} orphans", file=sys.stderr)


def memory_slugs() -> set:
    if MEMORY_DIR is None or not MEMORY_DIR.exists():
        return set()
    return {nfc(p.stem) for p in MEMORY_DIR.rglob("*.md")}


def print_property_issues(con, column: str, allowed: set[str]):
    placeholders = ", ".join("?" for _ in allowed)
    rows = con.execute(
        f"SELECT path, {column} FROM notes "
        f"WHERE {column} IS NOT NULL AND {column} NOT IN ({placeholders}) "
        "AND source = 'vault' ORDER BY path",
        tuple(sorted(allowed)),
    ).fetchall()
    print(f"\n## invalid {column}: {len(rows)}")
    for path, value in rows:
        print(f"{path}\t{value}")


def superseded_target_resolves(con, value: str) -> bool:
    match = WIKILINK.fullmatch(value.strip())
    if not match:
        return False
    target = match.group(1).strip().rstrip("\\").strip()
    base = target[:-3] if target.endswith(".md") else target
    return con.execute(
        "SELECT 1 FROM notes WHERE (path = ? OR title = ?) AND source = 'vault' LIMIT 1",
        (base + ".md", base.split("/")[-1]),
    ).fetchone() is not None


def cmd_check(_args):
    con = connect()
    raw = con.execute(
        "SELECT src, dst_title FROM links WHERE dst_path IS NULL ORDER BY src"
    ).fetchall()
    mem = memory_slugs()
    broken = [(src, title) for src, title in raw if nfc(title) not in mem]
    suppressed = len(raw) - len(broken)
    note = f" ({suppressed} memory refs suppressed)" if suppressed else ""
    print(f"## broken wikilinks: {len(broken)}{note}")
    for src, title in broken:
        print(f"{src}\t[[{title}]]")

    # Check unverified markers ([要確認] / ［要確認］)
    unverified = []
    for p, rel, _ in iter_notes():
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
            for lineno, line in enumerate(text.splitlines(), start=1):
                if UNVERIFIED_PATTERN.search(line):
                    unverified.append((rel, lineno, line.strip()))
        except OSError:
            pass
    print(f"\n## unverified markers ([要確認]): {len(unverified)}")
    for path, lineno, line in unverified:
        snip = line[:60] + "..." if len(line) > 60 else line
        print(f"{path}:{lineno}\t{snip}")

    missing = [
        (path, title)
        for path, title in con.execute(
            "SELECT path, title FROM notes "
            "WHERE description IS NULL AND source = 'vault' ORDER BY path"
        )
        if not ORPHAN_EXEMPT.search(title)
    ]
    print(f"\n## missing description: {len(missing)}")
    for path, _ in missing:
        print(path)

    print_property_issues(con, "lifecycle", VALID_LIFECYCLE)
    print_property_issues(con, "visibility", VALID_VISIBILITY)
    print_property_issues(con, "orphan_status", VALID_ORPHAN_STATUS)

    superseded = con.execute(
        "SELECT path, superseded_by FROM notes "
        "WHERE lifecycle = 'superseded' AND source = 'vault' ORDER BY path"
    ).fetchall()
    missing_successor = [(path, value) for path, value in superseded if not value]
    invalid_successor = [
        (path, successor)
        for path, value in superseded
        for successor in (value or "").splitlines()
        if not superseded_target_resolves(con, successor)
    ]
    print(f"\n## superseded without superseded_by: {len(missing_successor)}")
    for path, _ in missing_successor:
        print(path)
    print(f"\n## invalid superseded_by: {len(invalid_successor)}")
    for path, value in invalid_successor:
        print(f"{path}\t{value}")

    # Check: superseded_by is set, but lifecycle is not superseded
    mismatched_lifecycle = con.execute(
        "SELECT path, lifecycle, superseded_by FROM notes "
        "WHERE superseded_by IS NOT NULL AND coalesce(lifecycle, '') != 'superseded' "
        "AND source = 'vault' ORDER BY path"
    ).fetchall()
    print(f"\n## superseded_by set but lifecycle not superseded: {len(mismatched_lifecycle)}")
    for path, lc, succ in mismatched_lifecycle:
        succ_first = succ.splitlines()[0] if succ else ""
        print(f"{path}\t(lifecycle: {lc or 'none'}, superseded_by: {succ_first})")

    duplicates = con.execute(
        "SELECT title, count(*) FROM notes WHERE source = 'vault' "
        "GROUP BY title HAVING count(*) > 1 ORDER BY count(*) DESC, title"
    ).fetchall()
    print(f"\n## duplicate titles: {len(duplicates)} groups")
    for title, count in duplicates:
        print(f"{title}\t{count}")
        for (path,) in con.execute(
            "SELECT path FROM notes WHERE title = ? AND source = 'vault' ORDER BY path",
            (title,),
        ):
            print(f"  {path}")


# --- scan command (read-only inventory before import) ---
IMPORT_EXTS = (".md", ".txt", ".markdown", ".rtf", ".docx", ".pdf", ".text")


def norm_cluster_title(name: str) -> str:
    """Strip common suffix variations to cluster potential editions of the same document."""
    t = nfc(name).lower()
    t = re.sub(r"\.[a-z0-9]+$", "", t)
    t = re.sub(r"(のコピー|copy|コピー|最終|最新|改訂|修正|バージョン)", "", t)
    t = re.sub(r"[_\-\s]*v?\d+(\.\d+)?$", "", t)
    t = re.sub(r"[\(（]\d+[\)）]", "", t)
    t = re.sub(r"\d{4}[-_年]?\d{1,2}[-_月]?\d{1,2}日?", "", t)
    return re.sub(r"[\s_\-]+", "", t)


def first_readable_line(path: Path) -> str:
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip().lstrip("#").strip()
                if line and not line.startswith("---"):
                    return nfc(line)[:40]
    except Exception:
        pass
    return ""


def cmd_scan(args):
    """Read-only inventory of a directory before importing files into Vault."""
    root = Path(args.folder).expanduser()
    if not root.exists():
        print(f"error: directory not found: {root}", file=sys.stderr)
        sys.exit(1)
    files = [
        p for p in sorted(root.rglob("*"))
        if p.is_file() and p.suffix.lower() in IMPORT_EXTS and not p.name.startswith(".")
    ]
    if not files:
        print(
            f"No importable files found in {root} (supported: {', '.join(IMPORT_EXTS)})",
            file=sys.stderr,
        )
        return

    print(f"# Import Inventory: {root}\n")
    print(f"Total: **{len(files)} files**. (Read-only scan; no files were modified.)\n")

    by_ext = {}
    for p in files:
        ext = p.suffix.lower()
        by_ext[ext] = by_ext.get(ext, 0) + 1
    print("## Format breakdown")
    for ext, cnt in sorted(by_ext.items(), key=lambda x: -x[1]):
        note = "" if ext in (".md", ".txt", ".markdown", ".text") else " (requires text extraction)"
        print(f"- `{ext}`: {cnt} files{note}")

    days = sorted(date.fromtimestamp(p.stat().st_mtime) for p in files)
    print(f"\nDate range: {days[0]} - {days[-1]}\n")

    print("## Files (newest first)")
    print("| Date | Size (KB) | Path | First line |")
    print("|---|---|---|---|")
    for p in sorted(files, key=lambda x: -x.stat().st_mtime):
        d = date.fromtimestamp(p.stat().st_mtime)
        rel = nfc(p.relative_to(root).as_posix())
        sz = p.stat().st_size // 1024
        print(f"| {d} | {sz} | {rel} | {first_readable_line(p)} |")

    # Group potential revisions
    groups, used = [], set()
    for i, a in enumerate(files):
        if i in used:
            continue
        na = norm_cluster_title(a.name)
        cluster = [a]
        for j, b in enumerate(files[i + 1:], start=i + 1):
            if j in used:
                continue
            if difflib.SequenceMatcher(None, na, norm_cluster_title(b.name)).ratio() >= 0.8:
                cluster.append(b)
                used.add(j)
        if len(cluster) > 1:
            groups.append(cluster)

    if groups:
        print("\n## Potential revision clusters (confirm current version before importing)")
        for g in groups:
            print(f"- {len(g)} files:")
            for p in sorted(g, key=lambda x: -x.stat().st_mtime):
                d = date.fromtimestamp(p.stat().st_mtime)
                print(f"  - {d}  {nfc(p.relative_to(root).as_posix())}")


def main():
    p = argparse.ArgumentParser(
        description="SQLite full-text index & check for an Obsidian Vault"
    )
    p.add_argument("--vault", help="Vault root (env: VAULT_SEARCH_VAULT / KURA_VAULT)")
    p.add_argument("--db", help="index path (env: VAULT_SEARCH_DB / KURA_DB)")
    p.add_argument(
        "--memory-dir",
        help="extra notes for --scope memory (env: VAULT_SEARCH_MEMORY_DIR)",
    )
    p.add_argument(
        "--exclude",
        help="comma-separated top-level folders to skip (env: VAULT_SEARCH_EXCLUDE)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("build")
    sp.add_argument(
        "--force",
        action="store_true",
        help="rebuild even if the vault note count collapsed (real mass deletion)",
    )

    sp = sub.add_parser("map")
    sp.add_argument("--folder")
    sp.add_argument(
        "--lifecycle",
        choices=("active", "reference", "raw", "superseded", "archive", "unclassified"),
    )

    sp = sub.add_parser("search")
    sp.add_argument(
        "q",
        help="space-separated terms are AND by default; quotes are unnecessary",
    )
    sp.add_argument("--k", type=int, default=10, help="maximum results (default: 10)")
    sp.add_argument(
        "--any",
        action="store_true",
        help="OR across space-separated terms (default is AND)",
    )
    sp.add_argument(
        "--scope",
        choices=("vault", "memory", "all"),
        default="vault",
        help="what to search: the Vault (default), memory-dir, or both",
    )
    sp.add_argument(
        "--include-retired",
        action="store_true",
        help="include notes marked superseded or archive (and inbox/archive/)",
    )
    sp.add_argument(
        "--include-internal",
        action="store_true",
        help="include notes marked visibility: internal",
    )
    sp.add_argument(
        "--all",
        dest="include_all",
        action="store_true",
        help="include retired and internal notes (both flags above)",
    )

    sp = sub.add_parser("links")
    sp.add_argument("note")

    sp = sub.add_parser("backlinks")
    sp.add_argument("note")

    sub.add_parser("orphans")
    sub.add_parser("check")

    sp = sub.add_parser("scan")
    sp.add_argument("folder", help="source folder to inspect before importing")

    args = p.parse_args()
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")  # Windows consoles default to cp932
    configure(args)
    check_sqlite()
    if args.cmd == "build":
        sys.exit(build(force=args.force))
    elif args.cmd == "scan":
        cmd_scan(args)
    else:
        {
            "map": cmd_map,
            "search": cmd_search,
            "links": cmd_links,
            "backlinks": cmd_backlinks,
            "orphans": cmd_orphans,
            "check": cmd_check,
        }[args.cmd](args)


if __name__ == "__main__":
    main()
