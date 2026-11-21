import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def get_utc_now():
    """Returns timezone-aware UTC datetime."""
    return datetime.datetime.now(datetime.timezone.utc)


class Incident(db.Model):
    """Represents a cybersecurity incident reported within the organization."""
    __tablename__ = 'incidents'

    id = db.Column(db.Integer, primary_key=True)
    incident_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), nullable=False, default='Medium', index=True)
    status = db.Column(db.String(30), nullable=False, default='Open', index=True)
    category = db.Column(db.String(50), nullable=False, default='Malware', index=True)
    affected_system = db.Column(db.String(150), nullable=False)
    assigned_to = db.Column(db.String(100), nullable=False, default='Unassigned')
    reporter = db.Column(db.String(100), nullable=False, default='SOC Analyst')
    created_at = db.Column(db.DateTime, default=get_utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)
    resolved_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    notes = db.relationship(
        'InvestigationNote',
        backref='incident',
        cascade='all, delete-orphan',
        order_by='InvestigationNote.created_at.desc()',
        lazy='select'
    )
    audit_logs = db.relationship(
        'AuditLog',
        backref='incident',
        cascade='all, delete-orphan',
        order_by='AuditLog.timestamp.desc()',
        lazy='select'
    )

    SEVERITY_LEVELS = ['Critical', 'High', 'Medium', 'Low']
    STATUS_CHOICES = ['Open', 'Investigating', 'Mitigated', 'Resolved', 'Closed']
    CATEGORIES = [
        'Phishing',
        'Ransomware',
        'Malware',
        'Unauthorized Access',
        'DDoS Attack',
        'Data Exfiltration',
        'Privilege Escalation',
        'Policy Violation',
        'Vulnerability Exploit',
        'Other'
    ]

    def to_dict(self):
        """Serialize incident model to a dictionary."""
        return {
            'id': self.id,
            'incident_number': self.incident_number,
            'title': self.title,
            'description': self.description,
            'severity': self.severity,
            'status': self.status,
            'category': self.category,
            'affected_system': self.affected_system,
            'assigned_to': self.assigned_to,
            'reporter': self.reporter,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            'resolved_at': self.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if self.resolved_at else None,
            'notes_count': len(self.notes),
            'audit_count': len(self.audit_logs)
        }

    def __repr__(self):
        return f'<Incident {self.incident_number}: {self.title}>'


class InvestigationNote(db.Model):
    """Analyst investigation notes attached to an incident."""
    __tablename__ = 'investigation_notes'

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.id', ondelete='CASCADE'), nullable=False, index=True)
    author = db.Column(db.String(100), nullable=False, default='SOC Analyst')
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=get_utc_now, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'incident_id': self.incident_id,
            'author': self.author,
            'content': self.content,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

    def __repr__(self):
        return f'<InvestigationNote id={self.id} incident_id={self.incident_id} author={self.author}>'


class AuditLog(db.Model):
    """Immutable audit trail of actions taken on an incident."""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.id', ondelete='CASCADE'), nullable=False, index=True)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=False)
    performed_by = db.Column(db.String(100), nullable=False, default='System')
    timestamp = db.Column(db.DateTime, default=get_utc_now, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'incident_id': self.incident_id,
            'action': self.action,
            'details': self.details,
            'performed_by': self.performed_by,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.timestamp else None
        }

    def __repr__(self):
        return f'<AuditLog id={self.id} incident_id={self.incident_id} action={self.action}>'
