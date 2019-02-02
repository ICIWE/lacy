# -*- coding: utf-8 -*-
# @author: NiHao

from flask import Blueprint

api = Blueprint('api', __name__)

from . import authentication, errors, views
