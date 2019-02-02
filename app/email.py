# -*- coding: utf-8 -*-
# @author: NiHao

import os
from threading import Thread
from flask import current_app, render_template
from flask_mail import Message
from . import mail


def send_email_thread(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(recipients, subject, template, sender=None, **kwargs):
    app = current_app._get_current_object()
    msg = Message()
    msg.subject = subject
    msg.sender = sender or os.environ.get('LACY_ADMIN')
    if isinstance(recipients, str):
        recipients = [recipients]
    msg.recipients = recipients
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_email_thread(app, msg))
    thr.start()
    # thr.join() 等待线程结束，此处直接返回，继续执行主线程。
    return thr
