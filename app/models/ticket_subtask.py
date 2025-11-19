from datetime import datetime
from app import db


class TicketSubtask(db.Model):
    __tablename__ = 'ticket_subtasks'

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    is_done = db.Column(db.Boolean, default=False, nullable=False)
    position = db.Column(db.Integer, default=0, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime)

    def mark_done(self):
        self.is_done = True
        self.completed_at = datetime.utcnow()

    def mark_undone(self):
        self.is_done = False
        self.completed_at = None

    def __repr__(self):
        return f'<TicketSubtask {self.title} (ticket {self.ticket_id})>'

