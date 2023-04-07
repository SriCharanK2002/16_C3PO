from flask import render_template,url_for,flash,redirect,request
from ChainForge import app, db, bcrypt,mail

#forms
from ChainForge.forms import (RegistrationForm,LoginForm,UpdateAccountForm, ArtAddForm,OrderAddForm,OrderAcceptForm)

#for database
from ChainForge.models import User, Art , Order

#login manager
from flask_login import login_user, current_user, logout_user, login_required


#for images
from PIL import Image

#to send email
from flask_mail import Message


#mish
import secrets
import os
import requests

#Google login
from oauthlib.oauth2 import WebApplicationClient
os.environ['OAUTH2LIB_INSERCURE_TRANSPORT'] = '1'

GOOGLE_CLIENT_ID = "470006790722-34gafh4khrucvtouorksrcd2grm9car9.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

client = WebApplicationClient(GOOGLE_CLIENT_ID)


mediums = ['Animes','Mangas','Web Series','Movies','Games','Books']
entries = []
@app.before_first_request
def create_tables():
    db.create_all()

@app.route("/")
@app.route("/home")
def home():
	return render_template('home.html',entries=entries)



@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))

   
    return render_template('register.html', title='Register', form=form,ru = None)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')


  
    return render_template('login.html', title='Login', form=form,ru = None)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

def profile_picture(form_picture):
    random_hex = secrets.token_hex(8)
    #returns filename and extension filename not needed so 
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    #to resize
    output_size = (125,125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = profile_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    #returns filename and extension filename not needed so 
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    #to resize

    output_size = (600,400)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route("/portfolio",methods=['GET', 'POST'])
@login_required
def portfolio():
    form = ArtAddForm()

    user = User.query.filter_by(username=current_user.username).first_or_404()


    data = Art.query.filter_by(user_id = user.id)


    if form.submit.data and form.validate_on_submit():
        if form.image.data:
            picture_file = save_picture(form.image.data)
            art = Art(title = form.title.data, price = form.price.data,description = form.description.data,  image_file = picture_file, user_id= current_user.id)
            db.session.add(art)
            db.session.commit()
            flash('Art Added', 'success')
            return redirect(url_for('portfolio'))

    elif request.method == 'POST':
        print(request.form.get("update"))
        id = request.form.get("id")
        if request.form.get("delete") == "delete":
            art = Art.query.filter_by(id = id).first_or_404()
            db.session.delete(art)
            db.session.commit()

        else:
            art = Art.query.filter_by(id = id).first_or_404()
            art.market = True
            # print(art)
            db.session.commit()

    elif request.method == 'GET':
        data = Art.query.filter_by(user_id = user.id)


    return render_template('portfolio.html',title='portfolio',form = form,data = data)

@app.route("/marketplace",methods=['GET','POST'])
@login_required
def marketplace():
    data = Art.query.filter_by(market = True)

    if request.method == "POST":
        id = request.form.get("id")
        art = Art.query.filter_by(id = id).first_or_404()

        art.user_id = current_user.id

        art.market= False

        db.session.commit()

        return redirect(url_for('marketplace'))
    elif request.method == "GET":
        data = Art.query.filter_by(market = True)
    return render_template('marketplace.html',title = 'marketplace',data = data)

@app.route("/send",methods=['GET','POST'])
@login_required
def send_order():
    form = OrderAddForm()
    if form.validate_on_submit():
        order = Order(title = form.title.data, description = form.description.data,
            price = form.price.data,req_id = current_user.id, art_id = form.artist.data)
        db.session.add(order)
        db.session.commit()

        flash('Order sent', 'success')
        return redirect(url_for('send_order'))
    return render_template('send_order.html',title='send_order',form = form)


@app.route("/receive_order",methods=['GET','POST'])
@login_required
def receive_order():
    form = OrderAcceptForm()
    data = Order.query.filter_by(art_id= current_user.id)
    if form.submit.data and form.validate_on_submit():

        id = request.form.get("id")
        if form.image.data:
            order = Order.query.filter_by(id = id).first()
            picture_file = save_picture(form.image.data)
            art = Art(title= order.title, price = order.price, description = order.description, image_file = picture_file, user_id = order.req_id)
            db.session.add(art)
            db.session.delete(order)
            db.session.commit()
            flash('Art Added', 'success')
            return redirect(url_for('receive_order'))
        else:
            flash('No image selected','danger')
            return redirect(url_for('receive_order'))
    elif request.method == 'POST':
        id = request.form.get("id")

        if request.form.get("delete") == "delete":
            order = Order.query.filter_by(id = id).first_or_404()
            db.session.delete(order)
            db.session.commit()
    else:

        data = Order.query.filter_by(art_id= current_user.id)

    return render_template('receive_order.html',title='receive_order',data = data,form = form)




# def send_reset_email(user):
#     token = user.get_reset_token()
#     msg = Message('Password Reset Request',sender='noreply@demo.com',recipients=[user.email])
#     msg.body = f'''To reset your password, visit the following link:
# {url_for('reset_token', token=token, _external=True)}
# If you did not make this request then simply ignore this email and no changes will be made.
# '''
#     mail.send(msg)


# @app.route("/reset_password", methods=['GET', 'POST'])
# def reset_request():
#     if current_user.is_authenticated:
#         return redirect(url_for('home'))
#     form = RequestResetForm()
#     if form.validate_on_submit():
#         user = User.query.filter_by(email=form.email.data).first()
#         send_reset_email(user)
#         flash('An email has been sent with instructions to reset your password.', 'info')
#         return redirect(url_for('login'))
#     return render_template('reset_request.html', title='Reset Password', form=form)


# @app.route("/reset_password/<token>", methods=['GET', 'POST'])
# def reset_token(token):
#     if current_user.is_authenticated:
#         return redirect(url_for('home'))
#     user = User.verify_reset_token(token)
#     if user is None:
#         flash('That is an invalid or expired token', 'warning')
#         return redirect(url_for('reset_request'))
#     form = ResetPasswordForm()
#     if form.validate_on_submit():
#         hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
#         user.password = hashed_password
#         db.session.commit()
#         flash('Your password has been updated! You are now able to log in', 'success')
#         return redirect(url_for('login'))
#     return render_template('reset_token.html', title='Reset Password', form=form)