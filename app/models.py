# -*- coding: utf-8 -*-
# @author: NiHao

import re
import datetime
from sqlalchemy import and_, any_, or_, UniqueConstraint
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask_login import UserMixin
from . import login_manager
from . import db


class ActionLog(db.Model):
    __tablename__ = 'action_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.Text)     # 'action;target_type:target_id;detail:detail'
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class StoreUp(db.Model):
    __tablename__ = 'store'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    c_id = db.Column(db.Integer, db.ForeignKey('collections.id'))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    user = db.relationship('User', back_populates='store_up')
    col = db.relationship('Collection', back_populates='store_by')
    __table_args__ = (UniqueConstraint('user_id', 'c_id'),)

    def __repr__(self):
        return '<StoreUp id=%s, user_id=%s, c_id=%s>' % (self.id, self.user_id, self.c_id)


class Collection(db.Model):
    __tablename__ = 'collections'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    cover = db.Column(db.String(128))
    tv = db.Column(db.Text)     # 'tv_id;tv_id;tv_id'
    description = db.Column(db.Text)
    create_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    store_by = db.relationship('StoreUp', back_populates='col', lazy='dynamic')
    __table_args__ = (UniqueConstraint('user_id', 'name'),)

    def __repr__(self):
        return '<Collection name=%s, user_id=%s>' % (self.name, self.user_id)

    @property
    def count(self):
        # 本清单中收录的电视剧数量
        if not self.tv:
            return 0
        id_list = self.tv.split(';')
        return len(set(id_list))

    def add_tv(self, tv):
        # 添加tv
        id_list = self.tv_id_list()
        if isinstance(tv, int):
            tv_id = tv
        elif isinstance(tv, TV):
            tv_id = tv.id
        else:
            raise ValueError
        if str(tv_id) not in id_list:
            id_list.append(str(tv_id))
            self.tv = ';'.join(id_list)
            db.session.add(self)
            return True
        return False

    def remove_tv(self, tv):
        # 删除tv
        id_list = self.tv_id_list()
        if isinstance(tv, int):
            tv_id = tv
        elif isinstance(tv, TV):
            tv_id = tv.id
        else:
            raise ValueError
        if str(tv_id) in id_list:
            id_list.remove(str(tv_id))
            self.tv = ';'.join(id_list)
            db.session.add(self)
            return True
        return False

    def save_cover(self, img):

        path = current_app.config['COVER_STORE_PATH'] + 'cover/'
        ends = img.filename.split('.')[-1]
        t = datetime.datetime.timestamp(datetime.datetime.now())
        m = '0' * (6 - len(str(self.id))) + str(self.id) + str(t * 1000000)
        if ends in ['jpg', 'png']:
            name = m + '.' + ends
        else:
            name = m + '.jpg'
        self.cover = path + name
        img.save(self.cover)
        db.session.add(self)

    def contains(self, tv):
        # 判断本 collection 中是否包含 tv（TV实例 或 tv id）
        id_list = self.tv_id_list()
        if isinstance(tv, int):
            return str(tv) in id_list
        elif isinstance(tv, TV):
            return str(tv.id) in id_list
        else:
            return False

    def tv_id_list(self):
        # 将 ; 分割的 tv_id 装换成 id 列表
        if not self.tv:
            return []
        return self.tv.split(';')

    def tv_items_list(self):
        # 将； 分割的tv 字符串，转换为TV 实例的列表
        r = []
        id_list = self.tv_id_list()
        for _id in id_list:
            tv = TV.query.filter_by(id=_id).first()
            if not tv:
                break
            r.append(tv)
        return r

    def tv_items_query(self):
        # 将； 分割的tv 字符串，转换为TV 的query 对象
        id_list = self.tv_id_list()
        return TV.query.filter(TV.id.in_(id_list))


