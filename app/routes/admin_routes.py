from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user # Giữ nguyên import này
from app.models import User, Job # Thêm Job vào đây cho đủ
from app import db
from werkzeug.security import generate_password_hash
import os
from werkzeug.utils import secure_filename
from flask import current_app
from datetime import datetime
from functools import wraps


# --- KHAI BÁO CẦN THIẾT ---
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
admin_bp = Blueprint('admin', __name__, template_folder='../templates/admin')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def admin_required(func):
    """Decorator để kiểm tra xem người dùng hiện tại có phải là Admin không."""
    @login_required
    def wrapper(*args, **kwargs):
        # Kiểm tra người dùng đã đăng nhập chưa và có vai trò là 'admin' không
        # THAY 'admin' VÀO ĐÂY BẰNG GIÁ TRỊ ROLE CỦA ADMIN TRONG DB CỦA BẠN
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Bạn không có quyền truy cập trang quản trị.', 'danger')
            return redirect(url_for('main.index')) # Chuyển hướng về trang chủ
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__ # Giữ tên hàm gốc
    return wrapper
# --- ROUTES QUẢN TRỊ ---

# 🏠 Trang admin chính
@admin_bp.route('/')
@admin_required # Áp dụng quyền Admin
def admin_dashboard():
    # Thêm kiểm tra quyền admin vào đây không cần thiết vì đã dùng @admin_required
    total_users = User.query.count()
    # Nếu tin_tuyen_dung muốn hiển thị tất cả job
    tin_tuyen_dung_list = Job.query.all() 
    return render_template('admin/index.html', 
                           tai_khoan=User.query.all(), 
                           ctv=[], 
                           tin_tuyen_dung=tin_tuyen_dung_list, 
                           total_users=total_users)


# 📋 Danh sách tài khoản (và các route liên quan)
@admin_bp.route('/users')
@admin_required
def user_list():
    users = User.query.all()
    return render_template('admin/users/index.html', users=users)

@admin_bp.route('/users/create', methods=['GET', 'POST'])
@admin_required
def user_add():
    # ... (giữ nguyên logic thêm user)
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        if User.query.filter_by(email=email).first():
            flash('Email đã được đăng ký.', 'danger')
            return redirect(url_for('admin.user_add'))

        hashed_pw = generate_password_hash(password)
        # THÊM 'is_admin' NẾU CẦN THIẾT CHO MODEL USER
        user = User(full_name=full_name, email=email, password_hash=hashed_pw, role=role) 

        db.session.add(user)
        db.session.commit()
        flash('Thêm tài khoản thành công!', 'success')
        return redirect(url_for('admin.user_list'))

    return render_template('admin/users/create.html')

@admin_bp.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def user_edit(id):
    # ... (giữ nguyên logic chỉnh sửa user)
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        user.full_name = request.form['full_name']
        user.email = request.form['email']
        user.role = request.form['role']

        new_password = request.form.get('password', '').strip()
        if new_password:
            user.password_hash = generate_password_hash(new_password)

        db.session.commit()
        flash('Cập nhật tài khoản thành công!', 'success')
        return redirect(url_for('admin.user_list'))

    return render_template('admin/users/edit.html', user=user)


@admin_bp.route('/users/delete/<int:id>', methods=['POST'])
@admin_required
def user_delete(id):
    # ... (giữ nguyên logic xóa user)
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    flash('Đã xóa tài khoản!', 'danger')
    return redirect(url_for('admin.user_list'))

# --- ROUTES TUYỂN DỤNG/CTV ---
@admin_bp.route('/recruiters')
@admin_required
def recruiter_list():
    # ... (giữ nguyên logic)
    recruiters = User.query.filter_by(role='recruiter').all()
    return render_template('admin/recruiters/index.html', recruiters=recruiters)

@admin_bp.route('/recruiters/create', methods=['GET', 'POST'])
@admin_required
def recruiter_add():
    # ... (giữ nguyên logic)
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(email=email).first():
            flash('Email đã được đăng ký.', 'danger')
            return redirect(url_for('admin.recruiter_add'))

        hashed_pw = generate_password_hash(password)

        # Upload avatar
        avatar_file = request.files.get('avatar')
        avatar_url = None
        if avatar_file and allowed_file(avatar_file.filename):
            filename = secure_filename(avatar_file.filename)
            # LƯU Ý: Phải đảm bảo 'UPLOAD_FOLDER' đã được cấu hình đúng trong config
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename) 
            avatar_file.save(save_path)
            # LƯU Ý: Đường dẫn này có thể cần thay đổi tùy vào cấu hình static của bạn
            avatar_url = f'/static/uploads/avatars/{filename}' 

        new_recruiter = User(
            full_name=full_name,
            email=email,
            password_hash=hashed_pw,
            role='recruiter', # Role được gán cứng là 'recruiter'
            avatar_url=avatar_url
        )

        db.session.add(new_recruiter)
        db.session.commit()
        flash('Thêm cộng tác viên thành công!', 'success')
        return redirect(url_for('admin.recruiter_list'))

    return render_template('admin/recruiters/create.html')

