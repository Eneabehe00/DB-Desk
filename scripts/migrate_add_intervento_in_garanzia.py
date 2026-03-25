#!/usr/bin/env python
"""
Migrazione: aggiunge la colonna intervento_in_garanzia alla tabella fogli_tecnici.
Eseguire dalla root del progetto: python scripts/migrate_add_intervento_in_garanzia.py
"""
import sys
import os

# Aggiungi la root del progetto al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_migration():
    from sqlalchemy import text
    from app import create_app, db
    
    app = create_app()
    with app.app_context():
        try:
            # MySQL/MariaDB
            db.session.execute(text("""
                ALTER TABLE fogli_tecnici
                ADD COLUMN intervento_in_garanzia TINYINT(1) NOT NULL DEFAULT 0
                COMMENT 'Intervento in garanzia (0=No, 1=Sì)'
            """))
            db.session.commit()
            print("OK: Colonna 'intervento_in_garanzia' aggiunta a fogli_tecnici.")
        except Exception as e:
            if 'Duplicate column name' in str(e) or '1060' in str(e):
                print("La colonna 'intervento_in_garanzia' esiste già. Nessuna modifica.")
                db.session.rollback()
            else:
                db.session.rollback()
                raise

if __name__ == '__main__':
    run_migration()