class HistoryTV(db.Model):
    # 用户的TV 观看历史
    __tablename__ = 'history_tv'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    tv_id = db.Column(db.Integer, db.ForeignKey('tv.id'))
    watched_episodes = db.Column(db.Text, default='')
    timestamp_watched = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    finished = db.Column(db.Boolean, default=False)

    watched_by = db.relationship('User', back_populates='tv_histories')
    tv_history = db.relationship('TV', back_populates='watched_by')
    __table_args__ = (UniqueConstraint('user_id', 'tv_id'),)

    def __repr__(self):
        return '<HistoryTV user_id=%s, tv_id=%s>' % (self.user_id, self.tv_id)

    @property
    def watched_ep_to_list(self):
        # 已观看的集数，转换为 list
        return self.watched_episodes.split(';')

    @staticmethod
    def watched_to(user, tv):
        # 观看至，已观看的最大集数
        h = user.tv_histories.filter_by(tv_id=tv.id).first()
        if not h or len(h.watched_episodes) < 1:
            return
        else:
            return max(h.watched_ep_to_list)

    @staticmethod
    def is_finished(user, tv):
        h = user.tv_histories.filter_by(tv_id=tv.id).first()
        if not h or not h.finished:
            return False
        return h.finished is True

    @staticmethod
    def on_change_watched(target, value, oldvalue, initiator):
        target.timestamp_watched = datetime.datetime.utcnow()
        tv = TV.query.filter_by(id=target.tv_id).first()
        li = value.split(';')
        if tv and len(li) >= tv.episodes and int(max(li)) >= tv.episodes:
            target.finished = True


# 监听watched_episodes 修改，更新timestamp_watched 和 finished 。
db.event.listen(HistoryTV.watched_episodes, 'set', HistoryTV.on_change_watched)


class Subscription(db.Model):
    __tablename__ = 'subs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    tv_id = db.Column(db.Integer, db.ForeignKey('tv.id'))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    remind = db.Column(db.Integer, default=0)   # 更新提醒
    finished = db.Column(db.Boolean, default=False)    # 已看完

    subscribed_by = db.relationship('User', back_populates='subscribed_tv')
    subscribed_tv = db.relationship('TV', back_populates='subscribed_by')
    __table_args__ = (UniqueConstraint('user_id', 'tv_id'),)

    def __repr__(self):
        return '<Subscription user_id=%s, tv_id=%s>' % (self.user_id, self.tv_id)


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)

    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %s>' % self.name


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    email = db.Column(db.String(128), unique=True, index=True)
    phone_number = db.Column(db.String(32), unique=True)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    member_since = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    about_me = db.Column(db.Text)
    icon = db.Column(db.Text)

    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    ''' cascade='all, delete-orphan' 参数加不加？ 默认：删除对象后，相关对象的值设为空；
    加上后：删除对象，相关对象的实体记录也删除 '''
    subscribed_tv = db.relationship('Subscription', back_populates='subscribed_by', lazy='dynamic')

    tv_histories = db.relationship('HistoryTV', back_populates='watched_by', lazy='dynamic')    # 返回 HistoryTV 实例

    collections = db.relationship('Collection', backref='owner', lazy='dynamic')
    action_log = db.relationship('ActionLog', backref='owner', lazy='dynamic')

    store_up = db.relationship('StoreUp', back_populates='user', lazy='dynamic')

    def __repr__(self):
        return '<User %s>' % self.username

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirm_token(self, expires_in=3600):
        # 生成验证邮箱的令牌
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expires_in)
        return s.dumps({'confirm': self.username}).decode('utf-8')

    def confirm_token(self, token):
        # 确认验证邮箱的令牌
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except Exception:
            return False
        if data.get('confirm') != self.username:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expires_in=3600):
        # 生成密码重置令牌
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expires_in)
        return s.dumps(
            {'reset': self.id, 'old_pwh': self.password_hash}).decode('utf-8')

    @staticmethod
    def reset_password(token, new_password):
        # 确认令牌，重置密码
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except Exception as e:
            return False
        user = User.query.filter_by(id=data.get('reset')).first()
        if user is None:
            return False
        if user.password_hash == data.get('old_pwh'):
            user.password = new_password
            db.session.add(user)
            return True

    def generate_modify_email_token(self, new_email, expires_in=3600):
        # 生成修改邮箱的令牌
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expires_in)
        return s.dumps({
            'modify_email': self.id, 'new_email': new_email}).decode('utf-8')

    def modify_email(self, token):
        # 验证令牌，修改邮箱
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('modify_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None or User.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        return True

    def generate_auth_token(self, expiration=3600):
        # api 生成身份认证信息
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id}).decode('utf-8')

    @staticmethod
    def verify_auth_token(token):
        # api 验证身份信息，并返回user 对象
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return None
        return User.query.get(data['id'])

    def subscribe_tv(self, tv):
        # 订阅tv
        if not self.tv_is_subscribed(tv):
            sub = Subscription(user_id=self.id, tv_id=tv.id)
            db.session.add(sub)
            return True
        return False

    def unsubscribe_tv(self, tv):
        # 取消订阅
        sub = self.subscribed_tv.filter_by(tv_id=tv.id).first()
        if sub:
            db.session.delete(sub)
            db.session.add(self)
            return True
        return False

    def tv_is_subscribed(self, tv):
        # 判断是否已订阅
        if isinstance(tv, int):
            tv_id = tv
        elif isinstance(tv, TV):
            tv_id = tv.id
        else:
            return False
        return self.subscribed_tv.filter_by(tv_id=tv_id).first() is not None

    def store_up_col(self, col):
        if not self.col_is_store_up(col):
            store = StoreUp(user_id=self.id, c_id=col.id)
            db.session.add(store)
            return True
        return False

    def un_store_up_col(self, col):
        store = self.store_up.filter_by(c_id=col.id).first()
        if store:
            db.session.delete(store)
            db.session.add(self)
            return True
        return False

    def col_is_store_up(self, col):
        if isinstance(col, int):
            c_id = col
        elif isinstance(col, Collection):
            c_id = col.id
        else:
            return False
        return self.store_up.filter_by(c_id=c_id).first() is not None

    @property
    def watched_tv(self):
        # 返回 TV 的query 对象
        return TV.query.join(HistoryTV, HistoryTV.tv_id == TV.id).filter(HistoryTV.user_id == self.id)

    def subscribed_tv_order_by_update(self):
        # 返回按照 更新时间排序的 订阅清单的查询对象
        return Subscription.query.outerjoin(TV, Subscription.tv_id == TV.id).filter(Subscription.user_id == self.id).\
            order_by(TV.new_date.desc())

    def subscribed_tv_order_by_watched(self):
        # 返回按照 观看时间排序的 订阅清单的查询对象
        return Subscription.query.outerjoin(
            HistoryTV, and_(HistoryTV.tv_id == Subscription.tv_id, HistoryTV.user_id == Subscription.user_id)).\
            filter(Subscription.user_id == self.id).order_by(HistoryTV.timestamp_watched.desc())


