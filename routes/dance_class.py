from flask import Blueprint, request, jsonify
from src.models import db, DanceClass, Student, student_classes, User # Importar User
from datetime import datetime, time

dance_class_bp = Blueprint("dance_class", __name__)

# Helper para obter o user_id (temporário, será substituído pela autenticação real)
def get_current_user_id():
    # TODO: Implementar autenticação real e obter o user_id do usuário logado
    # Por enquanto, para testes, podemos usar um user_id fixo ou passar via header/query param
    # Exemplo: return request.headers.get("X-User-ID", "some_default_user_id")
    return request.args.get("user_id") # Mantendo como query param por enquanto para compatibilidade

@dance_class_bp.route("/classes", methods=["GET"])
def get_classes():
    """Listar todas as turmas do usuário logado"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"error": "user_id é obrigatório"}), 400
            
        classes = DanceClass.query.filter_by(user_id=user_id).all()
        return jsonify([dance_class.to_dict() for dance_class in classes])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@dance_class_bp.route("/classes", methods=["POST"])
def create_class():
    """Criar uma nova turma para o usuário logado"""
    try:
        data = request.get_json()
        user_id = get_current_user_id()
        
        # Validação dos dados obrigatórios
        required_fields = ["name", "day_of_week", "start_time", "end_time", "location", "monthly_fee"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} é obrigatório"}), 400
        
        # Converter strings de tempo para objetos time
        start_time = datetime.strptime(data["start_time"], ",%H:%M").time()
        end_time = datetime.strptime(data["end_time"], ",%H:%M").time()
        
        dance_class = DanceClass(
            user_id=user_id,
            name=data["name"],
            day_of_week=data["day_of_week"],
            start_time=start_time,
            end_time=end_time,
            location=data["location"],
            monthly_fee=data["monthly_fee"]
        )
        
        db.session.add(dance_class)
        db.session.commit()
        
        return jsonify(dance_class.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@dance_class_bp.route("/classes/<class_id>", methods=["GET"])
def get_class(class_id):
    """Obter detalhes de uma turma específica do usuário logado"""
    try:
        user_id = get_current_user_id()
        dance_class = DanceClass.query.filter_by(id=class_id, user_id=user_id).first_or_404()
        class_data = dance_class.to_dict()
        
        # Adicionar lista de alunos da turma
        students = Student.query.join(student_classes).filter(student_classes.c.class_id == class_id).all()
        class_data["students"] = [student.to_dict() for student in students]
        
        return jsonify(class_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@dance_class_bp.route("/classes/<class_id>", methods=["PUT"])
def update_class(class_id):
    """Atualizar informações de uma turma do usuário logado"""
    try:
        user_id = get_current_user_id()
        dance_class = DanceClass.query.filter_by(id=class_id, user_id=user_id).first_or_404()
        data = request.get_json()
        
        # Atualizar campos se fornecidos
        if "name" in data:
            dance_class.name = data["name"]
        if "day_of_week" in data:
            dance_class.day_of_week = data["day_of_week"]
        if "start_time" in data:
            dance_class.start_time = datetime.strptime(data["start_time"], ",%H:%M").time()
        if "end_time" in data:
            dance_class.end_time = datetime.strptime(data["end_time"], ",%H:%M").time()
        if "location" in data:
            dance_class.location = data["location"]
        if "monthly_fee" in data:
            dance_class.monthly_fee = data["monthly_fee"]
        
        dance_class.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(dance_class.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@dance_class_bp.route("/classes/<class_id>", methods=["DELETE"])
def delete_class(class_id):
    """Excluir uma turma do usuário logado"""
    try:
        user_id = get_current_user_id()
        dance_class = DanceClass.query.filter_by(id=class_id, user_id=user_id).first_or_404()
        db.session.delete(dance_class)
        db.session.commit()
        
        return jsonify({"message": "Turma excluída com sucesso"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@dance_class_bp.route("/classes/<class_id>/students", methods=["POST"])
def add_student_to_class(class_id):
    """Adicionar um aluno a uma turma do usuário logado"""
    try:
        data = request.get_json()
        student_id = data.get("student_id")
        user_id = get_current_user_id()
        
        if not student_id:
            return jsonify({"error": "student_id é obrigatório"}), 400
        
        # Verificar se o aluno e a turma existem e pertencem ao usuário
        student = Student.query.filter_by(id=student_id, user_id=user_id).first_or_404()
        dance_class = DanceClass.query.filter_by(id=class_id, user_id=user_id).first_or_404()
        
        # Verificar se o aluno já está na turma
        existing = db.session.query(student_classes).filter_by(
            student_id=student_id, 
            class_id=class_id
        ).first()
        
        if existing:
            return jsonify({"error": "Aluno já está matriculado nesta turma"}), 400
        
        # Adicionar aluno à turma
        student.classes.append(dance_class)
        db.session.commit()
        
        return jsonify({"message": "Aluno adicionado à turma com sucesso"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@dance_class_bp.route("/classes/<class_id>/students/<student_id>", methods=["DELETE"])
def remove_student_from_class(class_id, student_id):
    """Remover um aluno de uma turma do usuário logado"""
    try:
        user_id = get_current_user_id()
        # Verificar se o aluno e a turma existem e pertencem ao usuário
        student = Student.query.filter_by(id=student_id, user_id=user_id).first_or_404()
        dance_class = DanceClass.query.filter_by(id=class_id, user_id=user_id).first_or_404()
        
        # Remover aluno da turma
        student.classes.remove(dance_class)
        db.session.commit()
        
        return jsonify({"message": "Aluno removido da turma com sucesso"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500



