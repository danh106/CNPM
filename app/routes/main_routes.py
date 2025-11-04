from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
<<<<<<< HEAD
from app.models import User
=======
>>>>>>> c99447b8bc428eb56c679bb2bee007b7eefb021c
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from app import db
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
<<<<<<< HEAD
from app.models import Job
from app.models import Applicant
=======
from datetime import datetime
import os
from app.models import User
>>>>>>> c99447b8bc428eb56c679bb2bee007b7eefb021c

main_bp = Blueprint('main', __name__)
serializer = URLSafeTimedSerializer('super-secret-key')

# ------------------ Models ------------------ #

class Applicant(db.Model):
    __tablename__ = 'applicants'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    position_applied = db.Column(db.String(100), nullable=True)
    resume_url = db.Column(db.String(255), nullable=True)
    status = db.Column(db.Enum('Đang xử lý', 'Đã phỏng vấn', 'Đã nhận việc'), default='Đang xử lý')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('applicant', uselist=False))


class UserImages(db.Model):
    __tablename__ = 'user_images'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

# ------------------ Routes ------------------ #


@main_bp.route('/')
def index():
    jobs = Job.query.order_by(Job.created_at.desc()).all()

    user_data = {
        "is_logged_in": current_user.is_authenticated,
        "username": current_user.full_name if current_user.is_authenticated else "Log in"
    }

    return render_template('index.html', user=user_data, jobs=jobs)



@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Đăng nhập thành công!', 'success')
            session['user_id'] = user.id
            session['user_role'] = user.role
            session['user_name'] = user.full_name
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('main.applicant_profile', user_id=user.id))
        else:
            flash('Email hoặc mật khẩu không đúng!', 'danger')
    return render_template('login.html')


@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']
        role = 'applicant'
        if User.query.filter_by(email=email).first():
            flash('Email này đã được đăng ký!', 'danger')
            return redirect(url_for('main.register'))
        new_user = User(
            full_name=full_name,
            email=email,
            password_hash=generate_password_hash(password),
            role=role
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html')


@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('Bạn đã đăng xuất!', 'info')
    return redirect(url_for('main.login'))


@main_bp.route('/applicant/<int:user_id>', methods=['GET', 'POST'])
@login_required
def applicant_profile(user_id):
    applicant = Applicant.query.filter_by(user_id=user_id).first_or_404()
    if current_user.role != 'admin' and current_user.id != user_id:
        flash("Bạn không có quyền xem hồ sơ này.", "danger")
        return redirect(url_for('main.index'))

    user_images = UserImages.query.filter_by(user_id=user_id).order_by(UserImages.uploaded_at.desc()).all()
    avatar_url = user_images[0].image_url if user_images else url_for('static', filename='img/default-avatar.png')

    if request.method == 'POST':
        applicant.phone_number = request.form.get('phone_number', applicant.phone_number)
        applicant.position_applied = request.form.get('position_applied', applicant.position_applied)

        # Upload CV
        cv_file = request.files.get('cv_file')
        if cv_file and cv_file.filename:
            cv_filename = secure_filename(cv_file.filename)
            cv_path = os.path.join(current_app.root_path, 'static/uploads/cv', cv_filename)
            os.makedirs(os.path.dirname(cv_path), exist_ok=True)
            cv_file.save(cv_path)
            applicant.resume_url = url_for('static', filename=f'uploads/cv/{cv_filename}')

        avatar_file = request.files.get('avatar_file')
        if avatar_file and avatar_file.filename:
            avatar_filename = secure_filename(avatar_file.filename)
            avatar_path = os.path.join(current_app.root_path, 'static/uploads/avatar', avatar_filename)
            os.makedirs(os.path.dirname(avatar_path), exist_ok=True)
            avatar_file.save(avatar_path)
            new_image = UserImages(user_id=user_id, image_url=url_for('static', filename=f'uploads/avatar/{avatar_filename}'))
            db.session.add(new_image)
            avatar_url = new_image.image_url

        db.session.commit()
        flash('Cập nhật hồ sơ thành công!', 'success')
        return redirect(url_for('main.applicant_profile', user_id=user_id))

        flash('Đã đặt lại mật khẩu. Vui lòng đăng nhập bằng mật khẩu mới.', 'success')
        return redirect(url_for('main.login'))

    return render_template('reset_password.html', token=token)
    applicant = Applicant.query.filter_by(user_id=user_id).first_or_404()
    if current_user.role != 'admin' and current_user.id != user_id:
        flash("Bạn không có quyền xem hồ sơ này.", "danger")
        return redirect(url_for('main.index'))

@main_bp.route('/job/<int:job_id>')
def job_details(job_id):
    job = Job.query.get_or_404(job_id)
    return render_template('job_details.html', job=job)
    
@main_bp.route('/job/<int:job_id>/apply', methods=['POST'])
def apply_job(job_id):
    job = Job.query.get_or_404(job_id)
    
    name = request.form['name']
    email = request.form['email']
    portfolio = request.form.get('portfolio')
    coverletter = request.form.get('coverletter')
    cv_file = request.files.get('cv')
    
    # Xử lý lưu file CV và tạo record Apply (nếu bạn có model Apply)
    # Ví dụ:
    # application = JobApplication(job_id=job.id, name=name, email=email, ...)
    # db.session.add(application)
    # db.session.commit()
    
    flash('Apply successfully!', 'success')
    return redirect(url_for('job_detail', job_id=job.id))

    