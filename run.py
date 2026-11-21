import os
from app import create_app
from app.models import db, Incident
from app.utils import seed_sample_incidents

# Instantiate Flask application
env_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(env_name)

# Ensure database tables exist and optionally seed sample data on first start
with app.app_context():
    db.create_all()
    if Incident.query.count() == 0:
        count = seed_sample_incidents(db)
        app.logger.info(f"Initialized database with {count} sample cybersecurity incidents.")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    app.logger.info(f"Starting SOC Incident Management System on http://{host}:{port}")
    app.run(host=host, port=port, debug=(env_name == 'development'))
