from datetime import datetime
from app import db # Giả sử 'app' và 'db' đã được định nghĩa
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
    activity_logs = db.relationship('ActivityLog', backref='user', lazy=True, cascade="all, delete")
    applicants = db.relationship('Applicant', backref='user', uselist=False, cascade="all, delete")
    applications = db.relationship('Application', backref='user', lazy=True, cascade="all, delete")
    jobs_created = db.relationship('Job', backref='creator', lazy=True, cascade="all, delete")
    images = db.relationship('UserImage', backref='user', lazy=True, cascade="all, delete")
    two_factor = db.relationship('TwoFactorAuth', backref='user', uselist=False, cascade="all, delete")

class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Applicant(db.Model):
    __tablename__ = "applicants"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    avatar_image_id = db.Column(db.Integer, db.ForeignKey('user_images.id', ondelete='SET NULL'))
    phone_number = db.Column(db.String(20))
    position_applied = db.Column(db.String(100))
    resume_url = db.Column(db.String(255))
    status = db.Column(db.Enum('Đang xử lý','Đã phỏng vấn','Đã nhận việc'), default='Đang xử lý')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    avatar_image = db.relationship('UserImage', foreign_keys=[avatar_image_id], backref='applicant_avatar')


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False)
    resume_url = db.Column(db.String(255))
    cover_letter = db.Column(db.Text)
    status = db.Column(db.Enum('pending','reviewed','accepted','rejected'), default='pending')
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)

    job = db.relationship('Job', backref='applications')


class Contact(db.Model):
    __tablename__ = "contacts"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    subject = db.Column(db.String(255))
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.Enum('new','read','replied'), default='new')

class Job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)  # Yêu cầu/Trình độ
    responsibilities = db.Column(db.Text)  # Trách nhiệm công việc
    benefits = db.Column(db.Text)  # Quyền lợi
    salary_range = db.Column(db.String(100))
    location = db.Column(db.String(150))
    job_type = db.Column(db.String(50))  # Loại công việc (Toàn thời gian, Bán thời gian...)
    vacancy = db.Column(db.Integer, default=1)  # Số lượng tuyển
    deadline = db.Column(db.Date)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    created_by_user = db.relationship('User', backref='jobs_posted', lazy=True)

class TwoFactorAuth(db.Model):
    __tablename__ = "two_factor_auth"

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    secret_key = db.Column(db.String(255), nullable=False)


class UserImage(db.Model):
    __tablename__ = "user_images"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)