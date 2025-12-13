from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, NumberRange, EqualTo, Regexp

# 1. NEW: Import for file uploads
from flask_wtf.file import FileField, FileAllowed 


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=4)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match")]
    )
    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class ProductForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    price = FloatField("Price", validators=[DataRequired(), NumberRange(min=0)])
    description = TextAreaField("Description")
    
    # 2. UPDATED: Changed from StringField('Image URL') to FileField('Product Image...')
    image = FileField(
        "Product Image (JPEG/PNG)", 
        validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')]
    )
    # --------------------------------------------------------------------------------
    
    category = StringField("Category")
    stock = IntegerField("Stock", validators=[NumberRange(min=0)])
    submit = SubmitField("Save")

class CheckoutForm(FlaskForm):
    # Shipping/Billing Fields
    fullname = StringField("Full name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    address = TextAreaField("Address", validators=[DataRequired()])
    
    # --- PAYMENT FIELDS ---
    card_number = StringField("Card Number", 
                              validators=[DataRequired(), Length(min=16, max=16, message="Card must be 16 digits")])
    expiry_date = StringField("MM/YY", 
                              validators=[DataRequired(), Regexp(r'^\d{2}\/\d{2}$', message="Format must be MM/YY")])
    cvc = StringField("CVC", 
                      validators=[DataRequired(), Length(min=3, max=4, message="CVC must be 3 or 4 digits")])
    # ----------------------
    
    submit = SubmitField("Place Order")

class ContactForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    message = TextAreaField("Message", validators=[DataRequired()])
    submit = SubmitField("Send")