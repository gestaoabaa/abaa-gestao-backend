from flask import Blueprint, request, jsonify
from src.models import db, Attendance, Student, DanceClass
from datetime import datetime, date
from sqlalchemy import func

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/attendance', methods=['GET'])
def get_attendance():
    """Listar registros de presença"""
    try:
        class_id = request.args.get('class_id')
        student_id = request.args.get('student_id')
        date_str = request.args.get('date')
        
        # Base query
        query = Attendance.query
        
        # Filtros opcionais
        if class_id:
            query = query.filter(Attendance.class_id == class_id)
        if student_id:
            query = query.filter(Attendance.student_id == student_id)
        if date_str:
            attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            query = query.filter(Attendance.date == attendance_date)
        
        attendance_records = query.all()
        return jsonify([record.to_dict() for record in attendance_records])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/attendance', methods=['POST'])
def create_attendance():
    """Registrar presença de um aluno"""
    try:
        data = request.get_json()
        
        # Validação dos dados obrigatórios
        required_fields = ['student_id', 'class_id', 'date', 'is_present']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} é obrigatório'}), 400
        
        # Converter string de data para objeto date
        attendance_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        
        # Verificar se já existe registro para este aluno, turma e data
        existing = Attendance.query.filter_by(
            student_id=data['student_id'],
            class_id=data['class_id'],
            date=attendance_date
        ).first()
        
        if existing:
            # Atualizar registro existente
            existing.is_present = data['is_present']
            existing.updated_at = datetime.utcnow()
            db.session.commit()
            return jsonify(existing.to_dict())
        else:
            # Criar novo registro
            attendance = Attendance(
                student_id=data['student_id'],
                class_id=data['class_id'],
                date=attendance_date,
                is_present=data['is_present']
            )
            
            db.session.add(attendance)
            db.session.commit()
            
            return jsonify(attendance.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/attendance/class/<class_id>/date/<date_str>', methods=['GET'])
def get_class_attendance_by_date(class_id, date_str):
    """Obter lista de chamada de uma turma para uma data específica"""
    try:
        attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Obter todos os alunos da turma
        dance_class = DanceClass.query.get_or_404(class_id)
        students = dance_class.students.all()
        
        # Obter registros de presença para esta data
        attendance_records = Attendance.query.filter_by(
            class_id=class_id,
            date=attendance_date
        ).all()
        
        # Criar dicionário de presença por aluno
        attendance_dict = {record.student_id: record.is_present for record in attendance_records}
        
        # Montar resposta com todos os alunos e seu status de presença
        result = []
        for student in students:
            result.append({
                'student': student.to_dict(),
                'is_present': attendance_dict.get(student.id, None)  # None se não foi registrado
            })
        
        return jsonify({
            'class': dance_class.to_dict(),
            'date': date_str,
            'attendance': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/attendance/class/<class_id>/bulk', methods=['POST'])
def bulk_create_attendance(class_id):
    """Registrar presença em lote para uma turma"""
    try:
        data = request.get_json()
        
        # Validação dos dados obrigatórios
        if 'date' not in data or 'attendance' not in data:
            return jsonify({'error': 'date e attendance são obrigatórios'}), 400
        
        attendance_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        attendance_list = data['attendance']  # Lista de {student_id, is_present}
        
        results = []
        for item in attendance_list:
            student_id = item.get('student_id')
            is_present = item.get('is_present')
            
            if not student_id or is_present is None:
                continue
            
            # Verificar se já existe registro
            existing = Attendance.query.filter_by(
                student_id=student_id,
                class_id=class_id,
                date=attendance_date
            ).first()
            
            if existing:
                existing.is_present = is_present
                existing.updated_at = datetime.utcnow()
                results.append(existing.to_dict())
            else:
                attendance = Attendance(
                    student_id=student_id,
                    class_id=class_id,
                    date=attendance_date,
                    is_present=is_present
                )
                db.session.add(attendance)
                results.append(attendance.to_dict())
        
        db.session.commit()
        return jsonify(results), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/attendance/student/<student_id>/stats', methods=['GET'])
def get_student_attendance_stats(student_id):
    """Obter estatísticas de presença de um aluno"""
    try:
        # Contar presenças e faltas
        total_records = Attendance.query.filter_by(student_id=student_id).count()
        present_count = Attendance.query.filter_by(student_id=student_id, is_present=True).count()
        absent_count = total_records - present_count
        
        attendance_rate = (present_count / total_records * 100) if total_records > 0 else 0
        
        return jsonify({
            'student_id': student_id,
            'total_classes': total_records,
            'present_count': present_count,
            'absent_count': absent_count,
            'attendance_rate': round(attendance_rate, 2)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/attendance/class/<class_id>/stats', methods=['GET'])
def get_class_attendance_stats(class_id):
    """Obter estatísticas de presença de uma turma"""
    try:
        # Estatísticas por semana (últimas 4 semanas)
        from datetime import timedelta
        
        today = date.today()
        weeks_data = []
        
        for i in range(4):
            week_start = today - timedelta(days=today.weekday() + (i * 7))
            week_end = week_start + timedelta(days=6)
            
            week_attendance = Attendance.query.filter(
                Attendance.class_id == class_id,
                Attendance.date >= week_start,
                Attendance.date <= week_end
            ).all()
            
            total_week = len(week_attendance)
            present_week = sum(1 for a in week_attendance if a.is_present)
            
            weeks_data.append({
                'week_start': week_start.isoformat(),
                'week_end': week_end.isoformat(),
                'total_classes': total_week,
                'present_count': present_week,
                'attendance_rate': round((present_week / total_week * 100) if total_week > 0 else 0, 2)
            })
        
        return jsonify({
            'class_id': class_id,
            'weekly_stats': weeks_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

