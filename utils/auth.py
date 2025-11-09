from functools import wraps
from flask import request, jsonify, g
from src.models.user import User

def get_current_user():
    """
    Obtém o usuário atual baseado no user_id fornecido no header da requisição.
    Em um ambiente de produção, isso seria baseado em um token JWT ou sessão.
    """
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return None
    
    user = User.query.get(user_id)
    return user

def require_auth(f):
    """
    Decorator que requer autenticação para acessar uma rota.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Autenticação necessária'}), 401
        
        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    """
    Decorator que requer papel de administrador para acessar uma rota.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Autenticação necessária'}), 401
        
        if user.role != 'admin':
            return jsonify({'error': 'Acesso negado. Apenas administradores podem acessar esta funcionalidade.'}), 403
        
        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function

def can_access_student(user, student):
    """
    Verifica se o usuário pode acessar os dados de um aluno específico.
    Administradores podem acessar qualquer aluno.
    Professores só podem acessar alunos que eles cadastraram.
    """
    if user.role == 'admin':
        return True
    
    return student.teacher_id == user.id

def can_access_class(user, dance_class):
    """
    Verifica se o usuário pode acessar os dados de uma turma específica.
    Administradores podem acessar qualquer turma.
    Professores só podem acessar turmas que eles criaram.
    """
    if user.role == 'admin':
        return True
    
    return dance_class.teacher_id == user.id

def can_access_payment(user, payment):
    """
    Verifica se o usuário pode acessar os dados de um pagamento específico.
    Administradores podem acessar qualquer pagamento.
    Professores só podem acessar pagamentos relacionados aos seus alunos.
    """
    if user.role == 'admin':
        return True
    
    return payment.teacher_id == user.id

def filter_by_user_access(query, model, user):
    """
    Filtra uma query baseada no acesso do usuário.
    Administradores veem todos os registros.
    Professores veem apenas seus próprios registros.
    """
    if user.role == 'admin':
        return query
    
    # Para modelos que têm teacher_id
    if hasattr(model, 'teacher_id'):
        return query.filter(model.teacher_id == user.id)
    
    # Para modelos que têm user_id (compatibilidade com código antigo)
    if hasattr(model, 'user_id'):
        return query.filter(model.user_id == user.id)
    
    return query

