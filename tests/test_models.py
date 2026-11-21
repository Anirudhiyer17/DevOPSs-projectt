import datetime
from app.models import db, Incident, InvestigationNote, AuditLog


def test_create_incident(app):
    """Test incident creation and attribute integrity."""
    with app.app_context():
        inc = Incident(
            incident_number='INC-TEST-0002',
            title='Malware Outbreak Test',
            description='Test malware hash flagged.',
            severity='High',
            status='Open',
            category='Malware',
            affected_system='workstation-99'
        )
        db.session.add(inc)
        db.session.commit()

        retrieved = Incident.query.filter_by(incident_number='INC-TEST-0002').first()
        assert retrieved is not None
        assert retrieved.title == 'Malware Outbreak Test'
        assert retrieved.severity == 'High'
        assert retrieved.status == 'Open'
        assert retrieved.affected_system == 'workstation-99'
        assert retrieved.reporter == 'SOC Analyst'  # default value
        assert retrieved.assigned_to == 'Unassigned'  # default value
        assert isinstance(retrieved.created_at, datetime.datetime)


def test_incident_to_dict(app, sample_incident):
    """Test incident serialization to dictionary."""
    with app.app_context():
        inc = db.session.get(Incident, sample_incident.id)
        d = inc.to_dict()
        assert d['incident_number'] == 'INC-TEST-0001'
        assert d['title'] == 'Test Unauthorized Access on Gateway'
        assert d['severity'] == 'Critical'
        assert d['notes_count'] == 1
        assert d['audit_count'] == 1


def test_investigation_note_and_cascade(app):
    """Test creating notes and cascading delete when incident is removed."""
    with app.app_context():
        inc = Incident(
            incident_number='INC-TEST-CASCADE',
            title='Cascade Test Case',
            description='Testing cascade deletions.',
            severity='Low',
            status='Open',
            affected_system='test-srv'
        )
        db.session.add(inc)
        db.session.commit()

        note1 = InvestigationNote(incident_id=inc.id, author='Analyst 1', content='Note 1')
        note2 = InvestigationNote(incident_id=inc.id, author='Analyst 2', content='Note 2')
        audit = AuditLog(incident_id=inc.id, action='Created', details='Details', performed_by='Tester')
        db.session.add_all([note1, note2, audit])
        db.session.commit()

        assert len(inc.notes) == 2
        assert len(inc.audit_logs) == 1

        # Delete incident
        db.session.delete(inc)
        db.session.commit()

        # Check children were cascade deleted
        assert InvestigationNote.query.filter_by(incident_id=inc.id).count() == 0
        assert AuditLog.query.filter_by(incident_id=inc.id).count() == 0


def test_incident_representation(app, sample_incident):
    """Test string representations."""
    with app.app_context():
        inc = db.session.get(Incident, sample_incident.id)
        assert 'INC-TEST-0001' in repr(inc)
