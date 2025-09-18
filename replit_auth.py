import jwt
import os
import uuid
from functools import wraps
from urllib.parse import urlencode

from flask import g, session, redirect, request, render_template, url_for
from flask_dance.consumer import (
    OAuth2ConsumerBlueprint,
    oauth_authorized,
    oauth_error,
)
from flask_dance.consumer.storage import BaseStorage
from flask_login import LoginManager, login_user, logout_user, current_user
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError
from sqlalchemy.exc import NoResultFound
from werkzeug.local import LocalProxy

from app import app, db
from models import OAuth, User
from datetime import datetime

class UserSessionStorage(BaseStorage):

    def get(self, blueprint):
        try:
            token = db.session.query(OAuth).filter_by(
                user_id=current_user.get_id(),
                browser_session_key=g.browser_session_key,
                provider=blueprint.name,
            ).one().token
        except (NoResultFound, AttributeError):
            token = None
        return token

    def set(self, blueprint, token):
        # Clean up old tokens for this user/session/provider
        db.session.query(OAuth).filter_by(
            user_id=current_user.get_id(),
            browser_session_key=g.browser_session_key,
            provider=blueprint.name,
        ).delete()
        
        # Create new OAuth record
        new_model = OAuth()
        new_model.user_id = current_user.get_id()
        new_model.browser_session_key = g.browser_session_key
        new_model.provider = blueprint.name
        new_model.token = str(token)  # Ensure token is stored as string
        db.session.add(new_model)
        db.session.commit()

    def delete(self, blueprint):
        db.session.query(OAuth).filter_by(
            user_id=current_user.get_id(),
            browser_session_key=g.browser_session_key,
            provider=blueprint.name).delete()
        db.session.commit()


def make_replit_blueprint():
    try:
        repl_id = os.environ['REPL_ID']
    except KeyError:
        raise SystemExit("the REPL_ID environment variable must be set")

    issuer_url = os.environ.get('ISSUER_URL', "https://replit.com/oidc")

    replit_bp = OAuth2ConsumerBlueprint(
        "replit_auth",
        __name__,
        client_id=repl_id,
        client_secret=None,
        base_url=issuer_url,
        authorization_url_params={
            "prompt": "login consent",
        },
        token_url=issuer_url + "/token",
        token_url_params={
            "auth": (),
            "include_client_id": True,
        },
        auto_refresh_url=issuer_url + "/token",
        auto_refresh_kwargs={
            "client_id": repl_id,
        },
        authorization_url=issuer_url + "/auth",
        use_pkce=True,
        code_challenge_method="S256",
        scope=["openid", "profile", "email", "offline_access"],
        storage=UserSessionStorage(),
    )

    @replit_bp.before_app_request
    def set_applocal_session():
        if '_browser_session_key' not in session:
            session['_browser_session_key'] = uuid.uuid4().hex
        session.modified = True
        g.browser_session_key = session['_browser_session_key']
        g.flask_dance_replit = replit_bp.session

    @replit_bp.route("/logout")
    def logout():
        del replit_bp.token
        logout_user()

        end_session_endpoint = issuer_url + "/session/end"
        encoded_params = urlencode({
            "client_id": repl_id,
            "post_logout_redirect_uri": request.url_root,
        })
        logout_url = f"{end_session_endpoint}?{encoded_params}"

        return redirect(logout_url)

    @replit_bp.route("/error")
    def error():
        return render_template("auth/replit_error.html"), 403

    return replit_bp


def save_user(user_claims):
    """Save or update user from Replit Auth claims"""
    user = User.query.filter_by(id=user_claims['sub']).first()
    
    if user:
        # Update existing user
        user.email = user_claims.get('email')
        user.first_name = user_claims.get('first_name')
        user.last_name = user_claims.get('last_name')
        user.profile_image_url = user_claims.get('profile_image_url')
        user.last_login = datetime.utcnow()
        user.email_verified = True  # Replit handles email verification
        user.account_active = True
    else:
        # Create new user
        user = User(
            id=user_claims['sub'],
            email=user_claims.get('email'),
            first_name=user_claims.get('first_name'),
            last_name=user_claims.get('last_name'),
            profile_image_url=user_claims.get('profile_image_url'),
            last_login=datetime.utcnow(),
            email_verified=True,
            account_active=True
        )
        db.session.add(user)
    
    db.session.commit()
    return user


@oauth_authorized.connect
def logged_in(blueprint, token):
    """Handle successful Replit Auth login"""
    user_claims = jwt.decode(token['id_token'],
                             options={"verify_signature": False})
    user = save_user(user_claims)
    login_user(user)
    blueprint.token = token
    
    # Redirect to intended page or home
    next_url = session.pop("next_url", None)
    if next_url:
        return redirect(next_url)
    else:
        return redirect(url_for('index'))


@oauth_error.connect
def handle_error(blueprint, error, error_description=None, error_uri=None):
    """Handle Replit Auth errors"""
    return redirect(url_for('replit_auth.error'))


def require_replit_login(f):
    """Decorator to require Replit authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            session["next_url"] = get_next_navigation_url(request)
            return redirect(url_for('replit_auth.login'))

        # Check token expiration and refresh if needed
        if hasattr(g, 'flask_dance_replit') and g.flask_dance_replit.token:
            expires_in = g.flask_dance_replit.token.get('expires_in', 0)
            if expires_in < 0:
                refresh_token_url = os.environ.get('ISSUER_URL', "https://replit.com/oidc") + "/token"
                try:
                    token = g.flask_dance_replit.refresh_token(
                        token_url=refresh_token_url,
                        client_id=os.environ['REPL_ID']
                    )
                    g.flask_dance_replit.token_updater(token)
                except InvalidGrantError:
                    # If refresh fails, require re-login
                    session["next_url"] = get_next_navigation_url(request)
                    return redirect(url_for('replit_auth.login'))

        return f(*args, **kwargs)

    return decorated_function


def get_next_navigation_url(request):
    """Get the URL to redirect to after login"""
    is_navigation_url = request.headers.get(
        'Sec-Fetch-Mode') == 'navigate' and request.headers.get(
            'Sec-Fetch-Dest') == 'document'
    if is_navigation_url:
        return request.url
    return request.referrer or request.url


replit = LocalProxy(lambda: g.flask_dance_replit)