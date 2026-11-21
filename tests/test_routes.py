from app.models import db, Incident


def test_dashboard_page(client, sample_incident):
    """Test SOC executive dashboard loads successfully with stats."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Security Operations Center' in response.data
    assert b'Total Recorded' in response.data
    assert b'INC-TEST-0001' in response.data


def test_incidents_list(client, sample_incident):
    """Test incident registry list page loads."""
    response = client.get('/incidents')
    assert response.status_code == 200
    assert b'Incident Management Registry' in response.data
    assert b'INC-TEST-0001' in response.data


def test_create_incident_success(client):
    """Test creating a new security incident via POST form."""
    form_data = {
        'title': 'DDoS Flooding on DNS Resolver',
        'description': 'UDP amplification attack observed exceeding 50 Gbps.',
        'severity': 'Critical',
        'category': 'DDoS Attack',
        'affected_system': 'ns1.corp.dns',
        'reporter': 'NetOps Sentinel',
        'assigned_to': 'Alex Chen',
        'status': 'Open'
    }
    response = client.post('/incidents/new', data=form_data, follow_redirects=True)
    assert response.status_code == 200
    assert b'DDoS Flooding on DNS Resolver' in response.data
    assert b'reported successfully' in response.data


def test_create_incident_validation_failure(client):
    """Test validation errors when required fields are missing."""
    invalid_data = {
        'title': '',  # missing title
        'description': '',
        'affected_system': ''
    }
    response = client.post('/incidents/new', data=invalid_data, follow_redirects=True)
    assert response.status_code == 200
    assert b'Incident Title is required' in response.data
    assert b'Incident Description is required' in response.data


def test_incident_detail(client, sample_incident):
    """Test viewing a specific incident dossier."""
    response = client.get(f'/incidents/{sample_incident.id}')
    assert response.status_code == 200
    assert b'Case Dossier Overview' in response.data
    assert sample_incident.title.encode() in response.data
    assert b'Initial IP blocked on firewall' in response.data  # Note content


def test_incident_detail_not_found(client):
    """Test requesting a non-existent incident triggers 404."""
    response = client.get('/incidents/99999')
    assert response.status_code == 404
    assert b'404' in response.data


def test_update_incident_status(client, sample_incident):
    """Test transitioning workflow status and recording audit trail."""
    response = client.post(
        f'/incidents/{sample_incident.id}/status',
        data={'status': 'Investigating', 'analyst_name': 'Sarah SOC Lead', 'reason': 'Investigating telemetry'},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Incident status updated" in response.data
    assert b"Investigating" in response.data

    # Verify transition in DB
    updated = db.session.get(Incident, sample_incident.id)
    assert updated.status == 'Investigating'

    # Check status changed to Resolved sets resolved_at
    response2 = client.post(
        f'/incidents/{sample_incident.id}/status',
        data={'status': 'Resolved', 'analyst_name': 'Sarah SOC Lead'},
        follow_redirects=True
    )
    assert response2.status_code == 200
    db.session.refresh(updated)
    assert updated.status == 'Resolved'
    assert updated.resolved_at is not None


def test_assign_incident(client, sample_incident):
    """Test reassigning an incident to an analyst."""
    response = client.post(
        f'/incidents/{sample_incident.id}/assign',
        data={'assigned_to': 'Elena Rostova', 'assigned_by': 'SOC Lead'},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'Assigned to Elena Rostova' in response.data

    updated = db.session.get(Incident, sample_incident.id)
    assert updated.assigned_to == 'Elena Rostova'


def test_add_investigation_note(client, sample_incident):
    """Test adding an analyst note to the case dossier."""
    response = client.post(
        f'/incidents/{sample_incident.id}/notes',
        data={'author': 'Incident Responder Mike', 'content': 'Memory capture completed. Sent to sandbox.'},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'Investigation note recorded in case dossier' in response.data
    assert b'Memory capture completed' in response.data


def test_edit_incident(client, sample_incident):
    """Test editing incident metadata."""
    update_data = {
        'title': 'Updated Title for Gateway Compromise',
        'description': 'Updated description with new indicators.',
        'severity': 'High',
        'category': 'Malware',
        'affected_system': 'gateway-cluster-updated',
        'reporter': 'Updated Reporter',
        'editor': 'SOC Manager'
    }
    response = client.post(
        f'/incidents/{sample_incident.id}/edit',
        data=update_data,
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'updated successfully' in response.data

    updated = db.session.get(Incident, sample_incident.id)
    assert updated.title == 'Updated Title for Gateway Compromise'
    assert updated.severity == 'High'


def test_delete_incident(client, sample_incident):
    """Test deleting an incident case."""
    inc_id = sample_incident.id
    response = client.post(
        f'/incidents/{inc_id}/delete',
        data={'deleted_by': 'Admin'},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'deleted successfully' in response.data

    assert db.session.get(Incident, inc_id) is None


def test_search_and_filter(client, sample_incident):
    """Test search queries and filters on incidents list."""
    # Search by keyword
    res1 = client.get('/incidents?q=Unauthorized')
    assert res1.status_code == 200
    assert b'INC-TEST-0001' in res1.data

    # Search with no match
    res2 = client.get('/incidents?q=NonExistentQueryXYZ')
    assert res2.status_code == 200
    assert b'No Incidents Found' in res2.data

    # Filter by severity
    res3 = client.get('/incidents?severity=Critical')
    assert res3.status_code == 200
    assert b'INC-TEST-0001' in res3.data


def test_export_csv(client, sample_incident):
    """Test CSV export route returns proper headers and content."""
    response = client.get('/export/csv')
    assert response.status_code == 200
    assert response.mimetype == 'text/csv'
    assert 'attachment;filename=security_incidents_export_' in response.headers.get('Content-Disposition')
    assert b'Incident ID,Case Number,Title' in response.data
    assert b'INC-TEST-0001' in response.data


def test_api_stats(client, sample_incident):
    """Test telemetry API endpoint for Chart.js."""
    response = client.get('/api/stats')
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'severity' in json_data
    assert 'status' in json_data
    assert 'categories' in json_data
    assert json_data['severity']['Critical'] >= 1
