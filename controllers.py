# -*- coding: utf-8 -*-
import os, random

from flask import send_from_directory, render_template, request, redirect, url_for, flash, session, g, jsonify, send_from_directory,Markup

import json

from werkzeug import secure_filename
from werkzeug.exceptions import default_exceptions
from werkzeug.security import generate_password_hash, check_password_hash

from sqlalchemy import desc

from apps import app, db, login_manager

from apps.models import (User, Tag, Article, Comment)

from flask.ext.login import login_required, login_user, logout_user, current_user

from pusher import Pusher

UPLOAD_FOLDER = './uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


@app.route("/")
def index():
	return redirect(url_for('login'))

# login & join  function
##############################################################################################################
@login_manager.user_loader
def load_user(user_id):
	return User.query.get(user_id)

@login_manager.unauthorized_handler
def unauthorized():
    flash(u"로그인이 필요합니다.")
    return redirect(url_for('login'))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.before_request
def before_request():
    g.user = current_user


@app.route("/login", methods=['GET', 'POST'])
def login():
	
	if request.method=="POST":
		user_id = request.form['userid']
		password = request.form['password']
		# 없는 회원
		if User.query.get(user_id) == None:
			flash(u'없는 ID입니다^^')
			return render_template('login.html')
		else:
			user = User.query.get(user_id)
			if check_password_hash(user.pw, password):
				login_user(user)
				return redirect(url_for('timeline', sort_type="all"))
			else :
				flash(u'비밀번호 틀림!')
				return render_template('login.html')

		return redirect(url_for('login'))

	flash('기존의 <span style="color:red">아이디가 5자리인 회원</span>은 다시가입해주세요^^')
	return render_template('login.html')


@app.route('/join', methods=['GET', 'POST'])
def join():
	if request.method == "POST":
		userid = request.form['userid']
		name = request.form['name']
		password = request.form['password']
		confirm = request.form['confirm']
		file = request.files['file']


		if User.query.get(userid):
			flash(u'이미 존재하는 회원입니다^^')
			return render_template('join.html', userid=userid, name=name, password=password, confirm=confirm)

		if password != confirm:
			flash(u'비밀번호가 일치 하지 않습니다!')
			return render_template('join.html', userid=userid, name=name)
			
		if len(userid) != 9 or (not userid.isdigit()):
			flash(u'<span style="color:red">학번(년도4자리 + 학번5자리) 9자리 숫자</span>를 입력해주세요. 예)201510322')
			return render_template('join.html', userid=userid, name=name, password=password, confirm=confirm)

		if len(name) == 0:
			flash(u'이름을 입력해주세요')
			return render_template('join.html', userid=userid, name=name, password=password, confirm=confirm)

		if len(password) == 0:
			flash(u'비밀번호를 입력해주세요')
			return render_template('join.html', userid=userid, name=name, password=password, confirm=confirm)

		filename = "" 
		if file and allowed_file(file.filename):
			#filename = secure_filename(file.filename)
			filename = "profile_" + userid + "." + file.filename.rsplit('.', 1)[1] 
			filename = filename.lower()
			file.save(os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], filename))

		new_user = User(id=userid, name=name, pw=generate_password_hash(password), photo=filename)
		db.session.add(new_user)
		db.session.commit()
		flash(u'회원 가입 완료^^')
		return redirect(url_for('login'))
	
	return render_template('join.html')


