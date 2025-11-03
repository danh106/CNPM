
from datetime import datetime
from app import db
from flask_login import UserMixin # <== THÊM IMPORT NÀY

# Thường thì cần thêm cả thư viện để kiểm tra mật khẩu
from werkzeug.security import generate_password_hash, check_password_hash

# Kế thừa từ db.Model VÀ UserMixin
class User(db.Model, UserMixin): # <== THÊM UserMixin VÀO ĐÂY
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    # Lưu ý: role phải có giá trị 'admin' để decorator @admin_required hoạt động
    role = db.Column(db.Enum('admin', 'recruiter', 'applicant'), default='applicant') 
    avatar_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    
    # --- CÁC PHƯƠNG THỨC HỖ TRỢ FLASK-LOGIN & BẢO MẬT ---
    
    # Phương thức này CẦN THIẾT để Flask-Login biết cách quản lý mật khẩu
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # Phương thức hỗ trợ kiểm tra quyền Admin
    @property
    def is_admin(self):
        """Trả về True nếu vai trò là 'admin'."""
        return self.role == 'admin'

    def __repr__(self):
        return f"<User {self.id}: {self.full_name}, Role: {self.role}>"
    


class CongTacVien(db.Model):
    __tablename__ = 'cong_tac_vien'

    id = db.Column(db.Integer, primary_key=True)
    ten = db.Column(db.String(100))
    email = db.Column(db.String(100))
    sdt = db.Column(db.String(20))
    dia_chi = db.Column(db.String(255))
    avatar = db.Column(db.String(255))  # ✅ Đường dẫn ảnh
    
class Job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)
    salary_range = db.Column(db.String(100))
    location = db.Column(db.String(150))
    deadline = db.Column(db.Date)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

