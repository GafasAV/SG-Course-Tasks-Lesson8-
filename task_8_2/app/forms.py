from flask_wtf import FlaskForm

from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Email, Length


class LoginForm(FlaskForm):
    """
    User Login Form override.
    Use at login.html.
    
    """
    username = StringField(
        'Username', validators=[InputRequired(), Length(min=4, max=16)])
    password = PasswordField(
        'Password', validators=[InputRequired(), Length(min=6, max=32)])


class RegisterForm(FlaskForm):
    """
    User Registration Form override.
    Use at register.html
    
    """
    username = StringField(
        'Username', validators=[InputRequired(), Length(min=4, max=16)])
    email = StringField(
        'Email', validators=[InputRequired(), Email(message="Invalid Email")])
    password = PasswordField(
        'Password', validators=[InputRequired(), Length(min=6, max=32)])


class UserControlForm(FlaskForm):
    """
    Personal User Control Form for get, save, find data at DB.
    Use at info.html
    
    """
    currencys = SubmitField(label='All Currencys')
    online = SubmitField(label='Get Online and Save')
    curr_name = StringField(
        'Currency', validators=[InputRequired()])
    get_history = SubmitField(label='Show History')