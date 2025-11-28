import json
import os
import threading
import uuid
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import secrets

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
REVOKED_FILE = os.path.join(DATA_DIR, 'revoked_tokens.json')
_lock = threading.Lock()


def _ensure_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump({'users': []}, f)
    if not os.path.exists(REVOKED_FILE):
        with open(REVOKED_FILE, 'w', encoding='utf-8') as f:
            json.dump({'revoked': []}, f)


def _load():
    _ensure_files()
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save(data):
    _ensure_files()
    with _lock:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)


def _load_revoked():
    _ensure_files()
    with open(REVOKED_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_revoked(data):
    _ensure_files()
    with _lock:
        with open(REVOKED_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)


def find_user_by_username(username):
    data = _load()
    for u in data.get('users', []):
        if u.get('username') == username:
            return u
    return None


def create_user(username, password, display_name=None):
    if find_user_by_username(username):
        raise ValueError('user_exists')
    user = {
        'username': username,
        'display_name': display_name or username,
        'password_hash': generate_password_hash(password),
        'avatar_url': None
    }
    data = _load()
    data.setdefault('users', []).append(user)
    _save(data)
    u = user.copy()
    del u['password_hash']
    return u


def authenticate_user(username, password):
    u = find_user_by_username(username)
    if not u:
        return None
    if not check_password_hash(u.get('password_hash', ''), password):
        return None
    return {k: v for k, v in u.items() if k != 'password_hash'}


def update_user_avatar(username, avatar_url):
    data = _load()
    changed = False
    for u in data.get('users', []):
        if u.get('username') == username:
            u['avatar_url'] = avatar_url
            changed = True
            break
    if changed:
        _save(data)
    return changed


def get_public_user(user):
    if not user:
        return None
    return {
        'username': user.get('username'),
        'display_name': user.get('display_name'),
        'avatar_url': user.get('avatar_url')
    }


def create_jwt_for_user(username, secret, expires_minutes=1440):
    now = datetime.utcnow()
    jti = uuid.uuid4().hex
    payload = {
        'sub': username,
        'iat': int(now.timestamp()),
        'exp': int((now + timedelta(minutes=expires_minutes)).timestamp()),
        'jti': jti
    }
    token = jwt.encode(payload, secret, algorithm='HS256')
    return token, payload


def verify_jwt(token, secret):
    try:
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        # Check revocation
        revoked = _load_revoked().get('revoked', [])
        if payload.get('jti') in revoked:
            return None
        return payload
    except Exception:
        return None


def revoke_jwt_jti(jti):
    data = _load_revoked()
    revoked = set(data.get('revoked', []))
    revoked.add(jti)
    _save_revoked({'revoked': list(revoked)})


def create_refresh_token_for_user(username, secret, expires_days=30):
    now = datetime.utcnow()
    jti = uuid.uuid4().hex
    payload = {
        'sub': username,
        'iat': int(now.timestamp()),
        'exp': int((now + timedelta(days=expires_days)).timestamp()),
        'jti': jti,
        'typ': 'refresh'
    }
    token = jwt.encode(payload, secret, algorithm='HS256')
    # store refresh token jti on user record
    data = _load()
    for u in data.get('users', []):
        if u.get('username') == username:
            u.setdefault('refresh_tokens', []).append({'jti': jti, 'exp': payload['exp']})
            _save(data)
            break
    return token, payload


def verify_refresh_token(token, secret):
    try:
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        if payload.get('typ') != 'refresh':
            return None
        # ensure jti exists on user
        username = payload.get('sub')
        data = _load()
        for u in data.get('users', []):
            if u.get('username') == username:
                for rt in u.get('refresh_tokens', []):
                    if rt.get('jti') == payload.get('jti'):
                        return payload
        return None
    except Exception:
        return None


def revoke_refresh_token_jti(username, jti):
    data = _load()
    changed = False
    for u in data.get('users', []):
        if u.get('username') == username:
            tokens = u.get('refresh_tokens', [])
            tokens = [t for t in tokens if t.get('jti') != jti]
            u['refresh_tokens'] = tokens
            changed = True
            break
    if changed:
        _save(data)


def revoke_all_refresh_tokens_for_user(username):
    data = _load()
    changed = False
    for u in data.get('users', []):
        if u.get('username') == username:
            u['refresh_tokens'] = []
            changed = True
            break
    if changed:
        _save(data)


def update_display_name(username, display_name):
    data = _load()
    changed = False
    for u in data.get('users', []):
        if u.get('username') == username:
            u['display_name'] = display_name
            changed = True
            break
    if changed:
        _save(data)
    return changed

