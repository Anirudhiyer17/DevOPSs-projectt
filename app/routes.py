from datetime import timedelta
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, jsonify, Response, current_app
)
from app.models import db, Incident, InvestigationNote, AuditLog, get_utc_now
from app.utils import (
    generate_incident_number,
    export_incidents_to_csv,
    seed_sample_incidents
)

main_bp = Blueprint('main', __name__)


# -----------------------------------------------------------------------------
# DASHBOARD
# -----------------------------------------------------------------------------
@main_bp.route('/')
def dashboard():
    """Security Operations Center (SOC) Executive Dashboard."""
    total_incidents = Incident.query.count()
    open_incidents = Incident.query.filter_by(status='Open').count()
    investigating_incidents = Incident.query.filter_by(status='Investigating').count()
    mitigated_incidents = Incident.query.filter_by(status='Mitigated').count()
    resolved_incidents = Incident.query.filter_by(status='Resolved').count()
    closed_incidents = Incident.query.filter_by(status='Closed').count()

    critical_count = Incident.query.filter_by(severity='Critical').count()
    high_count = Incident.query.filter_by(severity='High').count()
    medium_count = Incident.query.filter_by(severity='Medium').count()
    low_count = Incident.query.filter_by(severity='Low').count()

    recent_incidents = Incident.query.order_by(Incident.created_at.desc()).limit(6).all()
    recent_audits = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(8).all()

    stats = {
        'total': total_incidents,
        'open': open_incidents,
        'investigating': investigating_incidents,
        'mitigated': mitigated_incidents,
        'resolved': resolved_incidents,
        'closed': closed_incidents,
        'critical': critical_count,
        'high': high_count,
        'medium': medium_count,
        'low': low_count,
        'active_total': open_incidents + investigating_incidents
    }

    return render_template(
        'dashboard.html',
        stats=stats,
        recent_incidents=recent_incidents,
        recent_audits=recent_audits
    )


# -----------------------------------------------------------------------------
# INCIDENT MANAGEMENT (LIST, SEARCH, FILTER)
# -----------------------------------------------------------------------------
@main_bp.route('/incidents')
def incidents_list():
    """List incidents with multi-parameter search, filtering, and sorting."""
    search_query = request.args.get('q', '').strip()
    severity_filter = request.args.get('severity', '').strip()
    status_filter = request.args.get('status', '').strip()
    category_filter = request.args.get('category', '').strip()
    sort_by = request.args.get('sort', 'newest').strip()

    query = Incident.query

    # Search filter
    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(
            (Incident.title.ilike(search_pattern)) |
            (Incident.incident_number.ilike(search_pattern)) |
            (Incident.affected_system.ilike(search_pattern)) |
            (Incident.description.ilike(search_pattern)) |
            (Incident.assigned_to.ilike(search_pattern))
        )

    # Specific property filters
    if severity_filter and severity_filter in Incident.SEVERITY_LEVELS:
        query = query.filter_by(severity=severity_filter)

    if status_filter and status_filter in Incident.STATUS_CHOICES:
        query = query.filter_by(status=status_filter)

    if category_filter and category_filter in Incident.CATEGORIES:
        query = query.filter_by(category=category_filter)

    # Sorting
    if sort_by == 'oldest':
        query = query.order_by(Incident.created_at.asc())
    elif sort_by == 'severity':
        # Custom case ordering: Critical -> High -> Medium -> Low
        severity_order = db.case(
            (Incident.severity == 'Critical', 1),
            (Incident.severity == 'High', 2),
            (Incident.severity == 'Medium', 3),
            (Incident.severity == 'Low', 4),
            else_=5
        )
        query = query.order_by(severity_order, Incident.created_at.desc())
    else:
        query = query.order_by(Incident.created_at.desc())

    incidents = query.all()

    return render_template(
        'incidents.html',
        incidents=incidents,
        search_query=search_query,
        selected_severity=severity_filter,
        selected_status=status_filter,
        selected_category=category_filter,
        selected_sort=sort_by,
        severity_levels=Incident.SEVERITY_LEVELS,
        status_choices=Incident.STATUS_CHOICES,
        categories=Incident.CATEGORIES,
        total_found=len(incidents)
    )


