# -*- coding: utf-8 -*-
# @author: NiHao

import re
from datetime import datetime
from urllib import parse
from flask import render_template, url_for, redirect, session, flash, request, current_app, jsonify
from flask_login import current_user, login_required
from flask_sqlalchemy import get_debug_queries
from . import main
from ..models import TV, HistoryTV, Collection
from ..search import Search
from .. import db


@main.before_app_first_request
def search_initialize():
    # 初始化搜索，将搜索函数绑定到 current_app
    _search = Search(current_app.config['SEARCH_BLOOM_FILTER_SIZE'])
    _search.auto_add_events(db=db, TV=TV)
    current_app._search = _search


@main.route('/')
def index():
    # 首页
    tv = TV.query.filter_by(serialized=1).order_by(TV.new_date.desc()).all()[:15]
    my_list = []
    if current_user.is_authenticated:
        subs_list = current_user.subscribed_tv.all()
        if len(subs_list) > 7:
            subs_list = subs_list[:7]
        my_list = [item.subscribed_tv for item in subs_list]
    return render_template('index.html', HistoryTV=HistoryTV, new_items=tv, mylist=my_list)


@main.route('/subscribe/<int:tv_id>', methods=['POST', 'DELETE'])
@login_required
def subscribe(tv_id):
    # 订阅 / 取消订阅
    tv = TV.query.filter_by(id=tv_id).first()
    if not tv:
        return jsonify({'code': 404, 'message': '未知'})
    if request.method == 'POST':
        if current_user.tv_is_subscribed(tv):
            return jsonify({'code': -1, 'message': '不能重复订阅'})
        current_user.subscribe_tv(tv)
        db.session.commit()
        return jsonify({'code': 0, 'message': '成功'})
    if request.method == 'DELETE':
        if not current_user.tv_is_subscribed(tv):
            return jsonify({'code': -2, 'message': '项目不存在'})
        current_user.unsubscribe_tv(tv)
        db.session.commit()
        return jsonify({'code': 0, 'message': '成功'})


@main.route('/storeUp/<int:c_id>', methods=['POST', 'DELETE'])
@login_required
def store_collection(c_id):
    # 收藏其他人的清单
    col = Collection.query.filter_by(id=c_id).first()
    if not col:
        return jsonify({'code': 404, 'message': '未知'})
    if col.user_id == current_user.id:
        return jsonify({'code': -2, 'message': '收藏失败'})
    if request.method == 'POST':
        if current_user.col_is_store_up(col):
            return jsonify({'code': -1, 'message': '不能重复订阅'})
        current_user.store_up_col(col)
        db.session.commit()
        return jsonify({'code': 0, 'message': '成功'})
    if request.method == 'DELETE':
        if not current_user.col_is_store_up(col):
            return jsonify({'code': -2, 'message': '项目不存在'})
        current_user.un_store_up_col(col)
        db.session.commit()
        return jsonify({'code': 0, 'message': '成功'})


@main.route('/march/<int:tv_id>', methods=['POST', 'DELETE'])
@login_required
def march(tv_id):
    tv = TV.query.filter_by(id=tv_id).first()
    if not tv:
        return jsonify({'code': 404, 'message': '未知'})
    h = HistoryTV.query.filter_by(user_id=current_user.id, tv_id=tv_id).first()

    if request.method == 'POST':
        if h:
            if h.finished:
                return jsonify({'code': -1, 'message': '数据错误'})
            h.finished = True
        else:
            h = HistoryTV(user_id=current_user.id, tv_id=tv_id, finished=True)
        db.session.add(h)
        db.session.commit()
        if current_user.tv_is_subscribed(tv):   # 已看完节目, 取消订阅
            current_user.unsubscribe_tv(tv)
            db.session.commit()
        return jsonify({'code': 0, 'message': '成功'})
    if request.method == 'DELETE':
        if not h or not h.finished:
            return jsonify({'code': -1, 'message': '数据错误'})
        else:
            h.finished = False
            db.session.add(h)
            db.session.commit()
        return jsonify({'code': 0, 'message': '成功'})


@main.route('/subscribelist')
@login_required
def subscribe_list():
    # 追剧清单
    my_lists = []
    my_cs = []
    pagination = None
    if current_user.is_anonymous:
        return render_template('subscribe_list.html')
    if current_user.is_authenticated and current_user.confirmed:
        page = request.args.get('page', 1, type=int)

        # 排序。1：最近更新，2：最近观看，默认 1
        sort = int(request.args.get('sort', 1))
        query = current_user.subscribed_tv_order_by_update()
        if sort and sort == 2:
            query = current_user.subscribed_tv_order_by_watched()
        pagination = query.paginate(page, per_page=8)
        my_lists = [{'tv': item.subscribed_tv, 'remind': item.remind,
                     'finished': item.finished, 't': item.timestamp} for item in pagination.items]
        my_cs = Collection.query.filter_by(user_id=current_user.id).all()
    return render_template('subscribe_list.html', mylists=my_lists, pagination=pagination,
                           HistoryTV=HistoryTV, my_cs=my_cs)