@login_manager.user_loader
def load_user(userid):
    # 加载用户的回调函数，参数 userid 为Unicode类型。
    return User.query.get(int(userid))


class TV(db.Model):
    __tablename__ = 'tv'
    id = db.Column(db.Integer, primary_key=True)
    douban_id = db.Column(db.Integer, unique=True)
    name = db.Column(db.String(64), nullable=False, unique=True)
    score = db.Column(db.Numeric(3, 1), default=0)
    item_type = db.Column(db.String(8), default='tv')
    tv_type = db.Column(db.String(64))
    stars = db.Column(db.Text)
    director = db.Column(db.String(64), default='无')
    country = db.Column(db.String(32))
    tv_release = db.Column(db.String(64), default='未知')  # 上映时间（地区)
    episodes = db.Column(db.Integer, default=0)     # 集数, -1: 未知
    alias = db.Column(db.String(64))    # 别名
    summery = db.Column(db.Text)
    img_sm = db.Column(db.String(128))  # 小图路径
    img_lg = db.Column(db.String(128))  # 大图路径
    new_episode = db.Column(db.Integer)     # 更新至第几集
    new_date = db.Column(db.Date())         # 更新日期
    update_detail = db.Column(db.String(64))    # 更新详情 周更'w:1,7' ，月更'm:1,31'，其他'o:更新详情（text）'
    serialized = db.Column(db.String(8), default='0')   # 0-未知；1-连载；2-完结；3-未开播  # 此处使用字符串，是为了匹配时更加方便

    subscribed_by = db.relationship('Subscription', back_populates='subscribed_tv', lazy='dynamic')

    watched_by = db.relationship('HistoryTV', back_populates='tv_history', lazy='dynamic')

    def __repr__(self):
        return '<TV id=%s, name=%s>' % (self.id, self.name)

    # def tv_is_serialized(self):
    #     if self.new_episode is None and self.episodes is None:
    #         self.serialized = 0
    #     elif self.episodes == 0:
    #         self.serialized = 3
    #     elif self.episodes =< self.new_episode:
    #         self.serialized = 2
    #     else:
    #         self.serialized = 1

    @staticmethod
    def tv_category(serialized='', tv_type='', country='', year=''):
        # 根据不同的分类标签查询电视剧，返回query 对象
        serialized = '%' + str(serialized) + '%'    # 此处使用字符串，是为了匹配所有情况
        tv_type = '%' + str(tv_type) + '%'
        country = '%' + str(country) + '%'
        year = '%' + str(year) + '%'
        tv_query = TV.query.filter(TV.serialized.like(serialized)).filter(TV.tv_type.like(tv_type)).\
            filter(TV.country.like(country)).filter(TV.tv_release.like(year))
        return tv_query

    @staticmethod
    def generate_categories():
        # 生成电视剧分类标签
        categories = {}

        tv_type_set = set()
        result = db.session.query(TV.tv_type).all()
        for item in result:
            if item[0] is None:
                continue
            type_ = [x.strip() for x in item[0].split('/')]
            tv_type_set.update(type_)
        tv_type_list = list(tv_type_set)
        tv_type_list.append('')     # 此处 '' 表示匹配全部
        tv_type_list.sort()

        country_set = set()
        result = db.session.query(TV.country).all()
        for item in result:
            if item[0] is None:
                continue
            country_ = [x.strip() for x in item[0].split('/')]
            country_set.update(country_)
        country_list = list(country_set)
        country_list.append('')
        country_list.sort()

        year_set = set()
        result = db.session.query(TV.tv_release).all()
        for item in result:
            if item[0] is None:
                continue
            r = re.search('(\d{4})-', item[0])
            if not r:
                continue
            year_ = [r.group(1)]
            year_set.update(year_)
        year_list = list(year_set)
        year_list.append('')
        year_list.sort()

        categories['tv_types'] = tv_type_list
        categories['serialized'] = ['', '1', '2', '3']
        categories['country'] = country_list
        categories['year'] = year_list
        return categories

    @property
    def update_detail_for_human(self):
        # 将更新详情转换为容易理解的形式。 'w:1,2' --> '周一、周二'
        week = {'1': '一', '2': '二', '3': '三', '4': '四', '5': '五', '6': '六', '7': '日'}
        s = self.update_detail
        result = ''
        if s.find(':') != s.rfind(':'):
            raise ValueError
        [t, v] = s.split(':')
        if len(v) <= 0:
            raise ValueError
        if t == 'w':
            for i in v.split(','):
                result = result + '周%s、' % week.get(i)
            result = result[:-1]
        elif t == 'm':
            for i in v.split(','):
                result = result + '%s号、' % i
            result = result[:-1]
        elif t == 'o':
            result = v
        return result

    @property
    def is_finished(self):
        # 是否完结
        return self.new_episode >= self.episodes

    @staticmethod
    def get_timeline_json():
        # 仅考虑周更 ------------------------------------------
        tv = TV.query.filter_by(serialized='1').all()
        update_map = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: []}  # 0: 周一
        for item in tv:
            s = item.update_detail
            if s.find(':') != s.rfind(':'):
                raise ValueError
            v = s.split(':')[1]
            if len(v) <= 0:
                raise ValueError

            item_dict = {
                'cover': item.img_sm,
                'delay': 0,
                'last_ep': item.new_episode,
                'name': item.name,
                'url': '/tvdetail/%s' % str(item.id)
            }
            for i in v.split(','):
                if int(i) - 1 in update_map:
                    update_map[int(i) - 1].append(item_dict)

        result = []
        now = datetime.datetime.now()
        for i in range(-7, 7):
            date = now + datetime.timedelta(days=i)
            week = date.weekday()
            items = {'date': str(date.month) + '-' + str(date.day),
                     'date_ts': int(now.timestamp()),
                     'day_of_week': week,
                     'is_today': date == now,
                     'items': update_map[week]}
            result.append(items)
        return result
