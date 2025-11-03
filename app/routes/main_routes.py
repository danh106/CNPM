from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required
from app.models import User
from werkzeug.security import check_password_hash, generate_password_hash
from app import db
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature


serializer = URLSafeTimedSerializer('super-secret-key')


# Blueprint chính
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Đăng nhập thành công!', 'success')

            # Chuyển hướng tùy vai trò
            if user.role == 'admin':
                return redirect(url_for('admin.admin_dashboard'))
            else:
                return redirect(url_for('main.index'))
        else:
            flash('Email hoặc mật khẩu không đúng!', 'danger')
    return render_template('login.html')

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']
        role = 'applicant'  # mặc định là ứng viên

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email này đã được đăng ký!', 'danger')
            return redirect(url_for('main.register'))

        hashed_pw = generate_password_hash(password)
        new_user = User(full_name=full_name, email=email, password_hash=hashed_pw, role=role)
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

@main_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()

        if not user:
            flash('Email không tồn tại trong hệ thống.', 'danger')
            return redirect(url_for('main.forgot_password'))

        # Tạo token
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        token = s.dumps(email, salt='reset-password')

        # Giả lập gửi liên kết
        reset_link = url_for('main.reset_password', token=token, _external=True)
        flash(f'Liên kết đặt lại mật khẩu của bạn (demo): {reset_link}', 'info')
        return redirect(url_for('main.login'))

    return render_template('forgot_password.html')


@main_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # tạo serializer với SECRET_KEY của app
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='reset-password', max_age=1800)  # 30 phút
    except SignatureExpired:
        flash('Liên kết đã hết hạn. Vui lòng thử lại.', 'danger')
        return redirect(url_for('main.forgot_password'))
    except BadSignature:
        flash('Liên kết không hợp lệ.', 'danger')
        return redirect(url_for('main.forgot_password'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Người dùng không tồn tại.', 'danger')
        return redirect(url_for('main.forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('password', '').strip()
        if not new_password:
            flash('Vui lòng nhập mật khẩu mới.', 'warning')
            return render_template('reset_password.html', token=token)

        # ✅ Hash mật khẩu trước khi lưu
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()

        flash('Đã đặt lại mật khẩu. Vui lòng đăng nhập bằng mật khẩu mới.', 'success')
        return redirect(url_for('main.login'))

    return render_template('reset_password.html', token=token)
