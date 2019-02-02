
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, FileField
from wtforms.validators import DataRequired, Email, EqualTo, Length

''' 查看flask—wtf 文档，看是否需要增加功能 -- 以后'''


class ModifyCollForm(FlaskForm):
    name = StringField('清单名', validators=[DataRequired(), Length(1, 16)])
    summery = TextAreaField('简介', validators=[Length(1, 200)])
    file = FileField()
    submit = SubmitField('确认')
