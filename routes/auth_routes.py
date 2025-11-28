import os
import time
import uuid
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
from services.auth_service import (
    create_user,
    authenticate_user,
    get_public_user,
    update_user_avatar,
    create_jwt_for_user,
    verify_jwt,
    revoke_jwt_jti,
    create_refresh_token_for_user,
    verify_refresh_token,
    revoke_refresh_token_jti,
    revoke_all_refresh_tokens_for_user,
    update_display_name,
    find_user_by_username,
)

bp = Blueprint('auth', __name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
AVATAR_DIR = os.path.join(DATA_DIR, 'avatars')
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif'}

os.makedirs(AVATAR_DIR, exist_ok=True)


@bp.route('/api/auth/register', methods=['POST'])
def register():
    payload = request.get_json(force=True)
    username = (payload or {}).get('username')
    password = (payload or {}).get('password')
    display_name = (payload or {}).get('display_name')
    if not username or not password:
        return jsonify({'error': 'username and password required'}), 400
    try:
        user = create_user(username, password, display_name)
        # Create JWT and return to client
        token, payload = create_jwt_for_user(username, current_app.config.get('SECRET_KEY'), expires_minutes=current_app.config.get('JWT_EXP_MINUTES', 1440))
        refresh, rpay = create_refresh_token_for_user(username, current_app.config.get('SECRET_KEY'))
        return jsonify({'ok': True, 'user': get_public_user(user), 'token': token, 'refresh_token': refresh})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@bp.route('/api/auth/login', methods=['POST'])
def login():
    payload = request.get_json(force=True)
    username = (payload or {}).get('username')
    password = (payload or {}).get('password')
    if not username or not password:
        return jsonify({'error': 'username and password required'}), 400
    user = authenticate_user(username, password)
    if not user:
        return jsonify({'error': 'invalid-credentials'}), 401
    token, payload = create_jwt_for_user(username, current_app.config.get('SECRET_KEY'), expires_minutes=current_app.config.get('JWT_EXP_MINUTES', 1440))
    refresh, rpay = create_refresh_token_for_user(username, current_app.config.get('SECRET_KEY'))
    return jsonify({'ok': True, 'user': get_public_user(user), 'token': token, 'refresh_token': refresh})


def _auth_from_request(req):
    # Accept token via Authorization header or form field
    auth = req.headers.get('Authorization')
    token = None
    if auth and auth.startswith('Bearer '):
        token = auth.split(' ', 1)[1].strip()
    else:
        token = req.form.get('token') or req.args.get('token')
    if not token:
        return None
    payload = verify_jwt(token, current_app.config.get('SECRET_KEY'))
    if not payload:
        return None
    username = payload.get('sub')
    # return a lightweight user object
    return {'username': username, 'jti': payload.get('jti')}


@bp.route('/api/auth/me', methods=['GET'])
def me():
    auth = _auth_from_request(request)
    if not auth:
        return jsonify({'error': 'not_authenticated'}), 401
    # fetch user record
    user = create_user  # placeholder
    # find public user
    from services.auth_service import find_user_by_username
    u = find_user_by_username(auth.get('username'))
    if not u:
        return jsonify({'error': 'not_found'}), 404
    return jsonify({'ok': True, 'user': get_public_user(u)})


@bp.route('/api/auth/refresh', methods=['POST'])
def refresh():
    payload = request.get_json(silent=True) or {}
    refresh_token = payload.get('refresh_token') or request.form.get('refresh_token')
    if not refresh_token:
        return jsonify({'error': 'missing_refresh_token'}), 400
    verified = verify_refresh_token(refresh_token, current_app.config.get('SECRET_KEY'))
    if not verified:
        return jsonify({'error': 'invalid_refresh'}), 401
    username = verified.get('sub')
    # issue a new access token
    token, _ = create_jwt_for_user(username, current_app.config.get('SECRET_KEY'), expires_minutes=current_app.config.get('JWT_EXP_MINUTES', 1440))
    return jsonify({'ok': True, 'token': token})


@bp.route('/api/auth/update-profile', methods=['PATCH'])
def update_profile():
    auth = _auth_from_request(request)
    if not auth:
        return jsonify({'error': 'not_authenticated'}), 401
    username = auth.get('username')
    payload = request.get_json(silent=True) or {}
    display_name = payload.get('display_name')
    if display_name is None:
        return jsonify({'error': 'nothing_to_update'}), 400
    ok = update_display_name(username, display_name)
    if not ok:
        return jsonify({'error': 'update_failed'}), 500
    u = find_user_by_username(username)
    return jsonify({'ok': True, 'user': get_public_user(u)})


@bp.route('/api/auth/upload-avatar', methods=['POST'])
def upload_avatar():
    auth = _auth_from_request(request)
    if not auth:
        return jsonify({'error': 'not_authenticated'}), 401
    username = auth.get('username')

    if 'avatar' not in request.files:
        return jsonify({'error': 'no_file'}), 400
    f = request.files['avatar']
    if f.filename == '':
        return jsonify({'error': 'empty_filename'}), 400
    filename = secure_filename(f.filename)
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext not in ALLOWED_EXT:
        return jsonify({'error': 'invalid_file_type'}), 400
    ts = int(time.time())
    out_name = f"{username}_{ts}_{uuid.uuid4().hex}.{ext}"
    out_path = os.path.join(AVATAR_DIR, out_name)
    f.save(out_path)
    avatar_url = f'/avatars/{out_name}'
    update_user_avatar(username, avatar_url)
    return jsonify({'ok': True, 'avatar_url': avatar_url})


@bp.route('/api/auth/logout', methods=['POST'])
def logout():
    # Revoke token by JTI
    # Accept optional refresh_token to revoke that refresh session too
    auth = _auth_from_request(request)
    body = request.get_json(silent=True) or {}
    refresh_token = body.get('refresh_token') or request.form.get('refresh_token')
    if not auth and not refresh_token:
        return jsonify({'error': 'not_authenticated'}), 401
    if auth:
        jti = auth.get('jti')
        username = auth.get('username')
        if jti:
            revoke_jwt_jti(jti)
    if refresh_token:
        # try to decode refresh to get jti and username
        v = verify_refresh_token(refresh_token, current_app.config.get('SECRET_KEY'))
        if v:
            revoke_refresh_token_jti(v.get('sub'), v.get('jti'))
    return jsonify({'ok': True})


@bp.route('/api/auth/logout-all', methods=['POST'])
def logout_all():
    auth = _auth_from_request(request)
    if not auth:
        return jsonify({'error': 'not_authenticated'}), 401
    username = auth.get('username')
    # revoke all refresh tokens and optionally mark current access jti revoked
    revoke_all_refresh_tokens_for_user(username)
    jti = auth.get('jti')
    if jti:
        revoke_jwt_jti(jti)
    return jsonify({'ok': True})


@bp.route('/avatars/<path:filename>', methods=['GET'])
def serve_avatar(filename):
    return send_from_directory(AVATAR_DIR, filename)
