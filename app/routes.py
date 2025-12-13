from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from . import db
from .models import User, Product, Order, OrderItem, Notification
from .forms import RegisterForm, LoginForm, ProductForm, CheckoutForm, ContactForm
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename

bp = Blueprint("main", __name__)

# ---------- Email Helper Functions ----------
def send_order_confirmed_email(customer_email, order_id, customer_name, order_total):
    """Send order confirmation email to customer"""
    msg = Message(
        subject=f"Order #{order_id} Confirmed!",
        recipients=[customer_email],
        html=f"""
        <h3>Hello {customer_name},</h3>
        <p>Your order <strong>#{order_id}</strong> has been confirmed!</p>
        <p><strong>Order Total:</strong> ${order_total:.2f}</p>
        <p>Your order will be processed and shipped soon. You will receive tracking information shortly.</p>
        <p>Thank you for shopping with us!</p>
        """
    )
    try:
        from . import mail
        mail.send(msg)
    except:
        # Email not configured, skip silently
        pass

def send_order_cancelled_email(customer_email, order_id, customer_name):
    """Send order cancellation email to customer"""
    msg = Message(
        subject=f"Order #{order_id} Cancelled",
        recipients=[customer_email],
        html=f"""
        <h3>Hello {customer_name},</h3>
        <p>Your order <strong>#{order_id}</strong> has been cancelled by our admin.</p>
        <p>If you did not authorize this cancellation or have any questions, please contact our support team.</p>
        <p>Thank you for your understanding.</p>
        """
    )
    try:
        from . import mail
        mail.send(msg)
    except:
        # Email not configured, skip silently
        pass


import secrets, string

def generate_order_code(length=10):
    alphabet = string.ascii_uppercase + string.digits
    for _ in range(10):
        code = ''.join(secrets.choice(alphabet) for _ in range(length))
        # ensure uniqueness
        if not Order.query.filter_by(order_code=code).first():
            return code
    # fallback: longer random string
    return ''.join(secrets.choice(alphabet) for _ in range(length+4))


def log_notification_fallback(customer_email, text):
    """Append notification to a local log file as a fallback when email isn't sent."""
    try:
        logfile = current_app.config.get('NOTIFICATION_LOG', 'notifications.log')
        with open(logfile, 'a', encoding='utf-8') as f:
            f.write(f"[{customer_email}] {text}\n")
    except Exception:
        pass

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
    """Display shopping cart"""
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
    """Update cart quantities"""
    cart = get_cart()

    # Process all quantity updates from form fields
    for field_name, value in request.form.items():
        if field_name.startswith("qty_"):
            product_id = field_name.replace("qty_", "")
            try:
                quantity = int(value)
            except (ValueError, TypeError):
                quantity = 0
            
            # Remove item if quantity is 0 or less
            if quantity <= 0:
                cart.pop(product_id, None)
            else:
                cart[product_id] = quantity

    save_cart(cart)
    flash("Cart updated successfully", "success")
    return redirect(url_for("main.cart"))

@bp.route("/cart/remove", methods=["POST"])
def remove_from_cart():
    """Remove item from cart via form submission"""
    product_id = request.form.get("product_id")
    cart = get_cart()
    
    if product_id and product_id in cart:
        del cart[product_id]
        save_cart(cart)
        flash("Item removed from cart", "success")
    
    return redirect(url_for("main.cart"))

@bp.route("/cart/clear")
def cart_clear():
    """Clear entire cart"""
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
            # assign unique alphanumeric order code
            order.order_code = generate_order_code(10)
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
            flash("Order placed successfully! Please wait for admin confirmation.", "info")
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

# ---------- Admin Order Management ----------
@bp.route("/admin/orders/<int:order_id>")
@admin_required
def admin_order_details(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template("admin/order_details.html", order=order)

@bp.route("/admin/orders/<int:order_id>/confirm", methods=["POST"])
@admin_required
def admin_confirm_order(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Update order status to confirmed
    order.status = 'confirmed'
    
    # Update stock when order is confirmed
    for item in order.items:
        product = Product.query.get(item.product_id)
        if product:
            product.stock -= item.quantity
    
    db.session.commit()
    
    # Send confirmation email to customer
    send_order_confirmed_email(order.email, order_id, order.fullname, order.total)
    # Create in-app notification for registered users
    try:
        if order.user_id:
            n = Notification(user_id=order.user_id, message=f"Your order #{order_id} has been confirmed.")
            db.session.add(n)
            db.session.commit()
        else:
            # Guest order: fallback log
            log_notification_fallback(order.email, f"Order #{order_id} confirmed for {order.fullname}")
    except Exception:
        # Ensure notification errors don't block admin flow
        pass
    
    flash(f"Order #{order_id} confirmed! Stock updated. Customer notified via email.", "success")
    return redirect(url_for("main.admin_dashboard"))

@bp.route("/admin/orders/<int:order_id>/cancel", methods=["POST"])
@admin_required
def admin_cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    customer_email = order.email
    customer_name = order.fullname
    
    # Delete OrderItems first (foreign key constraint)
    OrderItem.query.filter_by(order_id=order_id).delete()
    db.session.delete(order)
    db.session.commit()
    
    # Send cancellation email to customer
    send_order_cancelled_email(customer_email, order_id, customer_name)
    # Create notification for user (if registered) or fallback log
    try:
        if order.user_id:
            n = Notification(user_id=order.user_id, message=f"Your order #{order_id} has been cancelled by admin.")
            db.session.add(n)
            db.session.commit()
        else:
            log_notification_fallback(customer_email, f"Order #{order_id} cancelled for {customer_name}")
    except Exception:
        pass
    
    flash(f"Order #{order_id} cancelled. Customer notified via email.", "warning")
    return redirect(url_for("main.admin_dashboard"))


# ---------- Notifications UI ----------
@bp.route('/notifications')
@login_required
def notifications():
    notes = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template('notifications.html', notifications=notes)


@bp.route('/notifications/<int:note_id>/read', methods=['POST'])
@login_required
def mark_notification_read(note_id):
    n = Notification.query.get_or_404(note_id)
    if n.user_id != current_user.id:
        flash('Not authorized', 'danger')
        return redirect(url_for('main.notifications'))
    n.is_read = True
    db.session.commit()
    return redirect(url_for('main.notifications'))

@bp.route('/notifications/clear-all', methods=['POST'])
@login_required
def clear_all_notifications():
    Notification.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash('All notifications cleared', 'success')
    return redirect(url_for('main.notifications'))