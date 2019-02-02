# -*- coding: utf-8 -*-
# @author: NiHao

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo


class SignupForm(FlaskForm):
    # 注册页面-表单
    username = StringField('名字', validators=[DataRequired(), Length(1, 64, message='用户名应为1-15个字符长')])
    email = StringField('电子邮件', validators=[DataRequired(), Length(1, 64), Email(message='邮箱格式不正确')])
    password = PasswordField('密码', validators=[
        DataRequired(), EqualTo('password2', message='两次密码输入不一致。'),
        Length(6, 128, message='请输入至少6个字符')])
    password2 = PasswordField('确认密码', validators=[DataRequired()])
    submit = SubmitField('创建账户')


class LoginForm(FlaskForm):
    # 登录页面-表单
    email = StringField('电子邮件', validators=[DataRequired(), Email(message='邮箱格式不正确'), Length(1, 64)])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我', default=False)
    submit = SubmitField('登录')


class ModifyPasswordForm(FlaskForm):
    # 修改密码页面-表单
    old_password = PasswordField('旧密码', validators=[DataRequired()])
    new_password = PasswordField('新密码', validators=[
        DataRequired(), EqualTo('new_password2', message='两次密码输入不一致。'),
        Length(6, 128, message='请输入至少6个字符')])
    new_password2 = PasswordField('确认新密码', validators=[DataRequired()])
    submit = SubmitField('更改密码')


class ModifyEmailForm(FlaskForm):
    # 修改绑定邮箱页面-表单
    password = PasswordField('账户密码', validators=[DataRequired()])
    new_email = StringField('新电子邮件', validators=[DataRequired(), Email(message='邮箱格式不正确'), Length(1, 64)])
    submit = SubmitField('更改邮箱')


class PasswordResetEmailForm(FlaskForm):
    # 重置密码请求-表单
    email = StringField('', validators=[DataRequired(), Email(message='邮箱格式不正确'), Length(1, 64)])
    submit = SubmitField('发送重置邮件')


class PasswordResetForm(FlaskForm):
    # 重置密码新密码-表单
    new_password = PasswordField('新密码', validators=[
        DataRequired(), EqualTo('new_password2', message='两次密码输入不一致。'),
        Length(6, 128, message='请输入至少6个字符')])
    new_password2 = PasswordField('确认新密码', validators=[DataRequired()])
    submit = SubmitField('更改密码')