# -----------------------------------------------------------------------------
# CREATE INCIDENT
# -----------------------------------------------------------------------------
@main_bp.route('/incidents/new', methods=['GET', 'POST'])
def incident_create():
    """Create and report a new security incident."""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        severity = request.form.get('severity', 'Medium').strip()
        category = request.form.get('category', 'Other').strip()
        affected_system = request.form.get('affected_system', '').strip()
        reporter = request.form.get('reporter', 'SOC Analyst').strip()
        assigned_to = request.form.get('assigned_to', 'Unassigned').strip()
        status = request.form.get('status', 'Open').strip()

        # Validation
        errors = []
        if not title:
            errors.append("Incident Title is required.")
        if not description:
            errors.append("Incident Description is required.")
        if not affected_system:
            errors.append("Affected System or Asset is required.")
        if severity not in Incident.SEVERITY_LEVELS:
            errors.append("Invalid severity level selected.")
        if status not in Incident.STATUS_CHOICES:
            status = 'Open'

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template(
                'incident_form.html',
                action='Create',
                severity_levels=Incident.SEVERITY_LEVELS,
                status_choices=Incident.STATUS_CHOICES,
                categories=Incident.CATEGORIES,
                form_data=request.form
            )

        inc_number = generate_incident_number()
        new_incident = Incident(
            incident_number=inc_number,
            title=title,
            description=description,
            severity=severity,
            status=status,
            category=category,
            affected_system=affected_system,
            reporter=reporter if reporter else 'SOC Analyst',
            assigned_to=assigned_to if assigned_to else 'Unassigned'
        )

        db.session.add(new_incident)
        db.session.flush()

        # Create initial audit log entry
        audit_entry = AuditLog(
            incident_id=new_incident.id,
            action='Incident Created',
            details=f"Incident '{title}' recorded with severity '{severity}'. Initial status: '{status}'.",
            performed_by=reporter if reporter else 'SOC Analyst'
        )
        db.session.add(audit_entry)
        db.session.commit()

        current_app.logger.info(
            f"Security Incident Created: [{inc_number}] '{title}' Severity: {severity} by {reporter}"
        )
        flash(f"Incident {inc_number} reported successfully.", 'success')
        return redirect(url_for('main.incident_detail', incident_id=new_incident.id))

    return render_template(
        'incident_form.html',
        action='Create',
        severity_levels=Incident.SEVERITY_LEVELS,
        status_choices=Incident.STATUS_CHOICES,
        categories=Incident.CATEGORIES,
        form_data={}
    )


# -----------------------------------------------------------------------------
# VIEW INCIDENT DETAILS & CASE DOSSIER
# -----------------------------------------------------------------------------
@main_bp.route('/incidents/<int:incident_id>')
def incident_detail(incident_id):
    """View complete incident case dossier, timeline, and investigation notes."""
    incident = db.get_or_404(Incident, incident_id)
    return render_template(
        'incident_detail.html',
        incident=incident,
        severity_levels=Incident.SEVERITY_LEVELS,
        status_choices=Incident.STATUS_CHOICES,
        categories=Incident.CATEGORIES
    )