@main.route('/watchedlist')
@login_required
def watched_list():
    # 已经看完的tv
    if current_user.is_authenticated:
        query = TV.query.join(HistoryTV, TV.id == HistoryTV.tv_id).\
            filter(HistoryTV.user_id == current_user.id, HistoryTV.finished == True).\
            order_by(HistoryTV.timestamp_watched.desc())
        page = request.args.get('page', 1, type=int)
        pagination = query.paginate(page, per_page=8, error_out=False)
        finished_tv = pagination.items
        my_cs = Collection.query.filter_by(user_id=current_user.id).all()
        return render_template('watched_list.html', finished_tv=finished_tv, pagination=pagination,
                               my_cs=my_cs)


@main.route('/subscribelist/<int:collection_id>')
def collection_list(collection_id):
    # 已创建的清单
    my_cs = []
    my_c = Collection.query.filter_by(id=collection_id).first_or_404()
    query = my_c.tv_items_query()
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page, per_page=8, error_out=False)
    tv_list = pagination.items
    if current_user.is_authenticated:
        my_cs = Collection.query.filter_by(user_id=current_user.id).all()
    return render_template('collection.html', my_cs=my_cs, my_c=my_c,
                           tv_list=tv_list, pagination=pagination, HistoryTV=HistoryTV)


@main.route('/collectionCreate/<string:title>')
@login_required
def collection_create(title):
    # 创建收藏清单
    c = Collection.query.filter_by(user_id=current_user.id, name=title).first()
    if c:
        flash('已创建同名清单', category='info')
        return redirect(url_for('main.index'))
    c = Collection(user_id=current_user.id, name=title)
    db.session.add(c)
    db.session.commit()
    flash('清单创建成功', category='success')
    c = Collection.query.filter_by(user_id=current_user.id, name=title).first()

    tv_id = request.args.get('tv_id')

    if len(tv_id) > 0:
        tv = TV.query.filter_by(id=int(tv_id)).first_or_404()
        if c.tv:
            c.tv = c.tv + ';' + str(tv_id)
        else:
            c.tv = str(tv_id)
        db.session.add(c)
        db.session.commit()
        flash('添加成功', category='success')
    return redirect(url_for('main.collection_list', collection_id=c.id))


@main.route('/collectionDelete/<int:cid>')
@login_required
def collection_delete(cid):
    # 删除收藏清单
    c = Collection.query.filter_by(id=cid).first_or_404()
    db.session.delete(c)
    db.session.commit()
    flash('清单已删除', category='success')
    return redirect(url_for('main.subscribe_list'))


@main.route('/j/collection/item', methods=['POST', 'DELETE'])
@login_required
def collection_item():
    # 在清单中添加、删除tv
    data = request.get_json()
    if not data:
        return jsonify({'code': 404, 'message': '未知'})
    if not data.get('c_id') or not data.get('tv_id'):
        return jsonify({'code': -1, 'message': '数据错误'})
    c = Collection.query.filter_by(id=int(data.get('c_id')), user_id=current_user.id).first()
    tv_id = int(data.get('tv_id'))
    tv = TV.query.filter_by(id=tv_id).first()
    if not c or not tv:
        return jsonify({'code': -1, 'message': '数据错误'})

    if request.method == 'POST':
        if c.contains(int(tv_id)):
            return jsonify({'code': -3, 'message': '不能重复添加'})
        if c.tv:
            c.tv = c.tv + ';' + str(tv_id)
        else:
            c.tv = str(tv_id)
        db.session.add(c)
        db.session.commit()
        return jsonify({'code': 0, 'message': '成功'})
    if request.method == 'DELETE':
        if not c.contains(int(tv_id)):
            return jsonify({'code': -3, 'message': '项目不存在'})
        c.remove_tv(tv)
        db.session.commit()
        return jsonify({'code': 0, 'message': '成功'})


