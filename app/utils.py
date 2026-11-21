import csv
import io
import datetime
from app.models import Incident, InvestigationNote, AuditLog, get_utc_now


def generate_incident_number():
    """Generates a human-friendly unique incident case number like INC-2026-0104."""
    year = get_utc_now().year
    count = Incident.query.count() + 1
    # Check uniqueness
    inc_num = f"INC-{year}-{count:04d}"
    # Safety loop if collision exists
    while Incident.query.filter_by(incident_number=inc_num).first() is not None:
        count += 1
        inc_num = f"INC-{year}-{count:04d}"
    return inc_num


def export_incidents_to_csv(incidents):
    """Exports list of incidents to CSV format."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        'Incident ID',
        'Case Number',
        'Title',
        'Category',
        'Severity',
        'Status',
        'Affected System',
        'Reporter',
        'Assigned To',
        'Created At',
        'Updated At',
        'Resolved At',
        'Notes Count'
    ])

    for inc in incidents:
        writer.writerow([
            inc.id,
            inc.incident_number,
            inc.title,
            inc.category,
            inc.severity,
            inc.status,
            inc.affected_system,
            inc.reporter,
            inc.assigned_to,
            inc.created_at.strftime('%Y-%m-%d %H:%M:%S') if inc.created_at else '',
            inc.updated_at.strftime('%Y-%m-%d %H:%M:%S') if inc.updated_at else '',
            inc.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if inc.resolved_at else '',
            len(inc.notes)
        ])

    return output.getvalue()


def seed_sample_incidents(db, force=False):
    """Populates database with realistic cybersecurity incident cases for demonstration."""
    if not force and Incident.query.count() > 0:
        return 0

    now = get_utc_now()

    samples = [
        {
            "incident_number": f"INC-{now.year}-0001",
            "title": "Credential Stuffing Attack Detected on Auth Gateway",
            "description": (
                "SOC SIEM alert: Over 45,000 failed auth requests originating from known Tor exit "
                "nodes targeting customer SSO portal within 10 minutes."
            ),
            "category": "Unauthorized Access",
            "severity": "Critical",
            "status": "Investigating",
            "affected_system": "auth-gateway-cluster.prod",
            "reporter": "SIEM Sentinel Sensor",
            "assigned_to": "Alex Chen (SOC Tier 2)",
            "created_at": now - datetime.timedelta(hours=6),
            "updated_at": now - datetime.timedelta(hours=2),
            "notes": [
                ("Alex Chen", "Firewall IP rate-limiting applied. Blocked offending /16 subnet."),
                ("Sarah Jenkins", "14 accounts locked due to spray attempt. Users notified to reset credentials.")
            ],
            "audit": [
                ("Incident Created", "Automated alert received from Splunk/Wazuh rule #7802.", "SIEM Sentinel Sensor"),
                ("Severity Set", "Assigned Critical due to production gateway impact.", "SIEM Sentinel Sensor"),
                ("Assigned", "Incident assigned to Alex Chen.", "SOC Lead"),
                ("Status Changed", "Status updated from Open to Investigating.", "Alex Chen (SOC Tier 2)")
            ]
        },
        {
            "incident_number": f"INC-{now.year}-0002",
            "title": "Spear Phishing Email Campaign with Macro-Enabled Attachment",
            "description": (
                "Multiple employees reported suspicious emails disguised as vendor invoices containing an "
                "obfuscated PowerShell macro (.xlsm attachment)."
            ),
            "category": "Phishing",
            "severity": "High",
            "status": "Mitigated",
            "affected_system": "corp-mail-exchange.internal",
            "reporter": "Finance AP Team",
            "assigned_to": "Elena Rostova (Incident Responder)",
            "created_at": now - datetime.timedelta(hours=18),
            "updated_at": now - datetime.timedelta(hours=4),
            "notes": [
                ("Elena Rostova", "SHA256: 3a7b...4e1 extracted. 48/70 VirusTotal vendors flag Emotet dropper."),
                ("Elena Rostova", "Purged 34 matching emails from mailboxes. Two compromised laptops quarantined.")
            ],
            "audit": [
                ("Incident Created", "User reported via Outlook PhishAlarm plugin.", "Finance AP Team"),
                ("Status Changed", "Status updated from Open to Investigating.", "Elena Rostova"),
                ("Status Changed", "Status updated from Investigating to Mitigated.", "Elena Rostova")
            ]
        },
        {
            "incident_number": f"INC-{now.year}-0003",
            "title": "Ransomware Binary Flagged by EDR on File Server FS-02",
            "description": (
                "EDR detected and killed unknown binary attempting to modify shadow copies and "
                "enumerate shared volumes on Windows File Server FS-02."
            ),
            "category": "Ransomware",
            "severity": "Critical",
            "status": "Resolved",
            "affected_system": "fs-02.corp.local",
            "reporter": "EDR Falcon Sensor",
            "assigned_to": "Marcus Vance (Senior SecOps)",
            "created_at": now - datetime.timedelta(days=2),
            "updated_at": now - datetime.timedelta(hours=12),
            "resolved_at": now - datetime.timedelta(hours=12),
            "notes": [
                ("Marcus Vance", "Host network-isolated immediately by EDR policy."),
                ("Marcus Vance", "Memory dump analyzed. Lateral movement attempted via SMBv1 exploit."),
                ("Marcus Vance", "File system intact, no encrypted files. Backups healthy. Host restored.")
            ],
            "audit": [
                ("Incident Created", "High severity automated detection from CrowdStrike.", "EDR Falcon Sensor"),
                ("Assigned", "Assigned to Marcus Vance.", "SOC Lead"),
                ("Status Changed", "Status transitioned to Investigating.", "Marcus Vance"),
                ("Status Changed", "Status transitioned to Resolved. Post-incident report filed.", "Marcus Vance")
            ]
        },
        {
            "incident_number": f"INC-{now.year}-0004",
            "title": "Layer 7 HTTP Flood against Public REST API",
            "description": (
                "Cloudflare alerted on 350,000 req/sec spike targeting /api/v1/search endpoint, causing "
                "504 gateway timeouts for mobile app users."
            ),
            "category": "DDoS Attack",
            "severity": "High",
            "status": "Resolved",
            "affected_system": "api.production.internal",
            "reporter": "Datadog APM Monitor",
            "assigned_to": "DevOps OnCall (Devin Patel)",
            "created_at": now - datetime.timedelta(days=3),
            "updated_at": now - datetime.timedelta(days=2),
            "resolved_at": now - datetime.timedelta(days=2),
            "notes": [
                ("Devin Patel", "Cloudflare 'Under Attack' mode enabled. Challenge-passage rule deployed."),
                ("Devin Patel", "Upstream origin CPU returned to normal (18%). Rate limits codified in Terraform.")
            ],
            "audit": [
                ("Incident Created", "Automated alert from Datadog APM.", "Datadog APM Monitor"),
                ("Status Changed", "Status changed to Investigating.", "Devin Patel"),
                ("Status Changed", "Status changed to Resolved.", "Devin Patel")
            ]
        },
        {
            "incident_number": f"INC-{now.year}-0005",
            "title": "S3 Cloud Bucket Accidentally Configured with Public Read",
            "description": (
                "Cloud Custodian compliance scanner flagged AWS S3 bucket 'finance-archive-raw-2025' "
                "with Public Read ACL containing vendor contracts."
            ),
            "category": "Policy Violation",
            "severity": "Medium",
            "status": "Resolved",
            "affected_system": "aws-s3-finance-archive",
            "reporter": "Cloud Custodian Bot",
            "assigned_to": "Cloud Sec Team",
            "created_at": now - datetime.timedelta(days=4),
            "updated_at": now - datetime.timedelta(days=4),
            "resolved_at": now - datetime.timedelta(days=4),
            "notes": [
                ("Cloud Sec Team", "Applied S3 Public Access Block at account level."),
                ("Cloud Sec Team", "CloudTrail access logs checked; zero unauthorized external GET requests recorded.")
            ],
            "audit": [
                ("Incident Created", "Automated finding from IAM posture scanner.", "Cloud Custodian Bot"),
                ("Status Changed", "Status changed to Resolved after remediation.", "Cloud Sec Team")
            ]
        },
        {
            "incident_number": f"INC-{now.year}-0006",
            "title": "Suspicious Privilege Escalation on Kubernetes Worker Node",
            "description": (
                "Falco runtime security daemon detected unexpected sudo execution and namespace escape "
                "attempt inside pod 'payment-worker-7b9f8'."
            ),
            "category": "Privilege Escalation",
            "severity": "High",
            "status": "Investigating",
            "affected_system": "k8s-prod-cluster-worker-04",
            "reporter": "Falco Runtime Monitor",
            "assigned_to": "Sarah Jenkins (SOC Lead)",
            "created_at": now - datetime.timedelta(hours=14),
            "updated_at": now - datetime.timedelta(hours=1),
            "notes": [
                ("Sarah Jenkins", "Terminated suspicious pod. Extracted container filesystem diff for forensic review."),
                ("Sarah Jenkins", "Suspected container breakout attempt using CVE-2024-21626.")
            ],
            "audit": [
                ("Incident Created", "Alert rule: 'Notice: Sudo or namespace manipulation in container'.", "Falco"),
                ("Assigned", "Assigned to Sarah Jenkins.", "SOC Lead"),
                ("Status Changed", "Status transitioned to Investigating.", "Sarah Jenkins")
            ]
        },
        {
            "incident_number": f"INC-{now.year}-0007",
            "title": "Suspected Rogue Wi-Fi Access Point in Building B",
            "description": (
                "WIPS detected an SSID broadcasting 'Corp-Guest-Secure' not registered in "
                "Cisco Meraki wireless controller."
            ),
            "category": "Unauthorized Access",
            "severity": "Low",
            "status": "Open",
            "affected_system": "bldg-b-wifi-infrastructure",
            "reporter": "Network Operations Center",
            "assigned_to": "Unassigned",
            "created_at": now - datetime.timedelta(hours=5),
            "updated_at": now - datetime.timedelta(hours=5),
            "notes": [],
            "audit": [
                ("Incident Created", "Dispatched physical sweep request to Floor 3 Facilities.", "NOC")
            ]
        },
        {
            "incident_number": f"INC-{now.year}-0008",
            "title": "SQL Injection Probe Attempt on Marketing Web Portal",
            "description": (
                "WAF blocked multiple automated SQL injection payload patterns (' UNION SELECT ..., 1=1 --) "
                "targeting /contact-us form."
            ),
            "category": "Vulnerability Exploit",
            "severity": "Low",
            "status": "Closed",
            "affected_system": "web-marketing.acme.org",
            "reporter": "ModSecurity WAF",
            "assigned_to": "Alex Chen (SOC Tier 2)",
            "created_at": now - datetime.timedelta(days=7),
            "updated_at": now - datetime.timedelta(days=6),
            "resolved_at": now - datetime.timedelta(days=6),
            "notes": [
                ("Alex Chen", "WAF rejected 1,200 payloads with 403. Input uses parameterized ORM; no vulnerability.")
            ],
            "audit": [
                ("Incident Created", "Automated WAF aggregated alert.", "ModSecurity WAF"),
                ("Status Changed", "Status changed to Closed.", "Alex Chen")
            ]
        }
    ]

    count = 0
    for s in samples:
        inc = Incident(
            incident_number=s["incident_number"],
            title=s["title"],
            description=s["description"],
            category=s["category"],
            severity=s["severity"],
            status=s["status"],
            affected_system=s["affected_system"],
            reporter=s["reporter"],
            assigned_to=s["assigned_to"],
            created_at=s["created_at"],
            updated_at=s["updated_at"],
            resolved_at=s.get("resolved_at")
        )
        db.session.add(inc)
        db.session.flush()

        for author, note_text in s["notes"]:
            note = InvestigationNote(
                incident_id=inc.id,
                author=author,
                content=note_text,
                created_at=s["updated_at"]
            )
            db.session.add(note)

        for action, details, performed_by in s["audit"]:
            audit = AuditLog(
                incident_id=inc.id,
                action=action,
                details=details,
                performed_by=performed_by,
                timestamp=s["created_at"]
            )
            db.session.add(audit)

        count += 1

    db.session.commit()
    return count
