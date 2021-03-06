# -*- coding: utf-8 -*-
# @author: NiHao

from flask import g
from flask_httpauth import HTTPBasicAuth
from .errors import bad_request, unauthorized, forbidden
from . import api
from ..models import User


auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(email_or_token, password):  # 输入参数的顺序不能错。
    if email_or_token == '':
        return False
    if password == '':
        g.current_user = User.verify_auth_token(email_or_token)
        g.token_used = True
        return g.current_user is not None
    user = User.query.filter_by(email=email_or_token).first()
    if not user:
        return False
    g.current_user = user
    g.token_used = False
    return user.check_password(password)


@auth.error_handler
def auth_error():
    return unauthorized('Invalid credentials')


@api.before_request
@auth.login_required
def before_request():
    if not g.current_user.is_anonymous and \
            not g.current_user.confirmed:
        return forbidden('Unconfirmed account')
