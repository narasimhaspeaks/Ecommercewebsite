from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from . import db
from .models import User, Product, Order, OrderItem
from .forms import RegisterForm, LoginForm, ProductForm, CheckoutForm, ContactForm
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename 

# --- FILE UPLOAD IMPORTS ---
from flask_uploads import UploadSet, IMAGES, configure_uploads 

# Initialize the image uploading system outside of a function
photos = UploadSet('photos', IMAGES) 
# ---------------------------

bp = Blueprint("main", __name__)

# ---------- Helper: cart ----------
def get_cart():
    cart = session.get("cart", {})
    return cart

def save_cart(cart):
    session["cart"] = cart
    session.modified = True

# ---------- Public routes ----------
@bp.route("/")
def home():
    q = request.args.get("q", "")
    cat = request.args.get("category", "")
    products = Product.query
    if q:
        products = products.filter(Product.name.ilike(f"%{q}%"))
    if cat:
        products = products.filter_by(category=cat)

    products = products.all()
    categories = [p.category for p in Product.query.with_entities(Product.category).distinct()]
    return render_template("home.html", products=products, categories=categories, q=q, category=cat)

@bp.route("/product/<int:product_id>")
def product_detail(product_id):
    p = Product.query.get_or_404(product_id)
    return render_template("product.html", product=p)

# ---------- Auth ----------
@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("Email already registered", "warning")
            return redirect(url_for("main.register"))

        u = User(username=form.username.data, email=form.email.data)
        u.set_password(form.password.data)
        db.session.add(u)
        db.session.commit()

        flash("Registered! Please log in.", "success")
        return redirect(url_for("main.login"))
    return render_template("register.html", form=form)

@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash("Logged in", "success")
            return redirect(url_for("main.home"))

        flash("Invalid credentials", "danger")
    return render_template("login.html", form=form)

@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.home"))

# ---------- Cart ----------
@bp.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    cart = get_cart()
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    save_cart(cart)
    flash(f"Added {product.name} to cart.", "success")
    # Redirect to the cart page after adding
    return redirect(url_for("main.cart")) 

@bp.route("/cart")
def cart():
    cart = get_cart()
    items = []
    total = 0.0

    for pid, qty in cart.items():
        p = Product.query.get(int(pid))
        if p:
            items.append({"product": p, "qty": qty, "subtotal": p.price * qty}) 
            total += p.price * qty

    return render_template("cart.html", items=items, total=total) 

@bp.route("/cart/update", methods=["POST"])
def cart_update():
    cart = get_cart()

    for pid, qty in request.form.items():
        if pid.startswith("qty_"):
            product_id = pid.split("_", 1)[1]
            try:
                q = int(qty)
            except:
                q = 0 

            if q <= 0:
                cart.pop(product_id, None)
            else:
                cart[product_id] = q

    save_cart(cart)
    flash("Cart updated", "success")
    return redirect(url_for("main.cart"))

@bp.route("/cart/clear")
def cart_clear():
    session.pop("cart", None)
    flash("Cart cleared", "info")
    return redirect(url_for("main.cart"))

# ---------- Checkout ----------
@bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    cart = get_cart()
    if not cart:
        flash("Cart is empty", "warning")
        return redirect(url_for("main.home"))

    form = CheckoutForm()
    items = []
    total = 0

    for pid, qty in cart.items():
        p = Product.query.get(int(pid))
        if p:
            items.append((p, qty)) 
            total += p.price * qty

    if form.validate_on_submit():
        
        # --- DUMMY PAYMENT PROCESSING ---
        payment_successful = True 

        if payment_successful:
            # 1. Create the Order
            order = Order(
                user_id=current_user.id if current_user.is_authenticated else None,
                fullname=form.fullname.data,
                email=form.email.data,
                address=form.address.data,
                total=total
            )
            db.session.add(order)
            db.session.commit() 

            # 2. Add Order Items and Update Stock
            for p, qty in items:
                # Add OrderItem
                oi = OrderItem(order_id=order.id, product_id=p.id, name=p.name, price=p.price, quantity=qty)
                db.session.add(oi)
                
                # --- STOCK DECREMENT LOGIC ---
                product_to_update = Product.query.get(p.id)
                if product_to_update and product_to_update.stock >= qty:
                    product_to_update.stock -= qty
            
            db.session.commit() 
            
            # 3. Finalize
            session.pop("cart", None)
            flash("Order placed and payment confirmed successfully!", "success")
            return redirect(url_for("main.orders"))
        
        else:
            flash("Payment failed. Please check your card details.", "danger")


    # Pre-fill data for logged-in users on GET request
    if current_user.is_authenticated and request.method == "GET":
        form.fullname.data = current_user.username
        form.email.data = current_user.email

    return render_template("checkout.html", form=form, items=items, total=total)

