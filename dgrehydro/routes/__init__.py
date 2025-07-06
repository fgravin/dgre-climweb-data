from flask import jsonify, Blueprint

def error(status=400, detail='Bad Request'):
    return jsonify({
        'status': status,
        'detail': detail
    }), status


endpoints = Blueprint('endpoints', __name__)
