import web3
from flask import Flask
from web3.exceptions import BadFunctionCallOutput
from web3.contract import Contract
from web3 import Web3
from web3 import Account
from flask import render_template, url_for, flash, redirect, request
from ChainForge import app, db, bcrypt, mail

# forms
from ChainForge.forms import (
    RegistrationForm,
    LoginForm,
    UpdateAccountForm,
    ArtAddForm,
    OrderAddForm,
    OrderAcceptForm,
)

# for database
from ChainForge.models import User, Art, Order

# login manager
from flask_login import login_user, current_user, logout_user, login_required


# for images
from PIL import Image

# to send email
from flask_mail import Message


# mish
import secrets
import os
import requests


w3 = Web3(Web3.HTTPProvider("HTTP://127.0.0.1:7545"))
assert True is w3.is_connected()
# Load the contract bytecode and ABI from files
with open("Chainforge/cbi.bin", "r") as f:
    bytecode = f.read()
with open("Chainforge/contract.abi", "r") as f:
    abi = f.read()
# from web3.auto import w3
contract_mi = w3.eth.contract(
    abi=abi, bytecode=bytecode, address="0xc30cf3353Cd6Dbdfd4DA2D289Db859b8C062Bcfd"
)
private_keys = {
    1: "0xfa2d3a6e6e28fb711d67ec44337fb7334fa94a9e37513f480172a6a74423d30c",
    2: "0x9378a6f21fbb0b42ffd04688f96d9c135541f6733c1f3a6474e8e3bbc77fe51c",
    3: "0x4e4bd19ecd4b8a0976c4d8e4ae3831c57dbdb19e1f487d9fbeeb9f2144a45c0e",
}


@app.before_first_request
def create_tables():
    db.create_all()


@app.route("/")
@app.route("/home")
def home():
    # for i in User.query.all():
    #     db.session.delete(i)
    #     db.session.commit()
    # print(User.query.all())
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    print(User.query.all())
    user = User.query.filter_by(id=2).first()
    print(user)
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        user = User(
            username=form.username.data, email=form.email.data, password=hashed_password
        )
        db.session.add(user)
        db.session.commit()
        # print(User.query.order_by.id.desc().first().id)
        account = Account.from_key(private_keys[User.query.all()[-1].id])
        nonce = w3.eth.get_transaction_count(account.address)
        transaction = contract_mi.functions.register(
            form.username.data
        ).build_transaction(
            {
                "from": account.address,
                "gas": 6721975,
                "gasPrice": 20000000000,
                "nonce": nonce,
            }
        )
        signed_txn = account.sign_transaction(transaction)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(receipt)
        # gas = w3.eth.estimateGas(transaction)

        # # Set the gas limit to slightly above the estimated gas value
        #     gas_limit = int(gas * 1.1)

        #     # Set the gas price to slightly above the current median gas price
        #     gas_price = w3.toWei('60', 'gwei')

        #     # Add the gas limit and gas price to the transaction
        #     transaction['gas'] = gas_limit
        #     transaction['gasPrice'] = gas_price

        flash("Your account has been created! You are now able to log in", "success")
        return redirect(url_for("login"))

    return render_template("register.html", title="Register", form=form, ru=None)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("home"))
        else:
            flash("Login Unsuccessful. Please check email and password", "danger")

    return render_template("login.html", title="Login", form=form, ru=None)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