@app.route('/update_profile', methods=['GET', 'POST'])
@login_required
def update_profile():
	user =  User.query.get(g.user.id)
	name = user.name
	photo = user.photo

	if request.method == "POST":
		name = request.form['name']
		password = request.form['password']
		confirm = request.form['confirm']
		file = request.files['file']

		if password != confirm:
			flash(u'비밀번호가 일치 하지 않습니다!')
			return render_template('update_profile.html', name=name)
			
		if len(name) == 0:
			flash(u'이름을 입력해주세요')
			return render_template('update_profile.html', name=name)

		filename = user.photo 
		if file and allowed_file(file.filename):
			filename = "profile_" + user.id + "." + file.filename.rsplit('.', 1)[1] 
			file.save(os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], filename))
		
		user.name = name
		user.photo = filename
		if len(password) > 0 :
			user.pw = generate_password_hash(password)

		db.session.commit()
		flash(u'회원정보 수정  완료^^')
		return redirect(url_for('personal_info'))
	
	return render_template('update_profile.html', name=name, photo=photo)
##############################################################################################################

@app.route('/timeline/<sort_type>', methods=['GET'])
@login_required
def timeline(sort_type):
	textcolor = ['danger', 'info', 'warning', 'success', 'primary', 'muted']

	# 인기 태그 10개
	tags = Tag.query.all() 
	tags.sort(key=lambda x: len(x.articles), reverse=True)
	tags = tags[0:10]

	articles_t = Article.query.all()
	articles_t.reverse()

	# 공지사항 뽑기
	notices = []
	tmp = []
	for article in articles_t:
		if article.tag_id == "공지사항":
			notices.append(article)
		else:
			tmp.append(article)
	articles_t = tmp

	# 태그 필터링
	if sort_type == "all":
		# 공지사항 한개만 맨 앞에 붙이기
		if len(notices) > 0:
			articles_t.insert(0, notices[0])
		articles = articles_t

	elif sort_type == "classmate":
		articles = []
		for article in articles_t:
			if article.user.id[4:7] == g.user.id[4:7]:
				articles.append(article)

	elif sort_type == "공지사항":
		articles = notices

	else:
		articles = []
		for article in articles_t:
			if article.tag.id == sort_type:
				articles.append(article)

	return render_template('timeline.html', articles=articles, tags=tags, textcolor=textcolor, sort_type=sort_type)

@app.route('/tags_all')
@login_required
def tags_all():
	textcolor = ['danger', 'info', 'warning', 'success', 'primary', 'muted']

	tags = Tag.query.all()
	tags.sort(key=lambda x: len(x.articles), reverse=True)

	return render_template('tags_all.html', tags=tags, textcolor=textcolor )


@app.route('/create_article', methods=["GET", "POST"])
@login_required
def create_article():
	textcolor = ['danger', 'info', 'warning', 'success', 'primary', 'muted']
	
	tags = Tag.query.all()
	tags.sort(key=lambda x: len(x.articles), reverse=True)
	#tags = tags[0:10]

	title = ""
	tag_typed = ""
	content = ""
	if request.method == "POST":
		title = request.form['title'].strip()
		tag_typed = request.form['tag'].strip()
		content = request.form['content'].strip()
		files = request.files.getlist('file[]')

		if len(title) == 0:
			flash(u"제목을 입력해주세요")
			return render_template('create_article.html', title=title, content=content, tag_typed=tag_typed, tags=tags, textcolor=textcolor)

		if len(tag_typed) == 0:
			flash(u"태그를 입력하거나 선택해주세요")
			return render_template('create_article.html', title=title, content=content, tag_typed=tag_typed, tags=tags, textcolor=textcolor)

		if tag_typed == "공지사항" and g.user.id != "nstalk":
			flash(u'"<span style="color:red">공지사항</span>"은 <span style="color:red">관리자</span>만 쓸 수있는 태그입니다')
			return render_template('create_article.html', title=title, content=content, tags=tags, textcolor=textcolor)

		if len(content) == 0:
			flash(u"내용을 입력해주세요")
			return render_template('create_article.html', title=title, content=content, tag_typed=tag_typed, tags=tags, textcolor=textcolor)
		

		#file type check
		# 왜 파일 업로드 안했을 때 길이가 1이지?
		if len(files[0].filename) > 0:
			for file in files:
				if file and allowed_file(file.filename):
					pass
				else:
					flash(file.filename + u": 허용된 파일 형식이 아닙니다(png,jpg,jpeg,gif만 허용)")
					return render_template('create_article.html', title=title, content=content, tag_typed=tag_typed, tags=tags, textcolor=textcolor)

		tag =  Tag.query.get(tag_typed)
		# new tag
		if tag is None:
			tag = Tag(id=tag_typed)
			if u"?" in tag.id or u"&" in tag.id or u" " in tag.id:
				flash(u"태그에 빈칸을 포함할 수 없습니다!")
				return render_template('create_article.html', title=title, content=content, tags=tags, textcolor=textcolor)
			db.session.add(tag)
			db.session.commit()
		
		user = User.query.get(g.user.id)
		
		article = Article(
			title = title.strip(), 
			content = content,
			like_count = 0,
			like_history = "",
			like_history_user = "",
			user_id = g.user.id,
			user = user,
			tag_id = tag.id,
			tag = tag,
			files = ""
		)
		# create article
		db.session.add(article)
		
		# tag count ++ 
		tag.article_count += 1

		db.session.commit()	
		
		#file upload
		filenames = []
		cnt = 0

		if len(files[0].filename) > 0:
			for file in files:
				filename = "photo" + str(cnt)+ "_" + str(article.id) + "." + file.filename.rsplit('.', 1)[1]
				filename = filename.lower()
				file.save(os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], filename))	
				filenames.append(filename)
				cnt += 1
			article.files = ",".join(filenames)
		db.session.commit()

		return redirect(url_for('timeline', sort_type="all"))
	return render_template('create_article.html', title=title, content=content, tags=tags, textcolor=textcolor)


