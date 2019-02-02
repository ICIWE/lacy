# -*- coding: utf-8 -*-
# @author: NiHao

from random import randint, sample, choice, choices
from datetime import datetime
from faker import Faker
from sqlalchemy.exc import IntegrityError
from . import db
from .models import User, TV, HistoryTV


def fake_tv_part():
    f = Faker(locale='zh_CN')
    all_tv = TV.query.all()
    d = datetime
    for i in all_tv:
        ep = i.episodes
        i.new_episode = randint(0, ep)
        i.new_date = f.date_between(d(2018, 11, 15), d(2018, 12, 27))
        i.update_detail = 'w:%s' % randint(1, 7)
        if i.new_episode == ep:
            i.serialized = 2
        else:
            i.serialized = 1
        db.session.add(i)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


# def fake_tv_full(num=10):
#     f = Faker(locale='zh_CN')
#     for i in range(num):
#         tv = TV(
#             douban_id=f.random_number(5, 99999),
#             name=f.name(),
#         )


def fake_user(c=100):
    f = Faker(locale='zh_CN')
    i = 0
    while i < c:
        u = User(username=f.name(),
                 email=f.email(),
                 phone_number=f.phone_number(),
                 password='password',
                 confirmed=True,
                 member_since=f.past_date(),
                 about_me=f.text())
        db.session.add(u)
        try:
            db.session.commit()
            i += 1
        except IntegrityError:
            db.session.rollback()


def fake_history(c=10):
    users = User.query.limit(c).all()
    tv = TV.query.all()
    for u in users:
        utv = sample(tv, choice(range(2, 10)))
        for i in utv:
            ep = i.episodes
            we = list(range(1, choice(range(0, ep))))
            we = ';'.join([str(z) for z in we])
            h = HistoryTV(user_id=u.id,
                          tv_id=i.id,
                          watched_episodes=we)
            db.session.add(h)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()