from src.models.user import db
from datetime import datetime
import uuid

class PrivateClassCombo(db.Model):
    __tablename__ = 'private_class_combo'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    num_classes = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<PrivateClassCombo {self.num_classes} classes - R${self.price}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'num_classes': self.num_classes,
            'price': float(self.price) if self.price else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

