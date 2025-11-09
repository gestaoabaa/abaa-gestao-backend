from flask import Blueprint, request, jsonify
from src.models import db, Student, DanceClass, Payment, User
from sqlalchemy import func

admin_bp = Blueprint("admin_bp", __name__)

@admin_bp.route("/admin/dashboard", methods=["GET"])
def get_admin_dashboard_data():
    """Obter dados do dashboard administrativo (visão geral de todos os professores)"""
    try:
        # Verificar se o usuário é admin (isso seria feito com autenticação real)
        # Por enquanto, vamos assumir que a rota só é acessada por admins

        total_students = Student.query.count()
        total_classes = DanceClass.query.count()
        total_teachers = User.query.filter_by(role='teacher').count()
        total_admins = User.query.filter_by(role='admin').count()  # Corrigido aspas e indentação
        total_revenue = db.session.query(func.sum(Payment.amount)).scalar() or 0

        # Alunos com pagamentos vencidos (todos os professores)
        overdue_students_count = Student.query.filter(
            Student.payment_due_date < datetime.now().date(),
            Student.scholarship_percentage < 100
        ).count()

        # Alunos com pagamentos próximos do vencimento (todos os professores)
        due_soon_students_count = Student.query.filter(
            Student.payment_due_date >= datetime.now().date(),
            Student.payment_due_date <= datetime.now().date() + timedelta(days=7),
            Student.scholarship_percentage < 100
        ).count()

        return jsonify({
            "statistics": {
                "total_students": total_students,
                "total_classes": total_classes,
                "total_teachers": total_teachers,
                "total_admins": total_admins,
                "total_revenue": float(total_revenue),
                "overdue_students_count": overdue_students_count,
                "due_soon_students_count": due_soon_students_count
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/admin/teachers", methods=["GET"])
def get_all_teachers():
    """Listar todos os professores"""
    try:
        teachers = User.query.filter_by(role='teacher').all()
        return jsonify([teacher.to_dict() for teacher in teachers])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/admin/students", methods=["GET"])
def get_all_students():
    """Listar todos os alunos (para admin)"""
    try:
        students = Student.query.all()
        return jsonify([student.to_dict() for student in students])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/admin/classes", methods=["GET"])
def get_all_classes():
    """Listar todas as turmas (para admin)"""
    try:
        classes = DanceClass.query.all()
        return jsonify([cls.to_dict() for cls in classes])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/admin/payments", methods=["GET"])
def get_all_payments():
    """Listar todos os pagamentos (para admin)"""
    try:
        payments = Payment.query.all()
        return jsonify([payment.to_dict() for payment in payments])
    except Exception as e:
        return jsonify({"error": str(e)}), 500



