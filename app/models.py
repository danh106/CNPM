from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('admin', 'recruiter', 'applicant'), default='applicant')
    avatar_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Quan hệ
    activity_logs = db.relationship('ActivityLog', back_populates='user', cascade="all, delete-orphan")
    applicant = db.relationship('Applicant', back_populates='user', uselist=False, cascade="all, delete-orphan")
    images = db.relationship('UserImages', back_populates='user', cascade="all, delete-orphan")
    two_factor = db.relationship('TwoFactorAuth', back_populates='user', uselist=False, cascade="all, delete-orphan")

    # Người tạo job (recruiter)
    jobs_posted = db.relationship('Job', back_populates='created_by_user', cascade="all, delete-orphan")

    # Ứng viên nộp đơn (applicant)
    applications = db.relationship('Application', back_populates='user', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.full_name}>"


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='activity_logs')


class Applicant(db.Model):
    __tablename__ = "applicants"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    avatar_image_id = db.Column(db.Integer, db.ForeignKey('user_images.id', ondelete='SET NULL'))
    phone_number = db.Column(db.String(20))
    position_applied = db.Column(db.String(100))
    resume_url = db.Column(db.String(255))
    status = db.Column(db.Enum('Đang xử lý', 'Đã phỏng vấn', 'Đã nhận việc'), default='Đang xử lý')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', back_populates='applicant')
    avatar_image = db.relationship('UserImages', foreign_keys=[avatar_image_id], back_populates='applicant_avatar')


class Contact(db.Model):
    __tablename__ = "contacts"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    subject = db.Column(db.String(255))
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.Enum('new', 'read', 'replied'), default='new')


class Job(db.Model):
    __tablename__ = 'jobs'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)
    responsibilities = db.Column(db.Text)
    benefits = db.Column(db.Text)
    salary_range = db.Column(db.String(100))
    location = db.Column(db.String(150))
    job_type = db.Column(db.String(50))
    vacancy = db.Column(db.Integer, default=1)
    deadline = db.Column(db.Date)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    created_by_user = db.relationship('User', back_populates='jobs_posted')
    applications = db.relationship('Application', back_populates='job', cascade="all, delete-orphan")
    details = db.relationship('JobPostDetails', back_populates='job', uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Job {self.title}>"


class Application(db.Model):
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False)
    resume_url = db.Column(db.String(255))
    cover_letter = db.Column(db.Text)
    status = db.Column(db.Enum('pending', 'reviewed', 'accepted', 'rejected'), default='pending')
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)

    job = db.relationship('Job', back_populates='applications')
    user = db.relationship('User', back_populates='applications')

    def __repr__(self):
        return f"<Application user={self.user_id}, job={self.job_id}, status={self.status}>"


class TwoFactorAuth(db.Model):
    __tablename__ = "two_factor_auth"

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    secret_key = db.Column(db.String(255), nullable=False)

    user = db.relationship('User', back_populates='two_factor')


class UserImages(db.Model):
    __tablename__ = 'user_images'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='images')
    applicant_avatar = db.relationship('Applicant', back_populates='avatar_image', uselist=False)

class JobPostDetails(db.Model):
    __tablename__ = 'job_post_details'

    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, comment='Mã công việc')
    
    approval_status = db.Column(db.Enum('Draft', 'Pending', 'Approved', 'Rejected'), default='Draft', nullable=False, comment='Trạng thái phê duyệt')
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL', onupdate='CASCADE'), comment='ID người phê duyệt')
    approved_at = db.Column(db.DateTime, comment='Thời điểm phê duyệt')
    rejection_reason = db.Column(db.Text, comment='Lý do từ chối')
    duration_days = db.Column(db.Integer, default=30, nullable=False, comment='Số ngày tồn tại')
    expires_at = db.Column(db.DateTime, comment='Thời điểm hết hạn')
    is_featured = db.Column(db.Boolean, default=False, nullable=False, comment='Tin nổi bật')

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    job = db.relationship('Job', back_populates='details', uselist=False)
    approved_by_user = db.relationship('User', foreign_keys=[approved_by])

    def __repr__(self):
        return f"<JobDetails JobID={self.job_id}, Status={self.approval_status}>"