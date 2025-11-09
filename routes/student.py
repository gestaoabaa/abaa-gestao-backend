from flask import Blueprint, request, jsonify, send_file
from ..models.student import Student
from ..models.user import db, User
from ..utils.auth import require_auth, filter_by_user_access, can_access_student
from flask import g
from openpyxl import Workbook
from io import BytesIO
from datetime import datetime

student_bp = Blueprint("student_bp", __name__)

@student_bp.route("/students", methods=["GET"])
@require_auth
def get_students():
    """Listar todos os alunos do usuário logado (ou todos se for admin)"""
    try:
        query = Student.query
        filtered_query = filter_by_user_access(query, Student, g.current_user)
        students = filtered_query.all()
        return jsonify([student.to_dict() for student in students])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@student_bp.route("/students", methods=["POST"])
@require_auth
def create_student():
    """Criar um novo aluno para o usuário logado"""
    try:
        data = request.get_json()

        payment_due_date_str = data.get("payment_due_date")
        payment_due_date = datetime.strptime(payment_due_date_str, "%Y-%m-%d").date() if payment_due_date_str else None

        new_student = Student(
            teacher_id=g.current_user.id,  # Usar teacher_id em vez de user_id
            name=data["name"],
            phone_number=data["phone_number"],
            payment_due_date=payment_due_date,
            scholarship_percentage=data.get("scholarship_percentage", 0),
            photo_url=data.get("photo_url")
        )
        db.session.add(new_student)
        db.session.commit()
        return jsonify(new_student.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@student_bp.route("/students/<student_id>", methods=["GET"])
@require_auth
def get_student(student_id):
    """Obter um aluno específico"""
    try:
        student = Student.query.get_or_404(student_id)
        
        if not can_access_student(g.current_user, student):
            return jsonify({"error": "Acesso negado"}), 403
        
        return jsonify(student.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@student_bp.route("/students/<student_id>", methods=["PUT"])
@require_auth
def update_student(student_id):
    """Atualizar um aluno existente"""
    try:
        student = Student.query.get_or_404(student_id)
        
        if not can_access_student(g.current_user, student):
            return jsonify({"error": "Acesso negado"}), 403
        
        data = request.get_json()

        student.name = data.get("name", student.name)
        student.phone_number = data.get("phone_number", student.phone_number)
        
        payment_due_date_str = data.get("payment_due_date")
        student.payment_due_date = datetime.strptime(payment_due_date_str, "%Y-%m-%d").date() if payment_due_date_str else None

        student.scholarship_percentage = data.get("scholarship_percentage", student.scholarship_percentage)
        student.photo_url = data.get("photo_url", student.photo_url)

        db.session.commit()
        return jsonify(student.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@student_bp.route("/students/<student_id>", methods=["DELETE"])
@require_auth
def delete_student(student_id):
    """Deletar um aluno"""
    try:
        student = Student.query.get_or_404(student_id)
        
        if not can_access_student(g.current_user, student):
            return jsonify({"error": "Acesso negado"}), 403
        
        db.session.delete(student)
        db.session.commit()
        return jsonify({"message": "Aluno deletado com sucesso"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@student_bp.route("/students/export/xlsx", methods=["GET"])
@require_auth
def export_students_xlsx():
    """Exportar lista de alunos para um arquivo Excel (xlsx)"""
    try:
        query = Student.query
        filtered_query = filter_by_user_access(query, Student, g.current_user)
        students = filtered_query.all()

        wb = Workbook()
        ws = wb.active
        ws.title = "Alunos ABAA"

        headers = [
            "ID", "Nome", "Telefone", "Data de Vencimento",
            "Percentual de Bolsa", "Status da Bolsa", "Valor a Pagar (Mensalidade)"
        ]
        ws.append(headers)

        for student in students:
            base_monthly_fee = 120.00  # TODO: Este valor deve ser configurável por turma/professor
            discounted_amount = student.calculate_discounted_amount(base_monthly_fee)

            ws.append([
                student.id,
                student.name,
                student.phone_number,
                student.payment_due_date.strftime("%d/%m/%Y") if student.payment_due_date else "",
                f"{student.scholarship_percentage}%",
                student.get_scholarship_status(),
                f"R$ {discounted_amount:.2f}"
            ])

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name="alunos_abaa.xlsx"
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500