# -----------------------------------------------------------------------------
# EDIT INCIDENT
# -----------------------------------------------------------------------------
@main_bp.route('/incidents/<int:incident_id>/edit', methods=['GET', 'POST'])
def incident_edit(incident_id):
    """Update metadata for an existing incident."""
    incident = db.get_or_404(Incident, incident_id)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        severity = request.form.get('severity', incident.severity).strip()
        category = request.form.get('category', incident.category).strip()
        affected_system = request.form.get('affected_system', incident.affected_system).strip()
        reporter = request.form.get('reporter', incident.reporter).strip()
        editor = request.form.get('editor', 'SOC Analyst').strip()

        errors = []
        if not title:
            errors.append("Incident Title cannot be empty.")
        if not description:
            errors.append("Incident Description cannot be empty.")
        if not affected_system:
            errors.append("Affected System cannot be empty.")

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template(
                'incident_form.html',
                action='Edit',
                incident=incident,
                severity_levels=Incident.SEVERITY_LEVELS,
                status_choices=Incident.STATUS_CHOICES,
                categories=Incident.CATEGORIES,
                form_data=request.form
            )

        changes = []
        if incident.title != title:
            changes.append(f"Title changed to '{title}'")
        if incident.severity != severity:
            changes.append(f"Severity changed from '{incident.severity}' to '{severity}'")
        if incident.category != category:
            changes.append(f"Category changed from '{incident.category}' to '{category}'")
        if incident.affected_system != affected_system:
            changes.append(f"Affected system updated to '{affected_system}'")

        incident.title = title
        incident.description = description
        incident.severity = severity
        incident.category = category
        incident.affected_system = affected_system
        incident.reporter = reporter
        incident.updated_at = get_utc_now()

        if changes:
            audit = AuditLog(
                incident_id=incident.id,
                action='Incident Updated',
                details="; ".join(changes),
                performed_by=editor
            )
            db.session.add(audit)

        db.session.commit()
        current_app.logger.info(f"Incident {incident.incident_number} updated by {editor}")
        flash(f"Incident {incident.incident_number} updated successfully.", 'success')
        return redirect(url_for('main.incident_detail', incident_id=incident.id))

    return render_template(
        'incident_form.html',
        action='Edit',
        incident=incident,
        severity_levels=Incident.SEVERITY_LEVELS,
        status_choices=Incident.STATUS_CHOICES,
        categories=Incident.CATEGORIES,
        form_data={
            'title': incident.title,
            'description': incident.description,
            'severity': incident.severity,
            'category': incident.category,
            'affected_system': incident.affected_system,
            'reporter': incident.reporter,
            'assigned_to': incident.assigned_to,
            'status': incident.status
        }
    )


# -----------------------------------------------------------------------------
# UPDATE STATUS & LIFECYCLE
# -----------------------------------------------------------------------------
@main_bp.route('/incidents/<int:incident_id>/status', methods=['POST'])
def incident_update_status(incident_id):
    """Transition incident workflow status."""
    incident = db.get_or_404(Incident, incident_id)
    new_status = request.form.get('status', '').strip()
    analyst_name = request.form.get('analyst_name', 'SOC Analyst').strip()
    reason = request.form.get('reason', '').strip()

    if new_status not in Incident.STATUS_CHOICES:
        flash(f"Invalid status '{new_status}' requested.", 'danger')
        return redirect(url_for('main.incident_detail', incident_id=incident.id))

    old_status = incident.status
    if old_status != new_status:
        incident.status = new_status
        incident.updated_at = get_utc_now()

        if new_status in ['Resolved', 'Closed']:
            if not incident.resolved_at:
                incident.resolved_at = get_utc_now()
        else:
            incident.resolved_at = None

        log_details = f"Status transitioned from '{old_status}' to '{new_status}'."
        if reason:
            log_details += f" Reason: {reason}"

        audit = AuditLog(
            incident_id=incident.id,
            action='Status Transition',
            details=log_details,
            performed_by=analyst_name
        )
        db.session.add(audit)
        db.session.commit()

        current_app.logger.info(
            f"Incident [{incident.incident_number}] status changed from {old_status} to {new_status} by {analyst_name}"
        )
        flash(f"Incident status updated to '{new_status}'.", 'success')

    return redirect(url_for('main.incident_detail', incident_id=incident.id))


