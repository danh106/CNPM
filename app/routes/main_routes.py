from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from app import db
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from app.models import Job
from app.models import Applicant
from datetime import datetime
import os
from app.models import UserImages
from app.models import Job, Application


main_bp = Blueprint('main', __name__)
serializer = URLSafeTimedSerializer('super-secret-key')


@main_bp.route('/')
def index():
    jobs = Job.query.order_by(Job.created_at.desc()).all()

    user_data = {
        "is_logged_in": current_user.is_authenticated,
        "username": current_user.full_name if current_user.is_authenticated else "Log in"
    }

    return render_template('index.html', user=user_data, jobs=jobs)

@main_bp.route('/admin')
@login_required
def admin_index():
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập!', 'danger')
        return redirect(url_for('main.login'))
    return render_template('admin/index.html')

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
                return redirect(url_for('main.admin_index'))
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
        new_applicant = Applicant(user_id=new_user.id)
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
    applicant = Applicant.query.filter_by(user_id=user_id).first()
    if not applicant:
        applicant = Applicant(user_id=user_id)
        db.session.add(applicant)
        db.session.commit()

    if current_user.role != 'admin' and current_user.id != user_id:
        flash("Bạn không có quyền xem hồ sơ này.", "danger")
        return redirect(url_for('main.index'))

    user = User.query.get(user_id)
    user_images = UserImages.query.filter_by(user_id=user_id).order_by(UserImages.uploaded_at.desc()).all()
    avatar_url = user_images[0].image_url if user_images else url_for('static', filename='img/default-avatar.png')

    if request.method == 'POST':
        # ✅ Cập nhật thông tin ứng viên
        applicant.phone_number = request.form.get('phone_number', applicant.phone_number)
        applicant.position_applied = request.form.get('position_applied', applicant.position_applied)

        # ✅ Cập nhật email (bảng User)
        new_email = request.form.get('email')
        if new_email and new_email != user.email:
            user.email = new_email

        # ✅ Xử lý file CV
        cv_file = request.files.get('cv_file')
        if cv_file and cv_file.filename:
            cv_filename = secure_filename(cv_file.filename)
            cv_path = os.path.join(current_app.root_path, 'static/uploads/cv', cv_filename)
            os.makedirs(os.path.dirname(cv_path), exist_ok=True)
            cv_file.save(cv_path)
            applicant.resume_url = url_for('static', filename=f'uploads/cv/{cv_filename}')

        # ✅ Ảnh đại diện
        avatar_file = request.files.get('avatar_file')
        if avatar_file and avatar_file.filename:
            avatar_filename = secure_filename(avatar_file.filename)
            avatar_path = os.path.join(current_app.root_path, 'static/uploads/avatar', avatar_filename)
            os.makedirs(os.path.dirname(avatar_path), exist_ok=True)
            avatar_file.save(avatar_path)

            new_image = UserImages(
                user_id=user_id,
                image_url=url_for('static', filename=f'uploads/avatar/{avatar_filename}')
            )
            db.session.add(new_image)
            db.session.flush()
            applicant.avatar_image_id = new_image.id
            avatar_url = new_image.image_url

        db.session.commit()
        flash('Cập nhật hồ sơ thành công!', 'success')
        return redirect(url_for('main.applicant_profile', user_id=user_id))

    return render_template('applicant_profile.html', applicant=applicant, avatar_url=avatar_url)


@main_bp.route('/job/<int:job_id>')
@login_required
def job_details(job_id):
    job = Job.query.get_or_404(job_id)
    
    applicant = Applicant.query.filter_by(user_id=current_user.id).first()
    
    return render_template('job_details.html', job=job, applicant=applicant, user=current_user)

@main_bp.route('/apply/<int:job_id>', methods=['POST'])
@login_required
def apply_job(job_id):
    job = Job.query.get_or_404(job_id)

    # Kiểm tra nếu đã nộp trước đó
    existing = Application.query.filter_by(user_id=current_user.id, job_id=job.id).first()
    if existing:
        flash('Bạn đã nộp hồ sơ cho công việc này rồi.', 'warning')
        return redirect(url_for('main.job_details', job_id=job.id))

    cv_file = request.files.get('cv')
    cover_letter = request.form.get('coverletter')

    new_app = Application(
        user_id=current_user.id,
        job_id=job.id,
        cover_letter=cover_letter,
        resume_url=cv_file.filename if cv_file else None,
    )
    db.session.add(new_app)
    db.session.commit()

    flash('Nộp hồ sơ thành công! Chúng tôi sẽ liên hệ sớm nhất có thể.', 'success')
    return redirect(url_for('main.job_details', job_id=job.id))

@main_bp.route('/my-applications')
@login_required
def my_applications():
    applications = (
        Application.query
        .filter_by(user_id=current_user.id)
        .order_by(Application.applied_at.desc())
        .all()
    )
    return render_template('my_applications.html', applications=applications)


@main_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            token = serializer.dumps(user.email)
            reset_url = url_for('main.reset_password', token=token, _external=True)
            # Gửi email reset_url cho user ở đây
            flash('Một liên kết đặt lại mật khẩu đã được gửi đến email của bạn.', 'info')
        else:
            flash('Email không tồn tại trong hệ thống.', 'danger')
        return redirect(url_for('main.login'))
    return render_template('forgot_password.html')


@main_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, max_age=3600)  # Token hợp lệ trong 1h
    except (SignatureExpired, BadSignature):
        flash('Liên kết đặt lại mật khẩu đã hết hạn hoặc không hợp lệ.', 'danger')
        return redirect(url_for('main.forgot_password'))

    user = User.query.filter_by(email=email).first_or_404()

    if request.method == 'POST':
        new_password = request.form.get('password')
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        flash('Đã đặt lại mật khẩu. Vui lòng đăng nhập bằng mật khẩu mới.', 'success')
        return redirect(url_for('main.login'))

    return render_template('reset_password.html', token=token)
