from flask import Blueprint, jsonify, request, session, redirect, url_for
from src.models.user import User, db
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import os

user_bp = Blueprint("user", __name__)

# Configurações do Google OAuth (substitua com suas credenciais reais)
# CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
# CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
# TODO: Configurar variáveis de ambiente para CLIENT_ID e CLIENT_SECRET
CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com" # Placeholder

@user_bp.route("/auth/google", methods=["POST"])
def google_auth():
    token = request.json.get("token")
    if not token:
        return jsonify({"error": "Token não fornecido"}), 400

    try:
        # Verificar o token de ID do Google
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), CLIENT_ID)

        if idinfo["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
            raise ValueError("Wrong issuer.")

        user_google_id = idinfo["sub"]
        user_email = idinfo["email"]
        user_name = idinfo["name"]
        user_picture = idinfo["picture"]

        user = User.query.filter_by(google_id=user_google_id).first()

        if not user:
            # Se o usuário não existe, cria um novo com role 'teacher' por padrão
            # O primeiro usuário a se registrar pode ser definido como admin manualmente no DB
            # Ou ter uma lógica para o primeiro usuário ser admin
            new_user = User(
                google_id=user_google_id,
                email=user_email,
                name=user_name,
                profile_picture_url=user_picture,
                role="teacher" # Default role
            )
            db.session.add(new_user)
            db.session.commit()
            user = new_user
        else:
            # Atualiza os dados do usuário existente
            user.email = user_email
            user.name = user_name
            user.profile_picture_url = user_picture
            db.session.commit()

        # Armazenar informações do usuário na sessão (ou retornar JWT)
        session["user_id"] = user.id
        session["user_role"] = user.role

        return jsonify(user.to_dict()), 200

    except ValueError as e:
        return jsonify({"error": f"Token inválido: {str(e)}"}), 401
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro na autenticação: {str(e)}"}), 500

@user_bp.route("/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    session.pop("user_role", None)
    return jsonify({"message": "Logout realizado com sucesso"}), 200

@user_bp.route("/me", methods=["GET"])
def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Não autenticado"}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404
    
    return jsonify(user.to_dict()), 200

@user_bp.route("/users", methods=["GET"])
def get_users():
    # Apenas administradores podem listar todos os usuários
    if session.get("user_role") != "admin":
        return jsonify({"error": "Acesso negado"}), 403
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@user_bp.route("/users/<user_id>", methods=["GET"])
def get_user(user_id):
    # Usuário pode ver seus próprios dados, admin pode ver qualquer um
    if session.get("user_id") != user_id and session.get("user_role") != "admin":
        return jsonify({"error": "Acesso negado"}), 403
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@user_bp.route("/users/<user_id>", methods=["PUT"])
def update_user(user_id):
    # Usuário pode atualizar seus próprios dados, admin pode atualizar qualquer um
    if session.get("user_id") != user_id and session.get("user_role") != "admin":
        return jsonify({"error": "Acesso negado"}), 403
    
    user = User.query.get_or_404(user_id)
    data = request.json
    user.name = data.get("name", user.name)
    user.email = data.get("email", user.email)
    user.profile_picture_url = data.get("profile_picture_url", user.profile_picture_url)
    # Apenas admin pode mudar o role
    if session.get("user_role") == "admin" and "role" in data:
        user.role = data["role"]
    db.session.commit()
    return jsonify(user.to_dict())

@user_bp.route("/users/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    # Apenas administradores podem deletar usuários
    if session.get("user_role") != "admin":
        return jsonify({"error": "Acesso negado"}), 403
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return "", 204


