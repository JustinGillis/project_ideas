from flask import Flask, render_template, request, redirect, session
import re
from flask_bcrypt import Bcrypt 
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_migrate import Migrate
import os
from pathlib import Path

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dumb_project_ideas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

app.secret_key = 'secret key'
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
bcrypt = Bcrypt(app)

pinned_table = db.Table('pinned', 
              db.Column('user_id', db.Integer, db.ForeignKey('user.id', ondelete='cascade'), primary_key=True), 
              db.Column('project_id', db.Integer, db.ForeignKey('project.id', ondelete='cascade'), primary_key=True))

likes_table = db.Table('likes', 
              db.Column('user_id', db.Integer, db.ForeignKey('user.id', ondelete='cascade'), primary_key=True), 
              db.Column('project_id', db.Integer, db.ForeignKey('project.id', ondelete='cascade'), primary_key=True))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255))
    email = db.Column(db.String(255))
    password = db.Column(db.String(255))
    projects_this_user_likes = db.relationship('Project', secondary=likes_table)
    projects_this_user_pinned = db.relationship('Project', secondary=pinned_table)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(255))
    title = db.Column(db.String(255))
    description = db.Column(db.String(255))
    instructions = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="cascade"))
    author = db.relationship('User', foreign_keys=[author_id], backref="user_projects")
    users_who_like_this_project = db.relationship('User', secondary=likes_table)
    users_who_pinned_this_project = db.relationship('User', secondary=pinned_table)
    num_likes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(255))
    author_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="cascade"), nullable=False)
    author = db.relationship('User', foreign_keys=[author_id], backref="user_comments")
    project_id = db.Column(db.Integer, db.ForeignKey("project.id", ondelete="cascade"), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())



# TODO STEPS
# fix delete comment code
# add filters
# add icons?
# log in after register
# fix responsive nav bar
# style view project page, maybe add more info like created at
# change posistion of card text
# modularize
# add validations

# TODO BACKLOG
# add option and fuctionality to add profile pics and show them somewhere
# add follower code to user class
# add categories class and fuctionality
# add option to follow user on single user page
# add single user view page with user stats (does showing the users projects here make sense?)
# change created by: text to a link to single user view page
# add jquery
# add os files 
# can repurpose into a site where ppl vote on project ideas so people can see if they should do them or not


@app.route('/')
def projects():
    if 'userid' in session:
        user = User.query.get(session['userid'])
        users = User.query.all()
        users_pinned_projects = user.projects_this_user_pinned
        project_likes = Project.query.order_by(Project.num_likes.desc()).all()
        return render_template('projects.html', user=user, users=users, projects=project_likes, users_pinned_projects=users_pinned_projects)
    else:
        users = User.query.all()
        project_likes = Project.query.order_by(Project.num_likes.desc()).all()
        return render_template('projects.html', users=users, projects=project_likes)


@app.route('/my_projects')
def my_projects():
    projects = Project.query.filter_by(author_id=session['userid']).all()
    return render_template('my_projects.html', projects=projects)

@app.route('/Order_by_date')
def Order_by_date():
    if 'userid' in session:
        user = User.query.get(session['userid'])
        users_pinned_projects = user.projects_this_user_pinned
        projects = Project.query.order_by(Project.id.desc()).all()
        return render_template('ordered_by_date.html', projects=projects, users_pinned_projects=users_pinned_projects)
    else:
        projects = Project.query.order_by(Project.id.desc()).all()
        return render_template('ordered_by_date.html', projects=projects)


# add validations & login
@app.route('/on_register', methods=['POST'])
def on_register():
    is_valid = True
    if is_valid:
        pw_hash = bcrypt.generate_password_hash(request.form['password'])
        new_user = User(username=request.form['username'], email=request.form['email'], password=pw_hash)
        db.session.add(new_user)
        db.session.commit()
        user = User.query.filter_by(username=request.form['username']).first()
        session['userid'] = user.id
        return redirect('/')
    else:
        return redirect('/')

@app.route('/on_login', methods=['post'])
def on_login():
    user = User.query.filter_by(username=request.form['username']).first()
    if user == None:
        return redirect('/')
    elif bcrypt.check_password_hash(user.password, request.form['password']):
        session['userid'] = user.id
        return redirect('/')

@app.route('/project_form')
def project_form():
    if 'userid' not in session:
        return redirect('/')
    return render_template('add_project.html')

app.config['IMAGE_UPLOADS'] = Path("C:/Users/Justin/OneDrive/coding_dojo/projects/dumb_project_ideas/static/img")

@app.route('/on_add_project', methods=['POST'])
def on_add_project():
    image = request.files['image']
    print('got', image)
    new_project = Project(image=image.filename, title=request.form['title'], description=request.form['description'], instructions=request.form['instructions'], author_id=session['userid'])
    db.session.add(new_project)
    db.session.commit()
    image.save(os.path.join(app.config['IMAGE_UPLOADS'], image.filename))
    return redirect('/')

@app.route('/view_project/<id>')
def view_project(id):
    if 'userid' in session:
        user = User.query.get(session['userid'])
    else:
        user = False
    project = Project.query.filter_by(id=id).first()
    comments = Comment.query.filter_by(project_id=id)
    return render_template('view_project.html', project=project, comments=comments, user=user)

@app.route('/on_like/<id>')
def on_like(id):
    existing_project = Project.query.get(id)
    existing_user = User.query.get(session['userid'])
    existing_user.projects_this_user_likes.append(existing_project)
    db.session.commit()
    existing_project.num_likes +=1
    db.session.commit()
    print('on like complete')
    return redirect('/view_project/' + id)

@app.route('/on_unlike/<id>')
def on_unlike(id):
    existing_project = Project.query.get(id)
    existing_user = User.query.get(session['userid'])
    existing_user.projects_this_user_likes.remove(existing_project)
    db.session.commit()
    existing_project.num_likes -=1
    db.session.commit()
    return redirect('/view_project/' + id)

@app.route('/on_comment/<id>', methods=['POST'])
def on_comment(id):
    comment = Comment(content=request.form['content'], author_id=session['userid'], project_id=id)
    db.session.add(comment)
    db.session.commit()
    return redirect('/view_project/' + id)

@app.route('/on_delete_comment/<project>/<id>')
def on_delete_comment(project, id):
    existing_user = User.query.get(session['userid'])
    comments = Comment.query.all()
    comment = Comment.query.get(id)
    print('comments:', comments)
    print('comment:', comment)
    print('*'*20)
    existing_user.user_comments.remove(comment)
    db.session.commit()
    return redirect('/view_project/' + project)

@app.route('/on_pin/<id>')
def on_pin(id):
    existing_project = Project.query.get(id)
    existing_user = User.query.get(session['userid'])
    existing_user.projects_this_user_pinned.append(existing_project)
    db.session.commit()
    print('on pin complete')
    return redirect('/view_project/' + id)

@app.route('/on_unpin/<id>')
def on_unpin(id):
    existing_project = Project.query.get(id)
    existing_user = User.query.get(session['userid'])
    existing_user.projects_this_user_pinned.remove(existing_project)
    db.session.commit()
    return redirect('/view_project/' + id)

@app.route('/on_logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)