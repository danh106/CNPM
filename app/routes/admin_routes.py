from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import User
from app.models import Job
from app import db
from werkzeug.security import generate_password_hash
import os
from werkzeug.utils import secure_filename
from flask import current_app
from datetime import datetime

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
admin_bp = Blueprint('admin', __name__, template_folder='../templates/admin')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 🏠 Trang admin chính
@admin_bp.route('/')
def admin_dashboard():
    # bạn có thể gửi thêm số liệu tổng quan ở đây
    total_users = User.query.count()
    return render_template('admin/index.html', tai_khoan=User.query.all(), ctv=[], tin_tuyen_dung=[], total_users=total_users)


# 📋 Danh sách tài khoản
@admin_bp.route('/users')
def user_list():
    users = User.query.all()
    return render_template('admin/users/index.html', users=users)


# ➕ Thêm tài khoản
@admin_bp.route('/users/create', methods=['GET', 'POST'])
def user_add():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        # kiểm tra email tồn tại
        if User.query.filter_by(email=email).first():
            flash('Email đã được đăng ký.', 'danger')
            return redirect(url_for('admin.user_add'))

        hashed_pw = generate_password_hash(password)
        user = User(full_name=full_name, email=email, password_hash=hashed_pw, role=role)

        db.session.add(user)
        db.session.commit()
        flash('Thêm tài khoản thành công!', 'success')
        return redirect(url_for('admin.user_list'))

    return render_template('admin/users/create.html')


# ✏️ Sửa tài khoản
@admin_bp.route('/users/edit/<int:id>', methods=['GET', 'POST'])
def user_edit(id):
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        user.full_name = request.form['full_name']
        user.email = request.form['email']
        user.role = request.form['role']

        # nếu client có gửi mật khẩu mới → cập nhật hash
        new_password = request.form.get('password', '').strip()
        if new_password:
            user.password_hash = generate_password_hash(new_password)

        db.session.commit()
        flash('Cập nhật tài khoản thành công!', 'success')
        return redirect(url_for('admin.user_list'))

    return render_template('admin/users/edit.html', user=user)


# ❌ Xóa tài khoản (POST)
@admin_bp.route('/users/delete/<int:id>', methods=['POST'])
def user_delete(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    flash('Đã xóa tài khoản!', 'danger')
    return redirect(url_for('admin.user_list'))

# tuyen dung
@admin_bp.route('/recruiters')
def recruiter_list():
    recruiters = User.query.filter_by(role='recruiter').all()
    return render_template('admin/recruiters/index.html', recruiters=recruiters)


# ----------------------------
# THÊM CỘNG TÁC VIÊN
# ----------------------------
@admin_bp.route('/recruiters/create', methods=['GET', 'POST'])
def recruiter_add():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']

        # Kiểm tra email tồn tại
        if User.query.filter_by(email=email).first():
            flash('Email đã được đăng ký.', 'danger')
            return redirect(url_for('admin.recruiter_add'))

        # Hash password
        hashed_pw = generate_password_hash(password)

        # Upload avatar
        avatar_file = request.files.get('avatar')
        avatar_url = None
        if avatar_file and allowed_file(avatar_file.filename):
            filename = secure_filename(avatar_file.filename)
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            avatar_file.save(save_path)
            avatar_url = f'/static/uploads/avatars/{filename}'

        new_recruiter = User(
            full_name=full_name,
            email=email,
            password_hash=hashed_pw,
            role='recruiter',
            avatar_url=avatar_url
        )

        db.session.add(new_recruiter)
        db.session.commit()
        flash('Thêm cộng tác viên thành công!', 'success')
        return redirect(url_for('admin.recruiter_list'))

    return render_template('admin/recruiters/create.html')


# ----------------------------
# SỬA CỘNG TÁC VIÊN
# ----------------------------
@admin_bp.route('/recruiters/edit/<int:id>', methods=['GET', 'POST'])
def recruiter_edit(id):
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


# ----------------------------
# XÓA CỘNG TÁC VIÊN
# ----------------------------
@admin_bp.route('/recruiters/delete/<int:id>', methods=['POST'])
def recruiter_delete(id):
    recruiter = User.query.get_or_404(id)
    if recruiter.role != 'recruiter':
        flash('Không thể xóa người không phải cộng tác viên.', 'danger')
        return redirect(url_for('admin.recruiter_list'))

    db.session.delete(recruiter)
    db.session.commit()
    flash('Đã xóa cộng tác viên!', 'danger')
    return redirect(url_for('admin.recruiter_list'))


# ----------------------------
# XEM THÔNG TIN CỘNG TÁC VIÊN
# ----------------------------
@admin_bp.route('/recruiters/view/<int:id>')
def recruiter_view(id):
    recruiter = User.query.get_or_404(id)
    if recruiter.role != 'recruiter':
        flash('Không thể xem người không phải cộng tác viên.', 'warning')
        return redirect(url_for('admin.recruiter_list'))

    return render_template('admin/recruiters/view.html', recruiter=recruiter)

@admin_bp.route('/jobs')
def job_list():
    jobs = Job.query.all()
    return render_template('admin/jobs/index.html', jobs=jobs)


# ----------------------------
# TẠO BÀI TUYỂN DỤNG MỚI
# ----------------------------
@admin_bp.route('/jobs/create', methods=['GET', 'POST'])
def job_add():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        requirements = request.form.get('requirements', '')
        salary_range = request.form.get('salary_range', '')
        location = request.form.get('location', '')
        deadline_str = request.form.get('deadline', '')
        created_by = int(request.form.get('created_by', 1))  # id người tạo, mặc định admin 1

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

    # Lấy danh sách các user để chọn người đăng tin
    users = User.query.all()
    return render_template('admin/jobs/create.html', users=users)


# ----------------------------
# SỬA BÀI TUYỂN DỤNG
# ----------------------------
@admin_bp.route('/jobs/edit/<int:id>', methods=['GET', 'POST'])
def job_edit(id):
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


# ----------------------------
# XÓA BÀI TUYỂN DỤNG
# ----------------------------
@admin_bp.route('/jobs/delete/<int:id>', methods=['POST'])
def job_delete(id):
    job = Job.query.get_or_404(id)
    db.session.delete(job)
    db.session.commit()
    flash('Đã xóa tin tuyển dụng!', 'danger')
    return redirect(url_for('admin.job_list'))


# ----------------------------
# XEM CHI TIẾT TIN TUYỂN DỤNG
# ----------------------------
@admin_bp.route('/jobs/view/<int:id>')
def job_view(id):
    job = Job.query.get_or_404(id)
    return render_template('admin/jobs/view.html', job=job)