# -----------------------------------------------------------------------------
# ASSIGN INCIDENT
# -----------------------------------------------------------------------------
@main_bp.route('/incidents/<int:incident_id>/assign', methods=['POST'])
def incident_assign(incident_id):
    """Assign or reassign an incident to a team member or specialist."""
    incident = db.get_or_404(Incident, incident_id)
    new_assignee = request.form.get('assigned_to', '').strip()
    assigned_by = request.form.get('assigned_by', 'SOC Lead').strip()

    if not new_assignee:
        new_assignee = 'Unassigned'

    old_assignee = incident.assigned_to
    if old_assignee != new_assignee:
        incident.assigned_to = new_assignee
        incident.updated_at = get_utc_now()

        audit = AuditLog(
            incident_id=incident.id,
            action='Reassigned',
            details=f"Assigned from '{old_assignee}' to '{new_assignee}'.",
            performed_by=assigned_by
        )
        db.session.add(audit)
        db.session.commit()

        current_app.logger.info(
            f"Incident [{incident.incident_number}] reassigned to {new_assignee} by {assigned_by}"
        )
        flash(f"Assigned to {new_assignee}.", 'success')

    return redirect(url_for('main.incident_detail', incident_id=incident.id))


# -----------------------------------------------------------------------------
# ADD INVESTIGATION NOTE
# -----------------------------------------------------------------------------
@main_bp.route('/incidents/<int:incident_id>/notes', methods=['POST'])
def incident_add_note(incident_id):
    """Add an analyst investigation note to the incident dossier."""
    incident = Incident.query.get_or_404(incident_id)
    content = request.form.get('content', '').strip()
    author = request.form.get('author', 'SOC Analyst').strip()

    if not content:
        flash("Investigation note content cannot be empty.", 'danger')
        return redirect(url_for('main.incident_detail', incident_id=incident.id))

    note = InvestigationNote(
        incident_id=incident.id,
        author=author if author else 'SOC Analyst',
        content=content
    )
    incident.updated_at = get_utc_now()

    preview = content[:60] + '...' if len(content) > 60 else content
    audit = AuditLog(
        incident_id=incident.id,
        action='Note Added',
        details=f"Investigation note added by {author}: '{preview}'",
        performed_by=author
    )

    db.session.add(note)
    db.session.add(audit)
    db.session.commit()

    current_app.logger.info(f"Note added to [{incident.incident_number}] by {author}")
    flash("Investigation note recorded in case dossier.", 'success')
    return redirect(url_for('main.incident_detail', incident_id=incident.id))


# -----------------------------------------------------------------------------
# DELETE INCIDENT
# -----------------------------------------------------------------------------
@main_bp.route('/incidents/<int:incident_id>/delete', methods=['POST'])
def incident_delete(incident_id):
    """Delete an incident and all associated notes and audit logs."""
    incident = Incident.query.get_or_404(incident_id)
    inc_num = incident.incident_number
    title = incident.title
    deleted_by = request.form.get('deleted_by', 'Administrator').strip()

    current_app.logger.warning(
        f"Incident Deleted: [{inc_num}] '{title}' by {deleted_by}"
    )

    db.session.delete(incident)
    db.session.commit()

    flash(f"Incident {inc_num} and associated case logs deleted successfully.", 'info')
    return redirect(url_for('main.incidents_list'))


# -----------------------------------------------------------------------------
# EXPORT INCIDENTS (CSV)
# -----------------------------------------------------------------------------
@main_bp.route('/export/csv')
def export_csv():
    """Export current incident registry to CSV."""
    incidents = Incident.query.order_by(Incident.created_at.desc()).all()
    csv_data = export_incidents_to_csv(incidents)

    timestamp = get_utc_now().strftime('%Y%m%d_%H%M%S')
    filename = f"security_incidents_export_{timestamp}.csv"

    current_app.logger.info(f"Incident registry exported to CSV ({len(incidents)} records)")

    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename={filename}'}
    )


