
import os
import re
import pytest
from flask import current_app
from app import create_app, db
from app.models import User, TV


@pytest.fixture
def client():
    app = create_app('testing')
    client = app.test_client()
    app_context = app.app_context()
    app_context.push()
    db.create_all()

    yield client

    db.session.remove()
    db.drop_all()
    app_context.pop()


# def test_basic_app_exists():
#     assert current_app is not None
#
#
# def test_basic_app_in_testing(client):
#     assert current_app.config['TESTING'] is not None


# def test_home_page(client):
#     resp = client.get('/')
#     print(resp.data)
#     assert '请登陆后查看' in resp.get_data(as_text=True)
