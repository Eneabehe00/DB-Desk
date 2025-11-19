from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models.user import User
from app.forms.auth import LoginForm, RegistrationForm, ChangePasswordForm

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Pagina di login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Il tuo account è stato disattivato. Contatta l\'amministratore.', 'error')
                return render_template('auth/login.html', form=form)
            
            login_user(user, remember=form.remember_me.data)
            user.update_last_login()
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.dashboard')
            
            flash(f'Benvenuto, {user.full_name}!', 'success')
            return redirect(next_page)
        else:
            flash('Username o password non validi.', 'error')
    
    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Pagina di registrazione"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        
        db.session.add(user)
        db.session.commit()
        # Auto-login dopo registrazione
        login_user(user, remember=True)
        user.update_last_login()
        flash(f'Benvenuto, {user.full_name}! Registrazione completata.', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout utente"""
    logout_user()
    flash('Logout effettuato con successo.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Cambio password"""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Password cambiata con successo!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Password attuale non corretta.', 'error')
    
    return render_template('auth/change_password.html', form=form)


@auth_bp.route('/profile')
@login_required
def profile():
    """Profilo utente"""
    return render_template('auth/profile.html', user=current_user)