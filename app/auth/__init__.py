# -*- coding: utf-8 -*-
# @author: NiHao

from flask import Blueprint


auth = Blueprint('auth', __name__)


from . import form, views