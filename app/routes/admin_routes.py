from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, jsonify
from flask_login import login_required, current_user 
from app.models import User, Job, JobPostDetails, TemplateCV
from werkzeug.security import generate_password_hash
from app import db 
import os
from werkzeug.utils import secure_filename
from flask import current_app
from datetime import datetime, date, timedelta
from functools import wraps
from sqlalchemy import func, or_


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
admin_bp = Blueprint('admin', __name__, template_folder='../templates/admin')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def admin_required(func):
    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Bạn không có quyền truy cập trang quản trị.', 'danger')
            return redirect(url_for('main.index')) 
        return func(*args, **kwargs)
    return wrapper

@admin_bp.route('/')
@admin_required 
def admin_dashboard():
    allusers = User.query.all()
    recruiters = User.query.filter_by(role='recruiter').all()
    tin_tuyen_dung_list = Job.query.all() 
    
    pending_count = db.session.query(JobPostDetails) \
                      .filter_by(approval_status='Pending').count()
                      
    latest_jobs = Job.query.order_by(Job.created_at.desc()).limit(5).all()

    return render_template('admin/index.html', 
                           tai_khoan=allusers,
                           totaluser=len(allusers),
                           ctv=recruiters,
                           tin_tuyen_dung=tin_tuyen_dung_list, 
                           
                           pending_count=pending_count,
                           latest_jobs=latest_jobs
                           )

@admin_bp.route('/users')
@admin_required
def user_list():
    users = User.query.all()
    return render_template('admin/users/index.html', users=users)

@admin_bp.route('/users/create', methods=['GET', 'POST'])
@admin_required
def user_add():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

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

@admin_bp.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def user_edit(id):
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
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    flash('Đã xóa tài khoản!', 'danger')
    return redirect(url_for('admin.user_list'))

@admin_bp.route('/recruiters')
@admin_required
def recruiter_list():
    recruiters = User.query.filter_by(role='recruiter').all()
    return render_template('admin/recruiters/index.html', recruiters=recruiters)

@admin_bp.route('/recruiters/create', methods=['GET', 'POST'])
@admin_required
def recruiter_add():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(email=email).first():
            flash('Email đã được đăng ký.', 'danger')
            return redirect(url_for('admin.recruiter_add'))

        hashed_pw = generate_password_hash(password)

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