# -----------------------------------------------------------------------------
# DEVOPS HEALTH MONITORING ENDPOINT
# -----------------------------------------------------------------------------
@main_bp.route('/healthz')
def healthz():
    """
    Kubernetes / Docker health check probe.
    Tests DB connectivity and returns system status.
    """
    try:
        # Simple database ping
        db.session.execute(db.text('SELECT 1'))
        db_status = 'connected'
        status_code = 200
        overall_status = 'healthy'
    except Exception as e:
        current_app.logger.error(f"Healthcheck DB failure: {str(e)}")
        db_status = f'disconnected: {str(e)}'
        status_code = 503
        overall_status = 'unhealthy'

    payload = {
        'status': overall_status,
        'app_name': current_app.config.get('APP_NAME', 'Security Incident System'),
        'version': current_app.config.get('APP_VERSION', '1.0.0'),
        'environment': current_app.config.get('ENV_NAME', 'production'),
        'database': db_status,
        'total_incidents': Incident.query.count() if db_status == 'connected' else 0,
        'timestamp': get_utc_now().isoformat() + 'Z'
    }
    return jsonify(payload), status_code


# -----------------------------------------------------------------------------
# DASHBOARD REAL-TIME STATS API FOR CHARTS
# -----------------------------------------------------------------------------
@main_bp.route('/api/stats')

def api_stats():
    """Provides categorized telemetry for Chart.js frontend charts."""

    # Severity breakdown
    severity_data = {
        'Critical': Incident.query.filter_by(severity='Critical').count(),
        'High': Incident.query.filter_by(severity='High').count(),
        'Medium': Incident.query.filter_by(severity='Medium').count(),
        'Low': Incident.query.filter_by(severity='Low').count()
    }

    # Status breakdown
    status_data = {
        'Open': Incident.query.filter_by(status='Open').count(),
        'Investigating': Incident.query.filter_by(status='Investigating').count(),
        'Mitigated': Incident.query.filter_by(status='Mitigated').count(),
        'Resolved': Incident.query.filter_by(status='Resolved').count(),
        'Closed': Incident.query.filter_by(status='Closed').count()
    }

    # Category breakdown
    categories = Incident.CATEGORIES
    category_data = {}

    for cat in categories:
        count = Incident.query.filter_by(category=cat).count()
        if count > 0:
            category_data[cat] = count

    # 24-hour incident activity
    now = get_utc_now().replace(tzinfo=None)
    start_time = now - timedelta(hours=23)
    start_hour = start_time.replace(
        minute=0, second=0, microsecond=0
    )

    hourly_counts = [0] * 24

    incidents_last_24h = Incident.query.filter(
        Incident.created_at >= start_hour
    ).all()

    for incident in incidents_last_24h:
        hour_index = int(
            (
                incident.created_at.replace(
                    minute=0, second=0, microsecond=0
                ) - start_hour
            ).total_seconds() // 3600
        )

        if 0 <= hour_index < 24:
            hourly_counts[hour_index] += 1

    hourly_labels = [
        (start_hour + timedelta(hours=i)).strftime('%H:00')
        for i in range(24)
    ]

    # Return dashboard statistics
    return jsonify({
        'severity': severity_data,
        'status': status_data,
        'categories': category_data,
        'total': Incident.query.count(),
        'hourly': {
            'labels': hourly_labels,
            'counts': hourly_counts
        }
    })



# -----------------------------------------------------------------------------
# SEED DEMO DATA TRIGGER (DEV/COLLEGE PRESENTATION AID)
# -----------------------------------------------------------------------------
@main_bp.route('/demo/seed', methods=['POST'])
def demo_seed():
    """Utility endpoint to seed sample data for presentations."""
    count = seed_sample_incidents(db, force=True)
    flash(f"Demo environment populated with {count} realistic cybersecurity incidents.", 'success')
    return redirect(url_for('main.dashboard'))