@main.route('/j/collectionModify', methods=['POST'])
@login_required
def collection_modify():
    # 需添加用户输入的安全验证 ========================================================================
    if request.get_json():
        data = request.get_json()
        if not data.get('id'):
            return jsonify({'code': -1, 'message': '数据错误'})
        c = Collection.query.filter_by(id=data.get('id'), user_id=current_user.id).first()
        if not c:
            return jsonify({'code': -2, 'message': '项目不存在'})
        if c.name == data.get('name'):
            return jsonify({'code': -3, 'message': '名称重复'})
        if data.get('name') and data.get('name').strip() is not None:
            c.name = data.get('name')
        if data.get('summery') and data.get('summery').strip() is not None:
            c.description = data.get('summery')
        db.session.add(c)
        db.session.commit()
        return jsonify({'code': 0, 'message': '成功'})
    if request.files:
        img = request.files.get('file')
        cid = request.form.get('id')
        if not img or not cid:
            return jsonify({'code': -1, 'message': '数据错误'})
        c = Collection.query.filter_by(id=cid, user_id=current_user.id).first()
        if not c:
            return jsonify({'code': -2, 'message': '项目不存在'})
        c.save_cover(img)
        db.session.commit()
        return jsonify({'code': 0, 'message': '成功'})
    return jsonify({'code': 404, 'message': '未知'})


@main.route('/tvdetail/<int:tv_id>')
def tv_detail(tv_id):
    tv = TV.query.filter_by(id=tv_id).first_or_404()
    watched_episodes = []
    history_tv = {}
    my_cs = []
    if current_user.is_authenticated:
        history_tv = HistoryTV.query.filter_by(user_id=current_user.id, tv_id=tv.id).first()
        if history_tv is not None:
            watched_episodes = history_tv.watched_ep_to_list
            watched_episodes = [int(i) for i in watched_episodes]
        my_cs = Collection.query.filter_by(user_id=current_user.id).all()
    return render_template('tv_detail.html', tv=tv, history_tv=history_tv,
                           watched_episodes=watched_episodes, my_cs=my_cs)


@main.route('/history/ep/<tv_id>', methods=['POST'])
@login_required
def modify_history_ep(tv_id):
    # 修改tv 已观看的集数
    episodes_submit = request.form.getlist('episodes')
    tv = TV.query.filter_by(id=tv_id).first()
    if tv is None:
        flash('项目不存在', category='error')
        return redirect(url_for('main.tv_detail', id=tv.id))
    if len(episodes_submit) == tv.episodes:
        finished = True
    else:
        finished = False
    episodes_submit = ';'.join(episodes_submit)
    history_tv = HistoryTV.query.filter_by(user_id=current_user.id, tv_id=tv.id).first()
    if history_tv is None:
        history_tv = HistoryTV(user_id=current_user.id, tv_id=id,
                               watched_episodes=episodes_submit, finished=finished)
    else:
        history_tv.watched_episodes = episodes_submit
        history_tv.finished = finished
    db.session.add(history_tv)
    db.session.commit()
    flash('添加成功', category='success')
    return redirect(url_for('main.tv_detail', tv_id=tv.id))


@main.route('/timeline')
def timeline():
    return render_template('timeline.html')


@main.route('/category')
def category():
    # 分类查看tv
    page = request.args.get('page', 1, type=int)

    serialized = request.args.get('serialized', '')
    tv_type = request.args.get('tv_type', '')
    country = request.args.get('country', '')
    year = request.args.get('year', '')

    categories = TV.generate_categories()
    tv_query = TV.tv_category(serialized=serialized, tv_type=tv_type, country=country, year=year)
    pagination = tv_query.paginate(page, per_page=36, error_out=False)
    tv = pagination.items
    count = tv_query.count()
    if count == 0:
        flash('未找到相关数据，请尝试其他关键字。', category='info')
    return render_template('category.html', categories=categories, tv=tv, pagination=pagination)


@main.route('/search')
def search():
    # 搜索    -- 搜索效率可以考虑提高 ------------------------------
    key = request.args.get('key', '').strip()
    results_id = current_app._search.search(key)
    results = []
    if len(results_id) > 0:
        for tv_id in results_id:
            tv = TV.query.filter_by(id=tv_id).first()
            results.append(tv)
    return render_template('search.html', results=results, key=key)


@main.route('/j/timeline')
def json_timeline():
    result = TV.get_timeline_json()
    return jsonify({
        'code': 0,
        'message': 'success',
        'result': result
    })


# 测试用x
@main.route('/test', methods=['GET', 'POST'])
def test():
    print(request.args.get('sad'))
    print(len(request.args))
    return render_template('demo.html')


# @main.after_app_request
# def after_app_request(response):
#     for query in get_debug_queries():
#         current_app.logger.warning(
#             'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n'
#             % (query.statement, query.parameters, query.duration,
#                query.context)
#         )
#     return response