@app.route('/update_article/<article_id>', methods=["GET", "POST"])
@login_required
def update_article(article_id):

	textcolor = ['danger', 'info', 'warning', 'success', 'primary', 'muted']
	
	tags = Tag.query.all()
	tags.sort(key=lambda x: len(x.articles), reverse=True)
	#tags = tags[0:10]

	article = Article.query.get(article_id)
	if g.user.id != article.user_id:
		flash(u'<span style="color:red">자신이 쓴 글만</span> 수정할 수 있습니다!')
		return redirect(url_for('show_article', article_id=article_id))

	title = article.title
	tag_typed = article.tag_id 
	content = article.content 
	files = article.files.split(",")

	if request.method == "POST":
		title = request.form['title'].strip()
		tag_typed = request.form['tag'].strip()
		content = request.form['content'].strip()
		files = request.files.getlist('file[]')

		if len(title) == 0:
			flash(u"제목을 입력해주세요")
			return render_template('update_article.html',article_id=article_id, title=title, content=content, tag_typed=tag_typed, tags=tags, files=files, textcolor=textcolor)

		if len(tag_typed) == 0:
			flash(u"태그를 입력하거나 선택해주세요")
			return render_template('update_article.html',article_id=article_id, title=title, content=content, tag_typed=tag_typed, tags=tags, files=files, textcolor=textcolor)

		if tag_typed == "공지사항" and g.user.id != "nstalk":
			flash(u'"<span style="color:red">공지사항</span>"은 <span style="color:red">관리자</span>만 쓸 수있는 태그입니다')
			return render_template('update_article.html',article_id=article_id, title=title, content=content, tag_typed=tag_typed, tags=tags, files=files, textcolor=textcolor)

		if len(content) == 0:
			flash(u"내용을 입력해주세요")
			return render_template('update_article.html',article_id=article_id, title=title, content=content, tag_typed=tag_typed, tags=tags, files=files, textcolor=textcolor)
		

		#file type check
		# 왜 파일 업로드 안했을 때 길이가 1이지?
		if len(files[0].filename) > 0:
			for file in files:
				if file and allowed_file(file.filename):
					pass
				else:
					flash(file.filename + u": 허용된 파일 형식이 아닙니다(png,jpg,jpeg,gif만 허용)")
					return render_template('update_article.html',article_id=article_id, title=title, content=content, tag_typed=tag_typed, tags=tags, files=files, textcolor=textcolor)

		tag =  Tag.query.get(tag_typed)
		# new tag-> change tag
		if tag is not None  and article.tag.id != tag.id:
			article.tag.article_count -= 1
			tag.article_count += 1

		if tag is None:
			article.tag.article_count -= 1
			tag = Tag(id=tag_typed)
			tag.article_count = 1
			if u"?" in tag.id or u"&" in tag.id or u" " in tag.id:
				flash(u"태그에 빈칸을 포함할 수 없습니다!")
				return render_template('update_article.html',article_id=article_id, title=title, content=content, tag_typed=tag_typed, tags=tags, files=files, textcolor=textcolor)
			db.session.add(tag)
			db.session.commit()

		# update article
		article.title = title
		article.content = content
		article.tag_id = tag.id
		article.tag = tag

		#file upload
		filenames = []
		cnt = 0
		if len(files[0].filename) > 0:
			for file in files:
				filename = "photo" + str(cnt)+ "_" + str(article.id) + "." + file.filename.rsplit('.', 1)[1]
				filename = filename.lower()
				file.save(os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], filename))	
				filenames.append(filename)
				cnt += 1
			article.files = ",".join(filenames)

		db.session.commit()

		return redirect(url_for('show_article', article_id=article_id))

	return render_template('update_article.html',article_id=article_id, title=title, content=content, tag_typed=tag_typed, tags=tags, files=files, textcolor=textcolor)

