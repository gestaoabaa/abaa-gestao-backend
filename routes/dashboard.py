from flask import Blueprint, request, jsonify
from src.models import db, Student, DanceClass, Payment, Attendance, User
from datetime import datetime, date, timedelta
from sqlalchemy import func

dashboard_bp = Blueprint("dashboard", __name__)

# Helper para obter o user_id (temporário, será substituído pela autenticação real)
def get_current_user_id():
    # TODO: Implementar autenticação real e obter o user_id do usuário logado
    # Por enquanto, para testes, podemos usar um user_id fixo ou passar via header/query param
    # Exemplo: return request.headers.get("X-User-ID", "some_default_user_id")
    return request.args.get("user_id") # Mantendo como query param por enquanto para compatibilidade

@dashboard_bp.route("/dashboard", methods=["GET"])
def get_dashboard_data():
    """Obter dados do dashboard para o usuário logado ou dados gerais para admin"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"error": "user_id é obrigatório"}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "Usuário não encontrado"}), 404

        today = date.today()
        
        if user.role == "admin":
            # Dados para o dashboard do administrador (visão geral)
            total_students = Student.query.count()
            total_classes = DanceClass.query.count()
            total_teachers = User.query.filter_by(role="teacher").count()
            total_admins = User.query.filter_by(role="admin").count()

            # Receita total (todos os pagamentos)
            total_revenue = db.session.query(func.sum(Payment.amount)).scalar() or 0

            # Alunos com pagamentos vencidos (todos os professores)
            overdue_students_count = Student.query.filter(
                Student.payment_due_date < today,
                Student.scholarship_percentage < 100
            ).count()

            # Alunos com pagamentos próximos do vencimento (todos os professores)
            due_soon_students_count = Student.query.filter(
                Student.payment_due_date >= today,
                Student.payment_due_date <= today + timedelta(days=7),
                Student.scholarship_percentage < 100
            ).count()

            return jsonify({
                "role": "admin",
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
        else:
            # Dados para o dashboard do professor (filtrado por user_id)
            next_week = today + timedelta(days=7)
            upcoming_classes = DanceClass.query.filter_by(user_id=user_id).all()
            
            # Pagamentos vencidos (excluindo bolsistas integrais)
            overdue_students = Student.query.filter(
                Student.user_id == user_id,
                Student.payment_due_date < today,
                Student.scholarship_percentage < 100  # Não incluir bolsistas integrais
            ).all()
            
            # Pagamentos próximos do vencimento (próximos 7 dias, excluindo bolsistas integrais)
            due_soon_students = Student.query.filter(
                Student.user_id == user_id,
                Student.payment_due_date >= today,
                Student.payment_due_date <= next_week,
                Student.scholarship_percentage < 100  # Não incluir bolsistas integrais
            ).all()
            
            # Atividade recente (últimos 10 pagamentos)
            recent_payments = Payment.query.join(Student).filter(
                Student.user_id == user_id
            ).order_by(Payment.created_at.desc()).limit(10).all()
            
            # Estatísticas gerais
            total_students = Student.query.filter_by(user_id=user_id).count()
            total_classes = DanceClass.query.filter_by(user_id=user_id).count()
            
            # Receita do mês atual
            current_month_start = today.replace(day=1)
            monthly_revenue = db.session.query(func.sum(Payment.amount)).join(Student).filter(
                Student.user_id == user_id,
                Payment.payment_date >= current_month_start,
                Payment.payment_date <= today
            ).scalar() or 0
            
            return jsonify({
                "role": "teacher",
                "upcoming_classes": [cls.to_dict() for cls in upcoming_classes],
                "payment_notifications": {
                    "overdue": [{
                        "student": student.to_dict(),
                        "days_overdue": (today - student.payment_due_date).days
                    } for student in overdue_students],
                    "due_soon": [{
                        "student": student.to_dict(),
                        "days_until_due": (student.payment_due_date - today).days
                    } for student in due_soon_students]
                },
                "recent_activity": [payment.to_dict() for payment in recent_payments],
                "statistics": {
                    "total_students": total_students,
                    "total_classes": total_classes,
                    "monthly_revenue": float(monthly_revenue),
                    "overdue_count": len(overdue_students),
                    "due_soon_count": len(due_soon_students)
                }
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500



