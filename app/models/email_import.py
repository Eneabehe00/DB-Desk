from datetime import datetime
from app import db


class EmailImportLog(db.Model):
    __tablename__ = 'email_import_log'

    id = db.Column(db.Integer, primary_key=True)
    imap_uid = db.Column(db.String(128), nullable=False, unique=True, index=True)
    message_id = db.Column(db.String(255))
    from_email = db.Column(db.String(255))
    subject = db.Column(db.String(500))
    created_ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id', ondelete='SET NULL'))
    received_at = db.Column(db.DateTime)
    processed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    created_ticket = db.relationship('Ticket')

    def __repr__(self):
        return f'<EmailImportLog UID={self.imap_uid} ticket={self.created_ticket_id}>'

