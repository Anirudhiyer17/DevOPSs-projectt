#!/usr/bin/env python3
"""
Database Seeding Script for Security Incident Case Management System.
Populates realistic SOC incidents for college presentations, testing, or demonstrations.

Usage:
    python seed.py          # Populates if database is empty
    python seed.py --force  # Overwrites and repopulates sample incidents
"""
import sys
import os
from app import create_app
from app.models import db, Incident, InvestigationNote, AuditLog
from app.utils import seed_sample_incidents

def main():
    force = '--force' in sys.argv
    app = create_app('development')

    with app.app_context():
        if force:
            print("Resetting existing incidents, notes, and audit logs...")
            AuditLog.query.delete()
            InvestigationNote.query.delete()
            Incident.query.delete()
            db.session.commit()

        db.create_all()
        count = seed_sample_incidents(db, force=force)
        print(f"Successfully seeded {count} cybersecurity incidents with investigation dossiers into database.")

if __name__ == '__main__':
    main()