@bp.route("/orders")
@login_required
def orders():
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.id.desc()).all()
    return render_template("orders.html", orders=user_orders)

# ---------- About / Contact ----------
@bp.route("/about")
def about():
    return render_template("about.html")

@bp.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        flash("Thank you for your message. We'll respond soon.", "success")
        return redirect(url_for("main.home"))
    return render_template("contact.html", form=form)

# ---------- Admin ----------
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Admin access required", "danger")
            return redirect(url_for("main.admin_login"))
        return f(*args, **kwargs)
    return wrapped

@bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.check_password(form.password.data) and user.is_admin:
            login_user(user)
            flash("Admin logged in", "success")
            return redirect(url_for("main.admin_dashboard"))

        flash("Invalid admin credentials", "danger")
    return render_template("admin/admin_login.html", form=form)

@bp.route("/admin")
@admin_required
def admin_dashboard():
    orders = Order.query.order_by(Order.id.desc()).limit(10).all()
    products = Product.query.order_by(Product.id.desc()).limit(5).all()
    return render_template("admin/dashboard.html", orders=orders, products=products)

@bp.route("/admin/products")
@admin_required
def admin_products():
    products = Product.query.order_by(Product.id.desc()).all()
    return render_template("admin/products.html", products=products)

# --- CORRECTED: admin_product_create ---
@bp.route("/admin/products/create", methods=["GET", "POST"])
@admin_required
def admin_product_create():
    form = ProductForm()
    
    if form.validate_on_submit():
        
        image_path = "https://via.placeholder.com/300x200?text=Product" 
        
        if form.image.data:
            filename = photos.save(form.image.data)
            image_path = url_for('static', filename='uploads/' + filename) 
        
        p = Product(
            name=form.name.data,
            price=form.price.data,
            description=form.description.data,
            image_url=image_path, 
            category=form.category.data or "General",
            stock=form.stock.data or 0
        )
        db.session.add(p)
        db.session.commit()
        flash("Product created", "success")
        return redirect(url_for("main.admin_products"))

    return render_template("admin/product_form.html", form=form, action="Create")
# ------------------------------------

# --- CORRECTED: admin_product_edit ---
@bp.route("/admin/products/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_product_edit(product_id):
    p = Product.query.get_or_404(product_id)
    form = ProductForm(obj=p) 
    
    if form.validate_on_submit():
        
        if form.image.data:
            filename = photos.save(form.image.data)
            p.image_url = url_for('static', filename='uploads/' + filename)
        
        p.name = form.name.data
        p.price = form.price.data
        p.description = form.description.data
        p.category = form.category.data
        p.stock = form.stock.data
        db.session.commit()

        flash("Product updated", "success")
        return redirect(url_for("main.admin_products"))

    return render_template("admin/product_form.html", form=form, action="Edit", p=p) 
# ------------------------------------

@bp.route("/admin/products/<int:product_id>/delete", methods=["POST"])
@admin_required
def admin_product_delete(product_id):
    p = Product.query.get_or_404(product_id)
    db.session.delete(p)
    db.session.commit()
    flash("Product deleted", "info")
    return redirect(url_for("main.admin_products"))