@app.route('/show_article/<article_id>')
@login_required
def show_article(article_id):
	article = Article.query.get(article_id)	
	comments = article.comments
	comments.reverse()
	files = article.files.split(",")
	return render_template('show_article.html', article=article, comments=comments, files=files)


@app.route('/delete_article/<article_id>')
def delete_article(article_id):
	article = Article.query.get(article_id)
	tag = Tag.query.get(article.tag_id)

	if g.user.id != article.user.id:
		flash(u'<span style="color:red">자신이 쓴 글만</span> 삭제할 수 있습니다!')
		return redirect(url_for('show_article', article_id=article_id))

	db.session.delete(article)
	tag.article_count -= 1
	if tag.article_count == 0:
		db.session.delete(tag)
	db.session.commit()
	flash(u'삭제되었습니다')
	return redirect(url_for('timeline', sort_type="all"))


@app.route('/like/<article_id>')
@login_required
def like(article_id):
	article = Article.query.get(article_id)	
	
	if g.user.id not in article.like_history:
		article.like_count += 1
		if len(article.like_history) == 0:
			article.like_history = g.user.id
			article.like_history_user = g.user.name
		else:
			article.like_history += "," + g.user.id
			article.like_history_user += "," + g.user.name
	else:
		article.like_count -= 1
		if len(article.like_history) == 1:
			article.like_history = ""
			article.like_history_user = ""
		else :
			tmps1 = article.like_history.split(',')
			tmps1.remove(g.user.id)
			tmps2 = article.like_history_user.split(',')
			tmps2.remove(g.user.name)
			article.like_history = ",".join(tmps1)
			article.like_history_user = ",".join(tmps2)
	db.session.commit()

	return redirect(url_for('show_article', article_id=article_id))

@app.route('/comment/<article_id>', methods=['POST'])
@login_required
def comment(article_id):
	article = Article.query.get(article_id)
	user = User.query.get(g.user.id)

	content = request.form['content']

	comment = Comment(
		article_id=article_id, 
		article=article, 
		user_id=g.user.id, 
		user=user, 
		content=content
	)
	db.session.add(comment)
	article.comment_count += 1
	db.session.commit()
	
	return redirect(url_for('show_article', article_id=article_id))