def profile_picture(form_picture):
    random_hex = secrets.token_hex(8)
    # returns filename and extension filename not needed so
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, "static/profile_pics", picture_fn)

    # to resize
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        print(User.query.all())
        if form.picture.data:
            picture_file = profile_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Your account has been updated!", "success")
        return redirect(url_for("account"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for("static", filename="profile_pics/" + current_user.image_file)
    return render_template(
        "account.html", title="Account", image_file=image_file, form=form
    )


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    # returns filename and extension filename not needed so
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, "static/profile_pics", picture_fn)

    # to resize

    output_size = (600, 400)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/portfolio", methods=["GET", "POST"])
@login_required
def portfolio():
    form = ArtAddForm()

    user = User.query.filter_by(username=current_user.username).first_or_404()

    data = Art.query.filter_by(user_id=user.id)

    if form.submit.data:
        if form.image.data:
            picture_file = save_picture(form.image.data)
            art = Art(
                title=form.title.data,
                price=form.price.data,
                description=form.description.data,
                image_file=picture_file,
                user_id=current_user.id,
            )
            db.session.add(art)
            db.session.commit()
            flash("Art Added", "success")
            return redirect(url_for("portfolio"))

    elif request.method == "POST":
        print(request.form.get("update"))
        id = request.form.get("id")
        if request.form.get("delete") == "delete":
            art = Art.query.filter_by(id=id).first()
            db.session.delete(art)
            db.session.commit()

        else:
            art = Art.query.filter_by(id=id).first()
            art.market = True
            account = Account.from_key(private_keys[current_user.id])
            nonce = w3.eth.get_transaction_count(account.address)
            transaction = contract_mi.functions.createProject(
                art.title, art.description, art.price
            ).build_transaction(
                {
                    "from": account.address,
                    "gas": 6721975,
                    "gasPrice": 20000000000,
                    "nonce": nonce,
                }
            )
            signed_txn = account.sign_transaction(transaction)

            # Send the signed transaction to the network
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            # print(art)
            db.session.commit()

    elif request.method == "GET":
        data = Art.query.filter_by(user_id=user.id)

    return render_template("portfolio.html", title="portfolio", form=form, data=data)


@app.route("/marketplace", methods=["GET", "POST"])
@login_required
def marketplace():
    data = Art.query.filter_by(market=True)

    if request.method == "POST":
        id = request.form.get("id")
        art = Art.query.filter_by(id=id).first_or_404()

        art.user_id = current_user.id

        art.market = False
        account = Account.from_key(private_keys[current_user.id])
        nonce = w3.eth.get_transaction_count(account.address)

        # Purchase
        transaction = contract_mi.functions.purchaseProject(int(id)).build_transaction(
            {
                "from": account.address,
                "value": int(art.price),
                "gas": 6721975,
                "gasPrice": 20000000000,
                "nonce": nonce,
            }
        )
        signed_txn = account.sign_transaction(transaction)

        # Send the signed transaction to the network
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

        # Wait for the transaction to be mined
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        # Print the transaction receipt
        print(receipt)

        db.session.commit()

        return redirect(url_for("marketplace"))
    elif request.method == "GET":
        data = Art.query.filter_by(market=True)
    return render_template("marketplace.html", title="marketplace", data=data)


@app.route("/send", methods=["GET", "POST"])
@login_required
def send_order():
    form = OrderAddForm()
    if form.validate_on_submit():
        # account = Account.from_key(private_keys[current_user.id])

        # nonce = w3.eth.get_transaction_count(account.address)

        # # Purchase
        # rec_account = Account.from_key(private_keys[form.artist.data])
        # transaction = contract_mi.functions.createOrder(
        #     form.title.data,
        #     private_keys[form.artist.data],
        #     0,
        #     int(form.price.data),
        #     form.description.data,
        # ).build_transaction(
        #     {
        #         "from": account.address,
        #         # "value": int(form.price.data),
        #         "gas": 6721975,
        #         "gasPrice": 20000000000,
        #         "nonce": nonce,
        #     }
        # )
        # signed_txn = account.sign_transaction(transaction)

        # # Send the signed transaction to the network
        # tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

        # # Wait for the transaction to be mined
        # receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        # # Print the transaction receipt
        # print(receipt)
        order = Order(
            title=form.title.data,
            description=form.description.data,
            price=form.price.data,
            req_id=current_user.id,
            art_id=form.artist.data,
        )
        db.session.add(order)
        db.session.commit()

        flash("Order sent", "success")
        return redirect(url_for("send_order"))
    return render_template("send_order.html", title="send_order", form=form)


@app.route("/receive_order", methods=["GET", "POST"])
@login_required
def receive_order():
    form = OrderAcceptForm()
    data = Order.query.filter_by(art_id=current_user.id)
    if form.submit.data and form.validate_on_submit():
        id = request.form.get("id")
        if form.image.data:
            order = Order.query.filter_by(id=id).first()
            picture_file = save_picture(form.image.data)
            art = Art(
                title=order.title,
                price=order.price,
                description=order.description,
                image_file=picture_file,
                user_id=order.req_id,
            )
            db.session.add(art)
            db.session.delete(order)
            db.session.commit()
            flash("Art Added", "success")
            return redirect(url_for("receive_order"))
        else:
            flash("No image selected", "danger")
            return redirect(url_for("receive_order"))
    elif request.method == "POST":
        id = request.form.get("id")

        if request.form.get("delete") == "delete":
            order = Order.query.filter_by(id=id).first_or_404()
            db.session.delete(order)
            db.session.commit()
    else:
        data = Order.query.filter_by(art_id=current_user.id)

    return render_template(
        "receive_order.html", title="receive_order", data=data, form=form
    )


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