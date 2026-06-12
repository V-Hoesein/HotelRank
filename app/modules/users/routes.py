from flask import Blueprint

users_bp = Blueprint('users', __name__)

@users_bp.route('/')
def list_users():
    return {"message": "Users endpoint"}