#사실 comment id만 있으면 된다.
@app.route('/delete_comment/<article_id>/<comment_id>')
def delete_comment(article_id, comment_id):
	article = Article.query.get(article_id)
	comment = Comment.query.get(comment_id)
	if g.user.id != comment.user.id:
		flash(u'<span style="color:red">자신이 쓴 글만</span> 삭제할 수 있습니다!')
		return redirect(url_for('show_article', article_id=article_id))

	db.session.delete(comment)
	article.comment_count -= 1
	db.session.commit()
	return redirect(url_for('show_article', article_id=article_id))

@app.route('/calendar')
@login_required
def calendar():
	flash(u'이 기능은 이번 주의 <span style="color:red">급식 메뉴 및 특별한 행사 일정</span>을 게시합니다(미완성)')
	return render_template("calendar.html")

@app.route('/personal_info')
@login_required
def personal_info():
	user = User.query.get(g.user.id)
	num_article = 0
	articles = user.articles
	articles.reverse()
	for i in articles:
		num_article += 1
	return render_template("personal_info.html", user=user, num_article=num_article, articles=articles)


@app.route('/user_info/<user_id>')
@login_required
def user_info(user_id):
	user = User.query.get(user_id)
	num_article = 0
	articles = user.articles
	for i in articles:
		num_article += 1
	return render_template("personal_info.html", user=user, num_article=num_article, articles=articles)


# file upload and download module
##############################################################################################################
def allowed_file(filename):
	return '.' in filename and \
			filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/file', methods=['GET', 'POST'])
def upload_file():
	if request.method == 'POST':
		files = request.files.getlist('file[]')
		filenames = []
		cnt = 0
		for file in files:
			if file and allowed_file(file.filename):
				filename = secure_filename(file.filename)
				file.save(os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], filename))	
				filenames.append(filename)
			else:
				return file.name + "-> 허용된 파일 형식이 아닙니다~^^"
		return "완료 : " + str(filenames)

	filelist = "<p><br>".join(os.listdir(os.path.join(app.root_path, app.config['UPLOAD_FOLDER']))) + "</p>"

	return render_template('fileupload.html', filelist=filelist) 

@app.route('/download/<filename>')
def uploaded_file(filename):
	return send_from_directory(os.path.join(app.root_path, app.config['UPLOAD_FOLDER']), filename)


##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
@app.route('/like_history_test', methods=['GET', 'POST'])
def like_history_test():
	articles = Article.query.all()
	for article in articles:
		userids = article.like_history
		if len(userids) == 0:
			article.like_history_user = ""
		else:
			cnt = 0 
			like_history_user = ""
			userids = userids.split(',')
			for userid in userids:
				user = User.query.get(userid)
				if cnt == 0 :
					like_history_user = user.name 
				else:
					like_history_user += "," + user.name	
				cnt += 1
			article.like_history_user = like_history_user
	db.session.commit()	
		
	return "good"

@app.route('/comment_cnt')
def comment_cnt():
	articles = Article.query.all()
	for article in articles:
		article.comment_count = len(article.comments)
	db.session.commit()
	return "good" 

@app.route('/article_cnt')
def article_cnt():
	tags = Tag.query.all()
	for tag in tags:
		tag.article_count = len(tag.articles)
	db.session.commit()
	return "good" 

@app.route('/delete0')
def delete0():
	tags = Tag.query.all()
	for tag in tags:
		if tag.article_count == 0:
			db.session.delete(tag)
	db.session.commit()
	return "good" 

@app.route('/delete_user/<user_id>')
def delete_user(user_id):
	user = User.query.get(user_id)
	db.session.delete(user)
	db.session.commit()
	return "good"

@app.route('/delete_all_article')
def delete_all_article():
	articles = Article.query.all()
	for a in articles:
		db.session.delete(a)
	db.session.commit()
	return "good"

@app.route('/delete_all_tag')
def delete_all_tag():
	tags = Tag.query.all()
	for t in tags:
		db.session.delete(t)
	db.session.commit()
	return 'good'


