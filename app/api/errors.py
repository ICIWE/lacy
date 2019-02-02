# -*- coding: utf-8 -*-
# @author: NiHao

from flask import jsonify

from . import api


def bad_request(msg):
    response = jsonify({'error': 'bad request', 'message': msg})
    response.status_code = 400
    return response


def unauthorized(msg):
    response = jsonify({'error': 'unauthorized', 'message': msg})
    response.status_code = 401
    return response


def forbidden(msg):
    response = jsonify({'error': 'forbidden', 'message': msg})
    response.status_code = 403
    return response


# errorhandler()
