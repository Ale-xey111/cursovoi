import os
import re
import time
from flask import Flask, render_template, request, flash, url_for, redirect, session, abort
#from flask_mysqldb import MySQL
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_required, login_user, LoginManager, login_manager, UserMixin, logout_user, current_user
from flask_migrate import Migrate


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Fijkl game fc1@localhost/flask_app_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

login_manager = LoginManager(app)
login_manager.login_view = 'Login'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), nullable = False)
    surname = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(220), nullable=False)

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return "<{}:{}>".format(self.id, self.name[:30], self.surname[:30])

class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    category = db.Column(db.String(100), nullable=False)
    descripiton = db.Column(db.String(255), nullable=False)
    image = db.Column(db.String(255), nullable=False)


class Cart(db.Model):
    __tablename__ = "cart"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

'''
@app.route('/')
def home():
    featured_products = Product.query.filter_by(category='light').all()
    special_offers = Product.query.filter_by(id = 10).all()

    return render_template('Home.html', featured_products=featured_products, special_offers=special_offers)
'''

@app.route('/')
def home():

    return render_template('index.html')


@app.route('/Login', methods = ["GET","POST"])
def Login():

    if "userLogged" in session:
        return redirect(url_for('profile', login = session['userLogged']))
    if request.method == 'POST' and ('login' in request.form) and ('password' in request.form):

        login_attempt = request.form['login']
        password_attempt = request.form['password']
        remember_me = request.form.get('checkbox') == 'on'

        user = User.query.filter_by(email = login_attempt).first()

        if user and check_password_hash(user.password, password_attempt):

            flash("Успешно", category='success')
            session['userLogged'] = user.email
            login_user(user)

            return redirect(url_for('profile', login=session['userLogged']))
        else:
            flash("Неверный логин или пароль. Попробуйте снова.", category="error")

    return render_template('Login.html')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(str(user_id))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash("Вы вышли из аккаунта" , "success")
    return redirect(url_for('home'))


@app.route("/profile/<login>" , methods = ["GET", "POST"])
@login_required
def profile(login):
    if current_user.email != login:
        abort(401)

    favorite_items = session.get('favorites' , [])
    favorite_products = []

    for item in favorite_items:
        product = Product.query.get(item['product_id'])
        if product:
            favorite_products.append({'product': product})


    if request.method == 'POST':

        if 'ClearObject' in request.form:
            product_to_remove = int(request.form['ClearObject'])
            session['favorites'] = [item for item in session['favorites'] if item['product_id'] != product_to_remove]
            return redirect(url_for('profile', login=current_user.email))

        if'ClearFavorites' in request.form:
            session['favorites'] = []
            return redirect(url_for('profile', login=current_user.email))

    return render_template('Profile.html', title=login, favorite_products = favorite_products)

def is_valid_email(email):
    email_regex = r'^\S+@\S+\.\S+$'
    return re.match(email_regex, email) is not None

@app.route('/SignUp' , methods = ["GET","POST"])
def SignUP():

    if request.method == 'POST':
        if not is_valid_email(request.form['E-mail']):
            flash("Пожалуйста, введите корректный адрес электронной почты.", category="error")
            return render_template('SignUp.html')

        if ((3 < len(request.form['name']) < 50) and
            (3 < len(request.form['surname']) < 50) and
            (4 < len(request.form['E-mail']) < 100) and
            (5 < len(request.form['password']) < 220)):

            hash = generate_password_hash(request.form['password'])

            new_user = User(
                name = request.form['name'],
                surname = request.form['surname'],
                email = request.form['E-mail'],
                password = hash
            )
            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for('home'))
        else:
            flash("Что-то пошло не так, попробуйте снова...", category="error")

    return render_template('SignUp.html')


@app.route('/Product/<int:id>')
def product_detail(id):
    product = Product.query.get_or_404(id)
    return render_template('Product_detail.html', product=product)


@app.route('/Cart' , methods = ["GET","POST"])
@login_required
def Cart():
    cart_items = session.get('cart', [])
    total = 0
    cart_products = []

    for item in cart_items:
        product = Product.query.get(item['product_id'])
        if product:
            cart_products.append({'product': product, 'quantity': item['quantity']})
            total +=product.price * item['quantity']

    if "submitAction" in request.form:
        session['cart'] = []
        flash("Корзина очищена", category='success')
        return redirect(url_for('Cart'))

    if request.method == 'POST':

        if 'ClearObject' in request.form:
            object_to_remove = int(request.form['ClearObject'])
            session['cart'] = [item for item in session['cart'] if item['product_id'] != object_to_remove]
            return redirect(url_for('Cart'))

    return render_template('Cart.html', cart_products=cart_products, total= total)


@app.route('/add_to_cart/<int:product_id>')
@login_required
def add_to_cart(product_id):
    if 'cart' not in session:
        session['cart'] = []

    product = Product.query.get(product_id)

    if product:
        for item in session['cart']:
            if item['product_id'] == product_id:
                if item['quantity'] < product.quantity:
                    item['quantity'] += 1
                    flash('Товар добавлен в корзину', category='success')

                else:
                    flash('Достигнуто максимальное количество товара', category='error')
                break
        else:
            session['cart'].append({'product_id': product_id, 'quantity': 1})

            flash('Товар добавлен в корзину', category='success')
    else:
        flash('Продукт не найден', category='error')

    return render_template('Cart.html')

@app.route('/add_to_favorites/<int:product_id>')
@login_required
def add_to_favorites(product_id):
    if 'favorites' not in session:
        session['favorites'] = []

    product = Product.query.get(product_id)

    if product:
        if not any(item['product_id'] == product_id for item in session['favorites']):
            session['favorites'].append({'product_id': product_id})
            flash(f'{product.name} добавлен в избранное', 'success')
        else:
            flash(f'{product.name} уже находится в избранном', 'info')
    else:
        flash('Продукт не найден', 'error')

    return redirect(url_for('profile', login=current_user.email))


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html') , 404


def create_app():
    with app.app_context():
        db.create_all()


if __name__ == '__main__':
    create_app()
    app.run(debug = True)

#сделать корзину, предпочтения пользователя поиск, использовать шаблон амазон.
#локализацию

'''
class BackMessage(db.Model):
    __tablename__ = "backmessage"
    id = db.Column(db.Integer(), primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    text = db.Column(db.String(1000), nullable=False)
'''

#INSERT INTO products (name,price,image,quantity,category,descripiton) VALUES ('Set of wheels for AUDI A6 C6 2005', 40,'4wheelsA6C6.png', 4, 'wheels','Car wheels have significant scratches and chips.');
#INSERT INTO products (name,price,image,quantity,category,descripiton) VALUES ('Right Headlight AUDI A6 C7', 630,'RightHeadlight A6C7.png', 4, 'light', 'New headlight from Germany. Fully working, no chips or scratches');

#Как реализовать форму обратной связи? Через бд?