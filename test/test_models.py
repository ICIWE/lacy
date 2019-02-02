# -*- coding: utf-8 -*-
# @author: NiHao

import time
import datetime
import logging
import pytest
from flask_sqlalchemy import BaseQuery
from app import create_app, db
from app.models import User, TV, Subscription, HistoryTV, Collection


# formatter = '%(asctime)s -%(name)s -%(levelname)s -%(message)s'
# logging.basicConfig(level=logging.DEBUG, format=formatter)
# log = logging.getLogger(__name__)


class TestUser(object):
    @pytest.fixture(autouse=True)
    def transact(self, request):
        app = create_app('testing')
        app_context = app.app_context()
        app_context.push()
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()
        app_context.pop()

    def test_password_setter_and_getter(self):
        u = User(password='dog')
        with pytest.raises(AttributeError):
            u.password
        assert u.password_hash is not None

    def test_check_passwrod(self):
        u = User(username='dog', password='dog')
        assert u.check_password('dog') is True
        assert u.check_password('cat') is False

    def test_store_load_user(self):
        u = User(username='dog', password='dog')
        db.session.add(u)
        db.session.commit()
        u = User.query.filter_by(id=1).first()
        assert u is not None
        assert u.username == 'dog'
        assert u.password_hash is not None
        assert u.confirmed == False
        assert u.member_since is not None

    def test_confirm_token(self):
        u = User(username='dog', password='dog')
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirm_token()
        assert u.confirm_token(token) is True
        assert u.confirmed is True

    def test_invalid_confirm_token(self):
        u1 = User(username='dog', password='dog')
        u2 = User(username='cat', password='cat')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_confirm_token()
        assert u2.confirm_token(token) is False

    def test_expired_confirm_token(self):
        u = User(username='dog', password='dog')
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirm_token(expires_in=1)
        time.sleep(2)
        assert u.confirm_token(token) is False

    def test_valid_reset_token(self):
        u = User(username='dog', password='dog')
        db.session.add(u)
        db.session.commit()
        token = u.generate_reset_token()
        assert u.reset_password(token, 'cat') is True
        db.session.commit()
        assert u.check_password('cat') is True

    def test_invalid_reset_token(self):
        u = User(username='dog', password='dog')
        db.session.add(u)
        db.session.commit()
        token = u.generate_reset_token()
        assert u.reset_password(token + 'dog', 'cat') is False
        assert u.check_password('dog') is True

    def test_valid_modify_email_token(self):
        u = User(username='dog', password='dog', email='dog@a.com')
        db.session.add(u)
        db.session.commit()
        token = u.generate_modify_email_token('new@a.com')
        assert u.modify_email(token) is True
        db.session.commit()
        assert u.email == 'new@a.com'

    def test_invalid_modify_email_token(self):
        u1 = User(username='dog', password='dog', email='dog@a.com')
        u2 = User(username='cat', password='cat', email='cat@a.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_modify_email_token('new@a.com')
        assert u2.modify_email(token) is False
        assert u2.email == 'cat@a.com'

    def test_duplicate_modify_email_token(self):
        u1 = User(username='dog', password='dog', email='dog@a.com')
        u2 = User(username='cat', password='cat', email='cat@a.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_modify_email_token('cat@a.com')
        assert u1.modify_email(token) is False
        assert u1.email == 'dog@a.com'

    def test_valid_auth_token(self):
        u = User(username='dog', password='dog')
        db.session.add(u)
        db.session.commit()
        token = u.generate_auth_token()
        user = u.verify_auth_token(token)
        assert user is not None
        assert user == u

    def test_subscribe_tv(self):
        u1 = User(username='dog', password='dog', email='dog@a.com')
        u2 = User(username='cat', password='cat', email='cat@a.com')
        tv1 = TV(name='a', serialized='1', tv_type='剧情', country='中国', tv_release='2018-8-9')
        tv2 = TV(name='b', serialized='2', tv_type='戏剧', country='加拿大', tv_release='2015-8-9')
        db.session.add(u1)
        db.session.add(u2)
        db.session.add(tv1)
        db.session.add(tv2)
        db.session.commit()
        u1.subscribe_tv(tv1)
        db.session.commit()
        assert u1.tv_is_subscribed(tv1) is True
        assert u1.tv_is_subscribed(tv2) is False
        assert u2.tv_is_subscribed(tv1) is False
        assert u1.subscribed_tv.filter_by(tv_id=tv1.id).first() is not None

    def test_unsubscribe_tv(self):
        u = User(username='dog', password='dog', email='dog@a.com')
        tv1 = TV(name='a', serialized='1', tv_type='剧情', country='中国', tv_release='2018-8-9')
        tv2 = TV(name='b', serialized='2', tv_type='戏剧', country='加拿大', tv_release='2015-8-9')
        db.session.add(u)
        db.session.add(tv1)
        db.session.add(tv2)
        db.session.commit()
        u.subscribe_tv(tv1)
        db.session.commit()
        assert u.tv_is_subscribed(tv1) is True
        assert u.unsubscribe_tv(tv2) is False
        assert u.unsubscribe_tv(tv1) is True
        assert Subscription.query.first() is None
        assert TV.query.first() is not None
        assert User.query.first() is not None

    def test_watched_tv(self):
        pass

    def test_subscribed_tv_order_by_watched(self):
        u1 = User(username='dog', password='dog', email='dog@a.com')
        u2 = User(username='cat', password='cat', email='cat@a.com')
        tv1 = TV(name='a', serialized='1', tv_type='剧情', country='中国', tv_release='2018-8-9')
        tv2 = TV(name='b', serialized='2', tv_type='戏剧', country='加拿大', tv_release='2015-8-9')
        tv3 = TV(name='c', serialized='1', tv_type='言情/古装', country='中国', tv_release='2018-8-9')
        tv4 = TV(name='d', serialized='2', tv_type='纪录片', country='中国', tv_release='2014-8-9')
        tv5 = TV(name='e', serialized='1', tv_type='剧情', country='日本', tv_release='2013-8-9')
        db.session.add(u1)
        db.session.add(u2)
        db.session.add(tv1)
        db.session.add(tv2)
        db.session.add(tv3)
        db.session.add(tv4)
        db.session.add(tv5)
        db.session.commit()
        s1 = Subscription(user_id=u1.id, tv_id=tv1.id)
        s2 = Subscription(user_id=u1.id, tv_id=tv2.id)
        s3 = Subscription(user_id=u1.id, tv_id=tv3.id)
        s4 = Subscription(user_id=u1.id, tv_id=tv5.id)
        db.session.add(s1)
        db.session.add(s2)
        db.session.add(s3)
        db.session.add(s4)
        db.session.commit()
        h1 = HistoryTV(user_id=u1.id, tv_id=tv1.id, timestamp_watched=datetime.datetime(2019, 1, 1))
        h2 = HistoryTV(user_id=u1.id, tv_id=tv2.id, timestamp_watched=datetime.datetime(2019, 1, 3))
        h3 = HistoryTV(user_id=u1.id, tv_id=tv3.id, timestamp_watched=datetime.datetime(2019, 1, 5))
        h4 = HistoryTV(user_id=u1.id, tv_id=tv5.id, timestamp_watched=datetime.datetime(2019, 1, 12))
        h5 = HistoryTV(user_id=u2.id, tv_id=tv4.id, timestamp_watched=datetime.datetime(2019, 1, 18))
        db.session.add(h1)
        db.session.add(h2)
        db.session.add(h3)
        db.session.add(h4)
        db.session.add(h5)
        db.session.commit()
        result = u1.subscribed_tv_order_by_watched().all()
        r_s = [i.subscribed_tv for i in u1.subscribed_tv.all()]
        assert len(result) == len(r_s)
        assert result[0].id == tv5.id
        assert result[-1].id == tv1.id
        assert tv4 not in r_s
        assert u2.subscribed_tv_order_by_watched().first() is None


class TestTV(object):
    @pytest.fixture(autouse=True)
    def transact(self, request):
        app = create_app('testing')
        app_context = app.app_context()
        app_context.push()
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()
        app_context.pop()

    def test_store_and_load_tv(self):
        tv = TV(name='egg')
        db.session.add(tv)
        db.session.commit()
        tv = TV.query.filter_by(id=1).first()
        assert tv.name == 'egg'

    def test_tv_category(self):
        tv1 = TV(name='a', serialized='1', tv_type='剧情', country='中国', tv_release='2018-8-9')
        tv2 = TV(name='b', serialized='2', tv_type='戏剧', country='加拿大', tv_release='2015-8-9')
        tv3 = TV(name='c', serialized='1', tv_type='言情/古装', country='中国', tv_release='2018-8-9')
        tv4 = TV(name='d', serialized='2', tv_type='纪录片', country='中国', tv_release='2014-8-9')
        tv5 = TV(name='e', serialized='1', tv_type='剧情', country='日本', tv_release='2013-8-9')
        db.session.add(tv1)
        db.session.add(tv2)
        db.session.add(tv3)
        db.session.add(tv4)
        db.session.add(tv5)
        db.session.commit()
        assert len(TV.tv_category(1, '剧情', '中国', 2018).all()) == 1
        assert len(TV.tv_category(1).all()) == 3
        assert len(TV.tv_category(country='日本').all()) ==1
        assert len(TV.tv_category(year='2019').all()) == 0

    def test_generate_categories(self):
        tv1 = TV(name='a', serialized='1', tv_type='剧情', country='中国', tv_release='2018-8-9')
        tv2 = TV(name='b', serialized='2', tv_type='戏剧', country='加拿大', tv_release='2015-8-9')
        tv3 = TV(name='c', serialized='1', tv_type='言情/古装', country='中国', tv_release='2018-8-9')
        tv4 = TV(name='d', serialized='2', tv_type='纪录片', country='中国', tv_release='2014-8-9')
        tv5 = TV(name='e', serialized='1', tv_type='剧情', country='日本', tv_release='2013-8-9')
        db.session.add(tv1)
        db.session.add(tv2)
        db.session.add(tv3)
        db.session.add(tv4)
        db.session.add(tv5)
        db.session.commit()
        r = TV.generate_categories()

        assert len(r['tv_types']) == 6
        assert '剧情' in r['tv_types']
        assert len(r['serialized']) == 4
        assert '1' in r['serialized']
        assert len(r['country']) == 4
        assert '中国' in r['country']
        assert len(r['year']) == 5
        assert '2018' in r['year']
        assert '' in r['year']

    def test_update_detail_for_human(self):
        tv1 = TV(name='a', update_detail='w:1,3,5')
        tv2 = TV(name='a', update_detail='m:1,3,5')
        assert tv1.update_detail_for_human == '周一、周三、周五'
        assert tv2.update_detail_for_human == '1号、3号、5号'

    def test_get_timeline_json(self):
        tv1 = TV(name='a', serialized='1', img_sm='/', new_episode=3, update_detail='w:1')
        tv2 = TV(name='b', serialized='1', img_sm='/', new_episode=4, update_detail='w:2')
        tv3 = TV(name='c', serialized='1', img_sm='/', new_episode=5, update_detail='w:3')
        tv4 = TV(name='d', serialized='1', img_sm='/', new_episode=6, update_detail='w:4')
        tv5 = TV(name='e', serialized='1', img_sm='/', new_episode=7, update_detail='w:5')
        db.session.add(tv1)
        db.session.add(tv2)
        db.session.add(tv3)
        db.session.add(tv4)
        db.session.add(tv5)
        db.session.commit()
        r = TV.get_timeline_json()
        now = datetime.datetime.now()
        m = {0: 'a', 1: 'b', 2: 'c', 3: 'd', 4: 'e'}
        for i in range(-7, 7):
            date = now + datetime.timedelta(days=i)
            week = date.weekday()
            assert r[i+7]['date'] == str(date.month) + '-' + str(date.day)
            if week in m:
                assert r[i+7]['items'][0]['name'] == m[week]


class TestCollection(object):
    @pytest.fixture(autouse=True)
    def transact(self, request):
        app = create_app('testing')
        app_context = app.app_context()
        app_context.push()
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()
        app_context.pop()

    def test_save_load(self):
        u = User(username='dog', password='dog', email='dog@a.com')
        db.session.add(u)
        db.session.commit()
        c = Collection(user_id=u.id, name='w')
        db.session.add(c)
        db.session.commit()
        assert Collection.query.get(1).user_id == u.id

    def test_tv_id_list(self):
        u = User(username='dog', password='dog', email='dog@a.com')
        db.session.add(u)
        db.session.commit()
        c = Collection(user_id=u.id, tv='1;2;3', name='w')
        db.session.add(c)
        db.session.commit()
        assert c.tv_id_list() == ['1', '2', '3']

    def test_add_tv_and_count(self):
        u = User(username='dog', password='dog', email='dog@a.com')
        tv1 = TV(name='a', serialized='1', img_sm='/', new_episode=3, update_detail='w:1')
        tv2 = TV(name='b', serialized='1', img_sm='/', new_episode=4, update_detail='w:2')
        tv3 = TV(name='c', serialized='1', img_sm='/', new_episode=5, update_detail='w:3')
        db.session.add(u)
        db.session.add(tv1)
        db.session.add(tv2)
        db.session.add(tv3)
        db.session.commit()
        c = Collection(user_id=u.id, name='w')
        db.session.add(c)
        db.session.commit()
        c.add_tv(tv1)
        db.session.commit()
        assert c.tv == '1'
        c.add_tv(tv2)
        db.session.commit()
        assert c.tv == '1;2'
        c.add_tv(tv2)
        db.session.commit()
        assert c.tv == '1;2'
        c.add_tv(3)
        db.session.commit()
        assert c.tv == '1;2;3'
        with pytest.raises(ValueError):
            c.add_tv('a')

    def test_remove_tv(self):
        u = User(username='dog', password='dog', email='dog@a.com')
        tv1 = TV(name='a', serialized='1', img_sm='/', new_episode=3, update_detail='w:1')
        tv2 = TV(name='b', serialized='1', img_sm='/', new_episode=4, update_detail='w:2')
        tv3 = TV(name='c', serialized='1', img_sm='/', new_episode=5, update_detail='w:3')
        db.session.add(u)
        db.session.add(tv1)
        db.session.add(tv2)
        db.session.add(tv3)
        db.session.commit()
        c = Collection(user_id=u.id, name='w')
        c.add_tv(tv1)
        c.add_tv(tv2)
        c.add_tv(tv3)
        db.session.commit()
        c.remove_tv(tv1)
        db.session.commit()
        assert c.tv == '2;3'
        c.remove_tv(2)
        db.session.commit()
        assert c.tv == '3'
        with pytest.raises(ValueError):
            c.remove_tv('a')

    def test_save_cover(self):
        # 不好测试
        pass

    def test_contains(self):
        u = User(username='dog', password='dog', email='dog@a.com')
        tv1 = TV(name='a', serialized='1', img_sm='/', new_episode=3, update_detail='w:1')
        db.session.add(u)
        db.session.add(tv1)
        db.session.commit()
        c = Collection(user_id=u.id, name='w')
        c.add_tv(tv1)
        db.session.commit()
        assert c.contains(1) is True
        assert c.contains(tv1) is True
        assert c.contains(33) is False
        assert c.contains('a') is False

    def test_tv_items_list(self):
        u = User(username='dog', password='dog', email='dog@a.com')
        tv1 = TV(name='a', serialized='1', img_sm='/', new_episode=3, update_detail='w:1')
        tv2 = TV(name='b', serialized='1', img_sm='/', new_episode=4, update_detail='w:2')
        tv3 = TV(name='c', serialized='1', img_sm='/', new_episode=5, update_detail='w:3')
        db.session.add(u)
        db.session.add(tv1)
        db.session.add(tv2)
        db.session.add(tv3)
        db.session.commit()
        c = Collection(user_id=u.id, name='w')
        c.add_tv(tv1)
        c.add_tv(tv2)
        c.add_tv(tv3)
        db.session.commit()
        r = c.tv_items_list()
        r_id = [i.id for i in r]
        assert isinstance(r, list)
        assert tv1.id in r_id
        assert tv2.id in r_id
        assert tv3.id in r_id
        assert len(r) == 3

    def test_tv_items_query(self):
        u = User(username='dog', password='dog', email='dog@a.com')
        tv1 = TV(name='a', serialized='1', img_sm='/', new_episode=3, update_detail='w:1')
        tv2 = TV(name='b', serialized='1', img_sm='/', new_episode=4, update_detail='w:2')
        tv3 = TV(name='c', serialized='1', img_sm='/', new_episode=5, update_detail='w:3')
        db.session.add(u)
        db.session.add(tv1)
        db.session.add(tv2)
        db.session.add(tv3)
        db.session.commit()
        c = Collection(user_id=u.id, name='w')
        c.add_tv(tv1)
        c.add_tv(tv2)
        c.add_tv(tv3)
        db.session.commit()
        r = c.tv_items_query()
        assert isinstance(r, BaseQuery)
        for i in r.all():
            assert i in c.tv_items_list()


class TestHistoryTV(object):
    @pytest.fixture(autouse=True)
    def transact(self, request):
        app = create_app('testing')
        app_context = app.app_context()
        app_context.push()
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()
        app_context.pop()

    def test_watched_ep_to_list(self):
        u = User(username='dog', password='dog', email='dog@a.com')
        tv1 = TV(name='a', serialized='1', img_sm='/', new_episode=3, update_detail='w:1')
        db.session.add(u)
        db.session.add(tv1)
        db.session.commit()
        h = HistoryTV(user_id=u.id, tv_id=tv1.id, watched_episodes='1;2;3;4;5')
        assert h.watched_ep_to_list == ['1', '2', '3', '4', '5']

    def test_watched_to(self):
        u = User(username='dog', password='dog', email='dog@a.com')
        tv1 = TV(name='a', serialized='1', img_sm='/', new_episode=3, update_detail='w:1')
        tv2 = TV(name='b', serialized='1', img_sm='/', new_episode=4, update_detail='w:2')
        db.session.add(u)
        db.session.add(tv1)
        db.session.add(tv2)
        db.session.commit()
        h = HistoryTV(user_id=u.id, tv_id=tv1.id, watched_episodes='1;2;3;4;5')
        db.session.add(h)
        db.session.commit()
        assert HistoryTV.watched_to(u, tv1) == '5'
        assert HistoryTV.watched_to(u, tv2) is None

    def test_is_finished(self):
        u = User(username='dog', password='dog', email='dog@a.com')
        tv1 = TV(name='a', serialized='1', img_sm='/', new_episode=4, update_detail='w:1')
        tv2 = TV(name='b', serialized='1', img_sm='/', new_episode=4, update_detail='w:2')
        db.session.add(u)
        db.session.add(tv1)
        db.session.add(tv2)
        db.session.commit()
        h = HistoryTV(user_id=u.id, tv_id=tv1.id, watched_episodes='1;2;3;4;5')
        db.session.add(h)
        db.session.commit()
        assert HistoryTV.is_finished(u, tv1) is True
        assert HistoryTV.is_finished(u, tv2) is False

    def test_on_change_watched(self):
        u = User(username='dog', password='dog', email='dog@a.com')
        tv1 = TV(name='a', serialized='1', img_sm='/', episodes=4, new_episode=4,
                 update_detail='w:1')
        db.session.add(u)
        db.session.add(tv1)
        db.session.commit()
        h = HistoryTV(user_id=u.id, tv_id=tv1.id, watched_episodes='1;2;3',
                      timestamp_watched=datetime.datetime(2019, 1, 1))
        db.session.add(h)
        db.session.commit()
        assert HistoryTV.watched_to(u, tv1) == '3'
        assert h.finished is False
        assert h.timestamp_watched < datetime.datetime.now()
        h.watched_episodes = '1;2;3;4'
        db.session.add(h)
        db.session.commit()
        assert HistoryTV.watched_to(u, tv1) == '4'
        assert h.finished is True
        assert datetime.datetime.now() - h.timestamp_watched < datetime.timedelta(days=1)
