# -*- coding: utf-8 -*-
# @author: NiHao

import os

import click
from dotenv import load_dotenv
from flask_migrate import Migrate, upgrade
from app import create_app, db
from app.models import User, Role, TV, Collection, ActionLog, HistoryTV, Subscription, StoreUp


load_dotenv()

# 临时使用 default ，主架构完成后改成可选。
app = create_app('development')
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, Role=Role, User=User, TV=TV, ActionLog=ActionLog,
                Col=Collection, H=HistoryTV, S=Subscription, StoreUp=StoreUp)


@app.cli.command()
@click.option('--length', default=25,
              help='Number of functions to include in the profiler report.')
@click.option('--profile-dir', default=None,
              help='Directory where profiler data files are saved.')
def profile(length, profile_dir):
    """Start the application under the code profiler."""
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length],
                                      profile_dir=profile_dir)
    app.run()


@app.cli.command()
def deploy():
    """ 部署 """
    upgrade()
