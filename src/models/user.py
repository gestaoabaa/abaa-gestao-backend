from ..main import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    profile_pic = db.Column(db.String(200), nullable=True)
    role = db.Column(db.String(20), default="teacher") # "teacher" ou "admin"

    def to_dict(self):
        return {
            "id": self.id,
            "google_id": self.google_id,
            "name": self.name,
            "email": self.email,
            "profile_pic": self.profile_pic,
            "role": self.role
        }
