from flask import Blueprint, request, jsonify, g
from ..models.user import User, db
from ..utils.auth import require_admin, require_auth

teacher_bp = Blueprint("teacher_bp", __name__)

@teacher_bp.route("/teachers", methods=["GET"])
@require_admin
def get_teachers():
    """Listar todos os professores (apenas para administradores)"""
    try:
        teachers = User.query.filter_by(role='teacher').all()
        return jsonify([teacher.to_dict() for teacher in teachers])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@teacher_bp.route("/teachers", methods=["POST"])
@require_admin
def create_teacher():
    """Criar um novo professor (apenas para administradores)"""
    try:
        data = request.get_json()
        
        # Verificar se o email já existe
        existing_user = User.query.filter_by(email=data["email"]).first()
        if existing_user:
            return jsonify({"error": "Email já está em uso"}), 400
        
        new_teacher = User(
            google_id=data.get("google_id", ""),  # Pode ser preenchido posteriormente no primeiro login
            email=data["email"],
            name=data["name"],
            profile_picture_url=data.get("profile_picture_url"),
            role="teacher"
        )
        
        db.session.add(new_teacher)
        db.session.commit()
        return jsonify(new_teacher.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@teacher_bp.route("/teachers/<teacher_id>", methods=["GET"])
@require_admin
def get_teacher(teacher_id):
    """Obter um professor específico (apenas para administradores)"""
    try:
        teacher = User.query.filter_by(id=teacher_id, role='teacher').first_or_404()
        return jsonify(teacher.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@teacher_bp.route("/teachers/<teacher_id>", methods=["PUT"])
@require_admin
def update_teacher(teacher_id):
    """Atualizar um professor existente (apenas para administradores)"""
    try:
        teacher = User.query.filter_by(id=teacher_id, role='teacher').first_or_404()
        data = request.get_json()
        
        # Verificar se o novo email já existe (se estiver sendo alterado)
        if data.get("email") and data["email"] != teacher.email:
            existing_user = User.query.filter_by(email=data["email"]).first()
            if existing_user:
                return jsonify({"error": "Email já está em uso"}), 400
        
        teacher.email = data.get("email", teacher.email)
        teacher.name = data.get("name", teacher.name)
        teacher.profile_picture_url = data.get("profile_picture_url", teacher.profile_picture_url)
        
        db.session.commit()
        return jsonify(teacher.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@teacher_bp.route("/teachers/<teacher_id>", methods=["DELETE"])
@require_admin
def delete_teacher(teacher_id):
    """Deletar um professor (apenas para administradores)"""
    try:
        teacher = User.query.filter_by(id=teacher_id, role='teacher').first_or_404()
        
        # Verificar se o professor tem alunos ou turmas associadas
        if teacher.students or teacher.classes:
            return jsonify({
                "error": "Não é possível deletar professor que possui alunos ou turmas associadas. "
                        "Transfira ou delete os dados associados primeiro."
            }), 400
        
        db.session.delete(teacher)
        db.session.commit()
        return jsonify({"message": "Professor deletado com sucesso"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@teacher_bp.route("/teachers/<teacher_id>/stats", methods=["GET"])
@require_admin
def get_teacher_stats(teacher_id):
    """Obter estatísticas de um professor específico (apenas para administradores)"""
    try:
        teacher = User.query.filter_by(id=teacher_id, role='teacher').first_or_404()
        
        stats = {
            "teacher_info": teacher.to_dict(),
            "total_students": len(teacher.students),
            "total_classes": len(teacher.classes),
            "total_private_combos": len(teacher.private_class_combos)
        }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@teacher_bp.route("/profile", methods=["GET"])
@require_auth
def get_my_profile():
    """Obter perfil do usuário logado"""
    try:
        return jsonify(g.current_user.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@teacher_bp.route("/profile", methods=["PUT"])
@require_auth
def update_my_profile():
    """Atualizar perfil do usuário logado"""
    try:
        data = request.get_json()
        
        # Verificar se o novo email já existe (se estiver sendo alterado)
        if data.get("email") and data["email"] != g.current_user.email:
            existing_user = User.query.filter_by(email=data["email"]).first()
            if existing_user:
                return jsonify({"error": "Email já está em uso"}), 400
        
        g.current_user.email = data.get("email", g.current_user.email)
        g.current_user.name = data.get("name", g.current_user.name)
        g.current_user.profile_picture_url = data.get("profile_picture_url", g.current_user.profile_picture_url)
        
        db.session.commit()
        return jsonify(g.current_user.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

