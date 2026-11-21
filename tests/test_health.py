def test_healthz_endpoint_healthy(client):
    """Test DevOps health check endpoint returns 200 OK and healthy status."""
    response = client.get('/healthz')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['database'] == 'connected'
    assert 'app_name' in data
    assert 'version' in data
    assert 'timestamp' in data


def test_404_json_error(client):
    """Test API requests for non-existent routes return JSON 404."""
    response = client.get('/api/does-not-exist', headers={'Accept': 'application/json'})
    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == 'Resource not found'
    assert data['status_code'] == 404
