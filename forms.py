# -*- coding: utf-8 -*-
from flask.ext.wtf import Form
from wtforms import (
    StringField,
    PasswordField,
    TextAreaField,
    HiddenField,
    FileField
)
from wtforms import validators

class ProblemForm(Form):
	title = StringField("Problem",
			[validators.data_required(u"문제의 요지를 입력해주세요~!"),
			validators.Length(min=1, max=35, message=u"제목은 최대 35글자 입니다 ^^")
			])
	# summernote는 비었을 때 <p><br></p>를 포함함, 데이터 리콰이어  벨리데잇 불가
	content = TextAreaField("내용")
	# jquery로 hidden field value를 꼭 채워주자. newtag를 선택해도 여기를 채워주자
	tag_id = HiddenField("Tag list", [validators.data_required(u"기존의 태그를 선택하거나, 새로 만들어 주세요^^"),])
 	newtag = StringField("New tag", [validators.Length(max=12, message=u"태그는 최대 12글자 입니다 ^^")])
	file = FileField("Upload file")

class SolutionForm(Form):
	content = TextAreaField("내용")
 
class LoginForm(Form):
    id = StringField(u'아뒤')
    password = PasswordField(u'비번')


class JoinForm(Form):
    id = StringField(
        u'아뒤',
        [validators.data_required(u'아이디 입력! 한글가능,1~16글자'),
		validators.Length(min=1, max=16, message=u'아이디는 최대 16글자입니다^^')]
        )
    password = PasswordField(
        u'비번',
        [validators.data_required(u'비밀번호를 입력해주셔야죠!'),
        validators.EqualTo('confirm', message=u'비번이 일치 하지 않아요ㅇㅅㅇ'),
				validators.Length(min=4,max=4, message=u'비밀번호는 4자리 입니다^^')]
        )
    confirm = PasswordField(
        u' ',
        [validators.data_required(u'비밀번호를 한 번더 입력해주싱')],
        )

