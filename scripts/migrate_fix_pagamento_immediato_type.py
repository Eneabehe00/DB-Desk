#!/usr/bin/env python
"""
Migrazione: converte pagamento_immediato da VARCHAR a TINYINT(1).

Il tipo VARCHAR causava la lettura errata di '0' come True (pagato).

Eseguire dalla root del progetto:
    python scripts/migrate_fix_pagamento_immediato_type.py
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def run_migration():
    from sqlalchemy import inspect, text
    from app import create_app, db

    app = create_app()
    with app.app_context():
        inspector = inspect(db.engine)
        if 'fogli_tecnici' not in inspector.get_table_names():
            print("Tabella fogli_tecnici non trovata. Nessuna modifica.")
            return

        columns = {col['name']: col for col in inspector.get_columns('fogli_tecnici')}
        pagamento_col = columns.get('pagamento_immediato')
        if not pagamento_col:
            print("Colonna pagamento_immediato non trovata. Nessuna modifica.")
            return

        col_type = str(pagamento_col['type']).lower()
        if 'tinyint' in col_type or col_type in ('boolean', 'bool'):
            print("Colonna pagamento_immediato già di tipo booleano. Nessuna modifica.")
            return

        with db.engine.begin() as connection:
            connection.execute(text(
                "UPDATE fogli_tecnici SET pagamento_immediato = CASE "
                "WHEN pagamento_immediato IN ('1', 'true', 'True', 'yes', 'y', 't') THEN 1 "
                "ELSE 0 END"
            ))
            connection.execute(text(
                "ALTER TABLE fogli_tecnici "
                "MODIFY COLUMN pagamento_immediato TINYINT(1) NOT NULL DEFAULT 0 "
                "COMMENT 'Intervento già pagato (0=No, 1=Sì)'"
            ))

        print("OK: Colonna pagamento_immediato convertita a TINYINT(1).")


if __name__ == '__main__':
    run_migration()
