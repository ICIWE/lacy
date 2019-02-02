# -*- coding: utf-8 -*-
# @author: NiHao

from flask import render_template, flash, redirect, url_for, request
from sqlalchemy import or_
from flask_login import current_user, login_required, login_user, logout_user
from . import auth
from .form import SignupForm, LoginForm, ModifyPasswordForm, PasswordResetEmailForm, PasswordResetForm, ModifyEmailForm
from ..models import User
from .. import db
from ..email import send_email


@auth.before_app_request
def before_request():
    # 登录后，未确认邮件的用户，会一直有确认提醒
    if current_user.is_authenticated and \
            not current_user.confirmed and \
            request.blueprint != 'auth' and request.endpoint != 'static':
        return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    # 未确认邮件的用户，会一直有提醒
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    # 登录页面
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash('登录成功')
            next_page = request.args.get('next')

            # 验证next 为相对url
            if next_page is None or not next_page.startswith('/'):
                next_page = url_for('main.index')
            return redirect(next_page)
        else:
            flash('用户名或密码错误！')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    # 退出登录
    logout_user()
    flash('您已退出登录。')
    return redirect(url_for('main.index'))


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    # 注册页面
    form = SignupForm()
    if form.validate_on_submit():
        users = User.query.filter(or_(User.username == form.username.data, User.email == form.email.data))

        if users.filter_by(username=form.username.data).first() is not None:
            flash('此用户名已被使用！')
        elif users.filter_by(email=form.email.data).first() is not None:
            flash('此邮箱已绑定用户！')
        else:
            user = User(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data
            )
            db.session.add(user)
            db.session.commit()
            token = user.generate_confirm_token()
            try:
                send_email(user.email, 'Lacy 注册确认', 'auth/email/confirm', user=user, token=token)
                flash('确认邮件已发送至您的邮箱，请确认邮箱以完成注册！')
            except:
                # ----------------logging------------------------------------------------------------------------------
                flash('发送出错！请登录后再选择重新发送。')
            return redirect(url_for('main.index'))
    return render_template('auth/signup.html', form=form)


@auth.route('/confirm')
def confirm():
    # 邮件确认视图
    user_id = request.args.get('user')
    user = User.query.filter_by(id=user_id).first()
    if not user or not user.confirm_token(request.args.get('token')) or not user.confirmed:
        msg = '验证链接错误或者已失效。'
    else:
        db.session.commit()
        msg = '邮箱验证成功！'
    return render_template('auth/confirm_email.html', msg=msg)


@auth.route('/confirm_')
@login_required
def resend_confirm_email():
    # 重新发送确认邮件
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    user = current_user
    token = user.generate_confirm_token()
    send_email(user.email, 'Lacy 注册确认', 'auth/email/confirm', user=user, token=token)
    flash('确认邮件已发送至您的邮箱，请确认邮箱以完成注册！')
    return redirect(url_for('main.index'))


@auth.route('/modify/password', methods=['GET', 'POST'])
@login_required
def modify_password():
    # 账户密码
    form = ModifyPasswordForm()
    if form.validate_on_submit():
        user = current_user._get_current_object()
        if user.check_password(form.old_password.data):
            user.password = form.new_password.data
            db.session.add(user)
            db.session.commit()
            flash('密码修改成功！')
            flash('请以新密码重新登录。')
            return redirect(url_for('auth.login'))
        flash('原密码输入错误！')
    return render_template('auth/modify.html', form=form)


@auth.route('/modify/email', methods=['GET', 'POST'])
@login_required
def modify_email_request():
    # 修改绑定邮箱页面
    form = ModifyEmailForm()
    if form.validate_on_submit():
        new_email = form.new_email.data
        if not current_user.check_password(form.password.data):
            flash('密码验证错误！')
        else:
            user = User.query.filter_by(email=new_email).first()
            if user:
                flash('此邮箱已绑定账户。')
            else:
                token = current_user.generate_modify_email_token(new_email)
                send_email(new_email, 'Lacy 更改邮箱', 'auth/email/modify_email',
                           user=current_user, token=token)
                flash('更改邮箱的确认邮件已经发往您的 新邮箱 ！', category='success')
                return redirect(url_for('main.index'))
    return render_template('auth/modify_email.html', form=form)


@auth.route('/modify/email/<token>')
@login_required
def modify_email(token):
    # 修改邮箱确认视图
    if current_user.modify_email(token):
        db.session.commit()
        logout_user()
        flash('邮箱修改成功！')
        flash('请重新登录！')
        return redirect(url_for('auth.login'))
    else:
        flash('验证失败！')
    return redirect(url_for('main.index'))


@auth.route('/password_reset', methods=['GET', 'POST'])
def password_reset_request():
    # 重置密码请求
    form = PasswordResetEmailForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user:
            flash('邮箱验证错误！')
        else:
            token = user.generate_reset_token()
            send_email(user.email, 'Lacy 密码重置', 'auth/email/password_reset', user=user, token=token)
            flash('密码重置邮件已发送至您的邮箱，请注意查收。')
            return redirect(url_for('auth.login'))
    return render_template('auth/password_reset.html', form=form)


@auth.route('/password_reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    # 重置密码
    form = PasswordResetForm()
    if form.validate_on_submit():
        if User.reset_password(token, form.new_password.data):
            db.session.commit()
            flash('密码重置成功！')
            return redirect(url_for('auth.login'))
        else:
            flash('验证失败！')
            return redirect(url_for('main.index'))
    return render_template('auth/password_reset.html', form=form)