@admin_bp.route('/recruiters/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def recruiter_edit(id):
    # ... (giữ nguyên logic)
    recruiter = User.query.get_or_404(id)
    if recruiter.role != 'recruiter':
        flash('Không thể chỉnh sửa người không phải cộng tác viên.', 'warning')
        return redirect(url_for('admin.recruiter_list'))

    if request.method == 'POST':
        recruiter.full_name = request.form['full_name']
        recruiter.email = request.form['email']

        new_password = request.form.get('password', '').strip()
        if new_password:
            recruiter.password_hash = generate_password_hash(new_password)

        # Upload avatar mới nếu có
        avatar_file = request.files.get('avatar')
        if avatar_file and allowed_file(avatar_file.filename):
            filename = secure_filename(avatar_file.filename)
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            avatar_file.save(save_path)
            recruiter.avatar_url = f'/static/uploads/avatars/{filename}'

        db.session.commit()
        flash('Cập nhật thông tin cộng tác viên thành công!', 'success')
        return redirect(url_for('admin.recruiter_list'))

    return render_template('admin/recruiters/edit.html', recruiter=recruiter)


@admin_bp.route('/recruiters/delete/<int:id>', methods=['POST'])
@admin_required
def recruiter_delete(id):
    # ... (giữ nguyên logic)
    recruiter = User.query.get_or_404(id)
    if recruiter.role != 'recruiter':
        flash('Không thể xóa người không phải cộng tác viên.', 'danger')
        return redirect(url_for('admin.recruiter_list'))

    db.session.delete(recruiter)
    db.session.commit()
    flash('Đã xóa cộng tác viên!', 'danger')
    return redirect(url_for('admin.recruiter_list'))

@admin_bp.route('/recruiters/view/<int:id>')
@admin_required
def recruiter_view(id):
    # ... (giữ nguyên logic)
    recruiter = User.query.get_or_404(id)
    if recruiter.role != 'recruiter':
        flash('Không thể xem người không phải cộng tác viên.', 'warning')
        return redirect(url_for('admin.recruiter_list'))

    return render_template('admin/recruiters/view.html', recruiter=recruiter)

# --- ROUTES QUẢN LÝ TIN TUYỂN DỤNG ---
@admin_bp.route('/jobs')
@admin_required
def job_list():
    jobs = Job.query.all()
    return render_template('admin/jobs/index.html', jobs=jobs)


@admin_bp.route('/jobs/create', methods=['GET', 'POST'])
@admin_required
def job_add():
    # ... (giữ nguyên logic)
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        requirements = request.form.get('requirements', '')
        salary_range = request.form.get('salary_range', '')
        location = request.form.get('location', '')
        deadline_str = request.form.get('deadline', '')
        # SỬA: Lấy created_by từ người dùng hiện tại (Admin)
        created_by = current_user.id 

        deadline = datetime.strptime(deadline_str, '%Y-%m-%d') if deadline_str else None

        new_job = Job(
            title=title,
            description=description,
            requirements=requirements,
            salary_range=salary_range,
            location=location,
            deadline=deadline,
            created_by=created_by
        )

        db.session.add(new_job)
        db.session.commit()
        flash('Đăng tin tuyển dụng thành công!', 'success')
        return redirect(url_for('admin.job_list'))

    # Lấy danh sách các user để chọn người đăng tin (Không cần nữa nếu job do Admin tạo)
    # Nếu muốn cho Admin chọn người tạo: users = User.query.all()
    return render_template('admin/jobs/create.html')


@admin_bp.route('/jobs/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def job_edit(id):
    # ... (giữ nguyên logic)
    job = Job.query.get_or_404(id)
    if request.method == 'POST':
        job.title = request.form['title']
        job.description = request.form['description']
        job.requirements = request.form.get('requirements', '')
        job.salary_range = request.form.get('salary_range', '')
        job.location = request.form.get('location', '')
        deadline_str = request.form.get('deadline', '')
        job.deadline = datetime.strptime(deadline_str, '%Y-%m-%d') if deadline_str else None
        db.session.commit()
        flash('Cập nhật tin tuyển dụng thành công!', 'success')
        return redirect(url_for('admin.job_list'))

    return render_template('admin/jobs/edit.html', job=job)


@admin_bp.route('/jobs/delete/<int:id>', methods=['POST'])
@admin_required
def job_delete(id):
    # ... (giữ nguyên logic)
    job = Job.query.get_or_404(id)
    db.session.delete(job)
    db.session.commit()
    flash('Đã xóa tin tuyển dụng!', 'danger')
    return redirect(url_for('admin.job_list'))


@admin_bp.route('/jobs/view/<int:id>')
@admin_required
def job_view(id):
    # ... (giữ nguyên logic)
    job = Job.query.get_or_404(id)
    return render_template('admin/jobs/view.html', job=job)

# --- LƯU Ý: XÓA HÀM DƯ THỪA ---
# Xóa hàm 'check_credentials' vì nó không còn được sử dụng khi đã có Flask-Login và Decorator.
# def check_credentials(username, password):
#     ...