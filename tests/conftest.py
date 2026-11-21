import pytest
from app import create_app
from app.models import db, Incident, InvestigationNote, AuditLog


@pytest.fixture
def app():
    """Create and configure a testing Flask application instance with in-memory SQLite."""
    test_app = create_app('testing')

    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Flask test client for issuing HTTP requests."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """CLI runner for testing commands."""
    return app.test_cli_runner()


@pytest.fixture
def sample_incident(app):
    """Fixture providing a committed sample incident with notes and audit logs."""
    with app.app_context():
        inc = Incident(
            incident_number='INC-TEST-0001',
            title='Test Unauthorized Access on Gateway',
            description='Test description of SSH brute force detection.',
            severity='Critical',
            status='Open',
            category='Unauthorized Access',
            affected_system='gateway-01.test',
            reporter='Automated Sensor',
            assigned_to='Alex Chen'
        )
        db.session.add(inc)
        db.session.flush()

        note = InvestigationNote(
            incident_id=inc.id,
            author='Alex Chen',
            content='Initial IP blocked on firewall.'
        )
        db.session.add(note)

        audit = AuditLog(
            incident_id=inc.id,
            action='Incident Created',
            details='Test incident created via pytest fixture.',
            performed_by='Test Runner'
        )
        db.session.add(audit)
        db.session.commit()

        # Re-query to bind to session
        return db.session.get(Incident, inc.id)
