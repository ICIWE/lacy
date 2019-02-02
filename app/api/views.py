# -*- coding: utf-8 -*-
# @author: NiHao

from flask import jsonify
from ..models import TV
from . import api


@api.route('/timeline/')
def get_timeline():
    result = TV.get_timeline_json()
    return jsonify({
        'code': 0,
        'message': 'success',
        'result': result
    })
