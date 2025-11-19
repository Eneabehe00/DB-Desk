from datetime import datetime
from app import db


class EmailDraft(db.Model):
    __tablename__ = 'email_drafts'

    id = db.Column(db.Integer, primary_key=True)
    imap_uid = db.Column(db.String(128), nullable=False, unique=True, index=True)
    message_id = db.Column(db.String(255))
    from_email = db.Column(db.String(255))
    subject = db.Column(db.String(500))
    body = db.Column(db.Text)
    received_at = db.Column(db.DateTime)
    processed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Status: 'pending', 'converted', 'ignored'
    status = db.Column(db.String(20), default='pending', nullable=False)
    converted_ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id', ondelete='SET NULL'))
    notes = db.Column(db.Text)  # Note dell'operatore
    
    converted_ticket = db.relationship('Ticket')

    def __repr__(self):
        return f'<EmailDraft UID={self.imap_uid} from={self.from_email}>'

    def to_dict(self):
        return {
            'id': self.id,
            'from_email': self.from_email,
            'subject': self.subject,
            'body': self.body[:200] + '...' if self.body and len(self.body) > 200 else self.body,
            'received_at': self.received_at.isoformat() if self.received_at else None,
            'status': self.status,
            'converted_ticket_id': self.converted_ticket_id
        }
