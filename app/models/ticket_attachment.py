from datetime import datetime
import os
from app import db


class TicketAttachment(db.Model):
    __tablename__ = 'ticket_attachments'

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id', ondelete='CASCADE'), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False, unique=True)
    content_type = db.Column(db.String(100))
    size_bytes = db.Column(db.Integer)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    uploaded_by = db.relationship('User')

    def file_path(self, app_config):
        return os.path.join(app_config['ATTACHMENTS_FOLDER'], self.stored_filename)

    def __repr__(self):
        return f'<TicketAttachment {self.filename} (ticket {self.ticket_id})>'

