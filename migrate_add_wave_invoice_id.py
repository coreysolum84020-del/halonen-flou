"""
One-shot migration: adds wave_invoice_id column to subscribers table.
Run once on production: python migrate_add_wave_invoice_id.py
Safe to run multiple times (IF NOT EXISTS).
"""
import os
from app import create_app
from app.extensions import db
from sqlalchemy import text

env = os.environ.get('FLASK_ENV', 'production')
app = create_app(env)

with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text(
            "ALTER TABLE subscribers ADD COLUMN IF NOT EXISTS "
            "wave_invoice_id VARCHAR(200)"
        ))
        conn.commit()
    print("Done: wave_invoice_id column added to subscribers table.")
