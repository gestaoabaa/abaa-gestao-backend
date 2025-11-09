from src.models.user import db
from datetime import datetime

# Tabela de associação entre Student e DanceClass
student_classes = db.Table('student_classes',
    db.Column('student_id', db.String(36), db.ForeignKey('student.id'), primary_key=True),
    db.Column('class_id', db.String(36), db.ForeignKey('dance_class.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

# Adicionando o relacionamento many-to-many aos modelos existentes
# Isso será importado nos modelos Student e DanceClass para estabelecer a relação

