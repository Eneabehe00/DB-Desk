"""Ripristina un ticket dal backup mysqldump per id/numero_ticket."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text, inspect

BACKUP_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'backups',
    'dbdesk_backup_20260521_153226.sql',
)
TICKET_NUMBER = 'TK2026050074'
TICKET_ID = 1597


def _extract_sql_tuple(content: str, start: int) -> str:
    """Estrae una tupla SQL ( ... ) a partire da start (su '(')."""
    if content[start] != '(':
        raise ValueError('start must be on opening paren')
    depth = 0
    in_string = False
    escape = False
    i = start
    while i < len(content):
        ch = content[i]
        if in_string:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == "'":
                if i + 1 < len(content) and content[i + 1] == "'":
                    i += 1
                else:
                    in_string = False
            i += 1
            continue
        if ch == "'":
            in_string = True
        elif ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0:
                return content[start : i + 1]
        i += 1
    raise ValueError('tuple non terminata')


def _find_related_tuples(content: str, table: str, ticket_id: int):
    marker = f"INSERT INTO `{table}` VALUES "
    pos = 0
    rows = []
    needle_id = f"({ticket_id},"
    needle_mid = f",{ticket_id},"
    needle_end = f",{ticket_id})"
    while True:
        idx = content.find(marker, pos)
        if idx == -1:
            break
        blob_start = idx + len(marker)
        blob_end = content.find('\n\n', blob_start)
        if blob_end == -1:
            blob_end = len(content)
        blob = content[blob_start:blob_end]
        scan = 0
        while scan < len(blob):
            if blob[scan] != '(':
                scan += 1
                continue
            try:
                tup = _extract_sql_tuple(blob, scan)
            except ValueError:
                break
            if needle_id in tup or needle_mid in tup or needle_end in tup:
                rows.append(tup)
            scan += len(tup)
            if scan < len(blob) and blob[scan] == ',':
                scan += 1
        pos = blob_end
    return rows


def main():
    if not os.path.isfile(BACKUP_PATH):
        print(f'Backup non trovato: {BACKUP_PATH}')
        sys.exit(1)

    with open(BACKUP_PATH, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    marker = f"({TICKET_ID},'{TICKET_NUMBER}'"
    start = content.find(marker)
    if start == -1:
        print(f'Ticket {TICKET_NUMBER} non trovato nel backup.')
        sys.exit(1)

    ticket_tuple = _extract_sql_tuple(content, start)

    app = create_app('default')
    with app.app_context():
        existing = db.session.execute(
            text('SELECT id FROM tickets WHERE id = :id OR numero_ticket = :n'),
            {'id': TICKET_ID, 'n': TICKET_NUMBER},
        ).first()
        if existing:
            print(f'Ticket già presente (id={existing[0]}).')
            sys.exit(0)

        db.session.execute(text(f'INSERT INTO `tickets` VALUES {ticket_tuple};'))
        print(f'Ripristinato ticket {TICKET_NUMBER} (id={TICKET_ID})')

        for table in ('ticket_macchine', 'ticket_ricambi', 'ticket_attachments', 'ticket_subtasks'):
            if table not in inspect(db.engine).get_table_names():
                continue
            for row in _find_related_tuples(content, table, TICKET_ID):
                try:
                    db.session.execute(text(f'INSERT INTO `{table}` VALUES {row};'))
                except Exception as exc:
                    print(f'  avviso {table}: {exc}')
            count = len(_find_related_tuples(content, table, TICKET_ID))
            if count:
                print(f'  + {count} righe in {table}')

        db.session.commit()
        row = db.session.execute(
            text('SELECT id, numero_ticket, titolo FROM tickets WHERE numero_ticket = :n'),
            {'n': TICKET_NUMBER},
        ).first()
        print(f'OK: /tickets/{row[0]} — {row[1]} — {row[2]}')


if __name__ == '__main__':
    main()
