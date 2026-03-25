#!/usr/bin/env python
"""
Migrazione: aggiunge la colonna sigla alla tabella departments.
La sigla viene usata per la numerazione dei fogli tecnici (es. MEC, GA, IT).
Eseguire dalla root del progetto: python scripts/migrate_add_sigla_department.py
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def run_migration():
    from sqlalchemy import text
    from app import create_app, db

    app = create_app()
    with app.app_context():
        try:
            db.session.execute(text("""
                ALTER TABLE departments
                ADD COLUMN sigla VARCHAR(10) NULL
                COMMENT 'Sigla per numerazione fogli tecnici (es. MEC, GA, IT)'
            """))
            db.session.commit()
            print("OK: Colonna 'sigla' aggiunta a departments.")
        except Exception as e:
            if 'Duplicate column name' in str(e) or '1060' in str(e):
                print("La colonna 'sigla' esiste già. Nessuna modifica.")
                db.session.rollback()
            else:
                db.session.rollback()
                raise


if __name__ == '__main__':
    run_migration()