@admin_bp.route('/recruiters/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
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
    recruiter = User.query.get_or_404(id)
    if recruiter.role != 'recruiter':
        flash('Không thể xem người không phải cộng tác viên.', 'warning')
        return redirect(url_for('admin.recruiter_list'))

    return render_template('admin/recruiters/view.html', recruiter=recruiter)



@admin_bp.route('/jobs')
@admin_required
def job_list():
    jobs = Job.query.all()
    return render_template('admin/jobs/index.html', jobs=jobs, today_date=date.today())


@admin_bp.route('/jobs/create', methods=['GET', 'POST'])
@admin_required
def job_add():
    users_list = User.query.filter(User.role.in_(['admin', 'recruiter'])).all()

    if request.method == 'POST':
        try:
            title = request.form['title']
            description = request.form['description']
            requirements = request.form.get('requirements', '')
            responsibilities = request.form.get('responsibilities', '')
            benefits = request.form.get('benefits', '')
            salary_range = request.form.get('salary_range', '')
            location = request.form.get('location', '')
            job_type = request.form.get('job_type', '')
            
            vacancy = int(request.form.get('vacancy') or 1)
            duration_days = int(request.form.get('duration_days') or 30)
            deadline_str = request.form.get('deadline')
            
            created_by = int(request.form.get('created_by')) 
            
            deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date() if deadline_str else None

            new_job = Job(
                title=title,
                description=description,
                requirements=requirements,
                responsibilities=responsibilities,
                benefits=benefits,
                salary_range=salary_range,
                location=location,
                job_type=job_type,
                vacancy=vacancy,
                deadline=deadline,
                created_by=created_by
            )

            db.session.add(new_job)
            db.session.flush() 

            expires_at = datetime.utcnow() + timedelta(days=duration_days) 
            
            job_details = JobPostDetails(
                job_id=new_job.id,
                approval_status='Pending', 
                approved_by=current_user.id,
                approved_at=datetime.utcnow(),
                duration_days=duration_days,
                expires_at=expires_at
            )
            db.session.add(job_details)
            db.session.commit()

            flash('Đăng tin tuyển dụng thành công và đã được phê duyệt!', 'success')
            return redirect(url_for('admin.job_list'))
            
        except ValueError:
            flash('Lỗi định dạng dữ liệu đầu vào. Vui lòng kiểm tra lại số lượng tuyển và thời hạn.', 'danger')
            db.session.rollback()
        except Exception as e:
            flash(f'Lỗi khi thêm tin tuyển dụng: {e}', 'danger')
            db.session.rollback()
            
    return render_template('admin/jobs/create.html', users=users_list)
@admin_bp.route('/jobs/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def job_edit(id):
    job = Job.query.get_or_404(id)
    if request.method == 'POST':
        try:
            job.title = request.form['title']
            job.description = request.form['description'] 
            job.responsibilities = request.form.get('responsibilities', '') 
            job.requirements = request.form.get('requirements', '') 
            job.benefits = request.form.get('benefits', '')
            
            job.salary_range = request.form.get('salary_range', '')
            job.location = request.form.get('location', '')
            job.job_type = request.form.get('job_type', '')
            job.vacancy = int(request.form.get('vacancy', 1))

            deadline_str = request.form.get('deadline')
            job.deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date() if deadline_str else None
            

            if job.details:
                new_duration = int(request.form.get('duration_days', job.details.duration_days))
                if new_duration != job.details.duration_days:
                    job.details.duration_days = new_duration
                    job.details.expires_at = datetime.utcnow() + timedelta(days=new_duration)

            db.session.commit()
            flash('Cập nhật tin tuyển dụng thành công!', 'success')
            return redirect(url_for('admin.job_list'))

        except ValueError:
             flash('Lỗi định dạng dữ liệu đầu vào. Vui lòng kiểm tra lại số lượng tuyển và thời hạn.', 'danger')
             db.session.rollback()
        except Exception as e:
             flash(f'Lỗi khi cập nhật tin tuyển dụng: {e}', 'danger')
             db.session.rollback()

    return render_template('admin/jobs/edit.html', job=job)

@admin_bp.route('/jobs/delete/<int:id>', methods=['POST'])
@admin_required
def job_delete(id):
    job = Job.query.get_or_404(id)
    db.session.delete(job)
    db.session.commit()
    flash('Đã xóa tin tuyển dụng!', 'danger')
    return redirect(url_for('admin.job_list'))


@admin_bp.route('/jobs/view/<int:id>')
@admin_required
def job_view(id):
    job = Job.query.get_or_404(id)
    return render_template('admin/jobs/view.html', job=job)


@admin_bp.route('/jobs/pending')
@admin_required
def job_pending_list():
    pending_jobs = db.session.query(Job) \
        .join(JobPostDetails) \
        .filter(JobPostDetails.approval_status == 'Pending') \
        .all()
        
    return render_template('admin/jobs_post/job_pending.html', 
                           jobs=pending_jobs,
                           today_date=date.today())
    
@admin_bp.route('/jobs/active') 
@admin_required
def job_active_list(): 
    active_jobs = db.session.query(Job) \
        .join(JobPostDetails) \
        .filter(JobPostDetails.approval_status == 'Approved') \
        .filter(JobPostDetails.expires_at > datetime.utcnow()) \
        .all() 
    
    return render_template('admin/jobs_post/job_active_list.html', 
                           jobs=active_jobs,
                           today_date=date.today())
    


@admin_bp.route('/jobs/approve/<int:id>', methods=['GET'])
@admin_required
def job_approve(id):
    job = Job.query.get_or_404(id)
    
    if not job.details:
        flash('Tin đăng này không có chi tiết phê duyệt.', 'danger')
        return redirect(url_for('admin.job_pending_list'))

    if job.details.approval_status != 'Pending':
        flash('Tin đăng này đã được xử lý.', 'warning')
        return redirect(url_for('admin.job_pending_list'))

    job.details.approval_status = 'Approved'
    job.details.approved_by = current_user.id
    job.details.approved_at = datetime.utcnow()
    
    duration = job.details.duration_days 
    job.details.expires_at = datetime.utcnow() + timedelta(days=duration)
    
    db.session.commit()
    flash(f'Tin tuyển dụng "{job.title}" đã được phê duyệt và đăng tải.', 'success')
    return redirect(url_for('admin.job_active_list'))

@admin_bp.route('/jobs/featured')
@admin_required
def job_featured_list():    
    featured_jobs = db.session.query(Job) \
        .join(JobPostDetails) \
        .filter(JobPostDetails.is_featured == True) \
        .filter(
            or_(
                JobPostDetails.approval_status == 'Approved',
                JobPostDetails.approval_status == 'Rejected'
            )
        ) \
        .filter(JobPostDetails.expires_at > datetime.utcnow()) \
        .all()
        
    return render_template('admin/jobs_post/job_featured_list.html', 
                           jobs=featured_jobs,
                           today_date=date.today())
    
@admin_bp.route('/jobs/select-feature')
@admin_required
def job_select_feature():
    jobs_to_feature = db.session.query(Job) \
        .join(JobPostDetails) \
        .filter(
            or_(
                JobPostDetails.approval_status == 'Approved',
                JobPostDetails.approval_status == 'Rejected'
            )
        ) \
        .filter(JobPostDetails.is_featured == False) \
        .filter(JobPostDetails.expires_at > datetime.utcnow()) \
        .all()
        
    return render_template('admin/jobs_post/job_select_feature.html', 
                           jobs=jobs_to_feature)
    
@admin_bp.route('/jobs/feature/<int:id>', methods=['GET'])
@admin_required
def job_feature(id):
    job = Job.query.get_or_404(id)
    
    if not job.details:
        flash('Lỗi: Tin tuyển dụng này không có chi tiết bài đăng.', 'danger')
        return redirect(url_for('admin.job_list'))

    is_currently_featured = job.details.is_featured
    job.details.is_featured = not is_currently_featured
    
    if job.details.is_featured:
        job.details.approval_status = 'Approved' 

    db.session.commit()

    if is_currently_featured:
        flash(f'Đã gỡ bỏ tin "{job.title}" khỏi danh sách nổi bật.', 'warning')
    else:
        flash(f'Đã ghim tin "{job.title}" vào danh sách nổi bật!', 'success')
    
    return redirect(url_for('admin.job_featured_list'))

@admin_bp.route('/jobs/soft-delete/<int:id>', methods=['POST'])
@admin_required
def job_soft_delete(id):
    job = Job.query.get_or_404(id)
    
    if job.details: 
        job.details.approval_status = 'Rejected' 
        
        job.details.is_featured = False 
    
    db.session.commit()
    
    flash(f'Tin tuyển dụng "{job.title}" đã được ẩn hoàn toàn khỏi hệ thống.', 'success')
    
    return redirect(url_for('admin.job_featured_list'))

@admin_bp.route('/jobs/active-delete/<int:id>', methods=['POST'])
@admin_required
def job_active_delete(id):
    job = Job.query.get_or_404(id)
    
    if job.details: 
        job.details.approval_status = 'Pending' 
        
        job.details.is_featured = False 
    
    db.session.commit()
    
    flash(f'Tin tuyển dụng "{job.title}" đã được ẩn hoàn toàn khỏi hệ thống.', 'success')
    
    return redirect(url_for('admin.job_active_list'))

@admin_bp.route('/jobs/reject/<int:id>', methods=['GET', 'POST'])
@admin_required
def job_reject(id):
    job = Job.query.get_or_404(id)
    
    if not job.details:
        flash('Tin đăng này không có chi tiết phê duyệt.', 'danger')
        return redirect(url_for('admin.job_pending_list'))

    if job.details.approval_status != 'Pending':
        flash('Tin đăng này đã được xử lý.', 'warning')
        return redirect(url_for('admin.job_pending_list'))
        
    if request.method == 'POST':
        rejection_reason = request.form.get('rejection_reason', 'Không đạt yêu cầu đăng tin.')
        
        job.details.approval_status = 'Rejected'
        job.details.approved_by = current_user.id
        job.details.rejection_reason = rejection_reason
        job.details.approved_at = datetime.utcnow() 
        
        db.session.commit()
        flash(f'Tin tuyển dụng "{job.title}" đã bị từ chối.', 'danger')
        return redirect(url_for('admin.job_pending_list'))

    return render_template('admin/jobs_post/job_reject.html', job=job)


@admin_bp.route('/jobs/analytics')
@admin_required
def job_analytics():

    today = date.today()
    last_7_days = [today - timedelta(days=i) for i in reversed(range(7))]

    total_jobs = Job.query.count()
    pending_count = db.session.query(JobPostDetails).filter_by(approval_status='Pending').count()
    active_count = db.session.query(JobPostDetails) \
        .filter(JobPostDetails.approval_status == 'Approved',
                JobPostDetails.expires_at > datetime.utcnow()).count()
    featured_count = db.session.query(JobPostDetails).filter_by(is_featured=True).count()

    labels = [d.strftime('%d-%m') for d in last_7_days]
    jobs_per_day = [Job.query.filter(func.date(Job.created_at) == d).count() for d in last_7_days]

    jobs_list = Job.query.order_by(Job.created_at.desc()).limit(10).all()

    analytics_data = {
        'total_jobs': total_jobs,
        'pending_count': pending_count,
        'active_count': active_count,
        'featured_count': featured_count,
        'chart_labels': labels,
        'chart_data': jobs_per_day,
        'jobs': jobs_list
    }

    return render_template('admin/jobs_post/job_analytics.html', data=analytics_data)

@admin_bp.route('/jobs/edit-approval/<int:id>', methods=['GET', 'POST'])
@admin_required
def job_edit_approval(id):
    job = Job.query.get_or_404(id)

    if not job.details:
        job.details = JobPostDetails(
            job_id=job.id,
            approval_status='Pending',
            approved_by=None,
            approved_at=None,
            is_featured=False,
            duration_days=30,
            expires_at=datetime.utcnow()  
        )
        db.session.add(job.details)
        db.session.commit()

    if request.method == 'POST':
        status = request.form.get('approval_status')
        reason = request.form.get('rejection_reason', '').strip()
        
        job.details.approval_status = status

        if status == 'Approved':
            job.details.approved_by = current_user.id
            job.details.approved_at = datetime.utcnow()
            job.details.rejection_reason = None  
        elif status == 'Rejected':
            job.details.approved_by = current_user.id
            job.details.approved_at = datetime.utcnow()
            job.details.rejection_reason = reason
        else:  
            job.details.approved_by = None
            job.details.approved_at = None
            job.details.rejection_reason = None

        db.session.commit()
        flash(f'Tin tuyển dụng "{job.title}" đã được cập nhật trạng thái phê duyệt.', 'success')
        return redirect(url_for('admin.job_active_list'))

    return render_template('admin/jobs_post/edit_pheduyet.html', job=job)

@admin_bp.route('/template-cv')
@admin_required
def template_cv_list():
    cv_templates = TemplateCV.query.order_by(TemplateCV.id.desc()).all()
    return render_template(
        'admin/template_cv/index.html',
        cv_templates=cv_templates
    )

@admin_bp.route('/template-cv/<int:id>/preview')
@admin_required
def preview_template_cv(id):
    cv = TemplateCV.query.get_or_404(id)
    return render_template('admin/template_cv/preview.html', cv=cv)

THUMBNAIL_FOLDER = 'static/uploads/avatar_cv'
CV_FILE_FOLDER = 'static/uploads/cv_file'
ALLOWED_THUMBNAILS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_CV_FILES = {'pdf', 'doc', 'docx'}

# Hàm kiểm tra file hợp lệ
def allowed_files(filename, allowed_exts):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_exts


@admin_bp.route('/template-cv/add', methods=['GET', 'POST'])
@admin_required
def add_template_cv():
    if request.method == 'POST':
        # Lấy dữ liệu từ form
        name_cv = request.form.get('name')
        description = request.form.get('description')
        category = request.form.get('category')
        is_active = 1 if request.form.get('is_active') == 'on' else 0

        # Xử lý thumbnail
        thumbnail_file = request.files.get('thumbnail')
        thumbnail_url = None
        if thumbnail_file and allowed_files(thumbnail_file.filename, ALLOWED_THUMBNAILS):
            filename = secure_filename(thumbnail_file.filename)
            save_path = os.path.join(current_app.root_path, THUMBNAIL_FOLDER, filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            thumbnail_file.save(save_path)
            # Lưu đường dẫn web vào DB
            thumbnail_url = f'/{THUMBNAIL_FOLDER}/{filename}'

        # Xử lý file CV
        cv_file = request.files.get('file_path')
        cv_url = None
        if cv_file and allowed_files(cv_file.filename, ALLOWED_CV_FILES):
            filename = secure_filename(cv_file.filename)
            save_path = os.path.join(current_app.root_path, CV_FILE_FOLDER, filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            cv_file.save(save_path)
            # Lưu đường dẫn web vào DB
            cv_url = f'/{CV_FILE_FOLDER}/{filename}'

        # Tạo object TemplateCV và lưu vào DB
        new_cv = TemplateCV(
            name_cv=name_cv,
            description=description,
            category=category,
            thumbnail=thumbnail_url,
            file_path=cv_url,
            is_active=is_active
        )
        db.session.add(new_cv)
        db.session.commit()
        flash('Thêm CV mẫu thành công!', 'success')
        return redirect(url_for('admin.template_cv_list'))

    return render_template('admin/template_cv/add.html')

@admin_bp.route('/template-cv/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_template_cv(id):
    cv = TemplateCV.query.get_or_404(id)

    if request.method == 'POST':
        old_name = cv.name_cv
        old_description = cv.description
        old_thumbnail = cv.thumbnail

        name_cv = request.form.get('name')
        description = request.form.get('description')
        file = request.files.get('thumbnail_file')

        if not name_cv or not description:
            flash("Tên và mô tả không được để trống!", "danger")
            return redirect(request.url)

        cv.name_cv = name_cv
        cv.description = description

        if file and file.filename:
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                save_path = os.path.join('static/uploads/avatar_cv', filename)

                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                file.save(save_path)
                cv.thumbnail = f"/static/uploads/avatar_cv/{filename}"
            else:
                flash("File không hợp lệ! Chỉ cho phép png, jpg, jpeg.", "danger")
                return redirect(request.url)

        if (
            cv.name_cv == old_name and
            cv.description == old_description and
            cv.thumbnail == old_thumbnail
        ):
            flash("Không có thay đổi nào được thực hiện!", "warning")
            return redirect(request.url)

        try:
            db.session.commit()
            flash("Cập nhật CV mẫu thành công!", "success")
        except Exception as e:
            db.session.rollback()
            flash("Lỗi! Không thể cập nhật dữ liệu.", "danger")
            print("Lỗi DB:", e)

        return redirect(url_for('admin.template_cv_list'))

    return render_template('admin/template_cv/edit.html', cv=cv)

@admin_bp.route('/template-cv/<int:id>/delete', methods=['POST'])
@admin_required
def delete_template_cv(id):
    cv = TemplateCV.query.get_or_404(id)
    db.session.delete(cv)
    db.session.commit()
    flash('Xoá CV mẫu thành công!', 'success')
    return redirect(url_for('admin.template_cv_list'))
