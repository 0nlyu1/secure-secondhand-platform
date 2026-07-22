from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from models import Message, Product, Report, Transaction, User, db

app = Flask(__name__)

app.config["SECRET_KEY"] = "whs-secure-coding-development-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///market.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

@app.context_processor
def inject_logged_in_user():
    user = None

    if "user_id" in session:
        user = db.session.get(User, session["user_id"])

    return {"logged_in_user": user}


@app.route("/")
def index():
    current_user = None
    search_query = request.args.get("q", "").strip()

    if "user_id" in session:
        current_user = db.session.get(User, session["user_id"])

        if current_user is None:
            session.clear()

    products_query = Product.query.filter_by(is_blocked=False)

    if search_query:
        products_query = products_query.filter(
            Product.title.contains(search_query)
            | Product.description.contains(search_query)
        )

    products = products_query.order_by(Product.created_at.desc()).all()

    return render_template(
        "index.html",
        current_user=current_user,
        products=products,
        search_query=search_query,
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        flash("이미 로그인되어 있습니다.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        if not 4 <= len(username) <= 30:
            flash("아이디는 4자 이상 30자 이하로 입력해주세요.", "error")
            return render_template("register.html", username=username)

        if not username.isalnum():
            flash("아이디는 영문과 숫자만 사용할 수 있습니다.", "error")
            return render_template("register.html", username=username)

        if len(password) < 8:
            flash("비밀번호는 8자 이상이어야 합니다.", "error")
            return render_template("register.html", username=username)

        if password != password_confirm:
            flash("비밀번호 확인이 일치하지 않습니다.", "error")
            return render_template("register.html", username=username)

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash("이미 사용 중인 아이디입니다.", "error")
            return render_template("register.html", username=username)

        new_user = User(
            username=username,
            password=generate_password_hash(password),
        )

        db.session.add(new_user)
        db.session.commit()

        flash("회원가입이 완료되었습니다. 로그인해주세요.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        flash("이미 로그인되어 있습니다.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("아이디와 비밀번호를 모두 입력해주세요.", "error")
            return render_template("login.html", username=username)

        user = User.query.filter_by(username=username).first()

        if user is None or not check_password_hash(user.password, password):
            flash("아이디 또는 비밀번호가 올바르지 않습니다.", "error")
            return render_template("login.html", username=username)

        if user.is_suspended:
            flash("정지된 계정입니다. 관리자에게 문의해주세요.", "error")
            return render_template("login.html", username=username)

        session.clear()
        session["user_id"] = user.id

        flash(f"{user.username}님, 로그인되었습니다.", "success")
        return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("로그아웃되었습니다.", "success")
    return redirect(url_for("index"))

@app.route("/mypage", methods=["GET", "POST"])
def mypage():
    if "user_id" not in session:
        flash("로그인이 필요한 기능입니다.", "error")
        return redirect(url_for("login"))

    user = db.session.get(User, session["user_id"])

    if user is None:
        session.clear()
        flash("사용자 정보를 찾을 수 없습니다.", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        bio = request.form.get("bio", "").strip()

        if len(bio) > 300:
            flash("소개글은 300자 이하로 입력해주세요.", "error")
            return render_template("mypage.html", user=user)

        user.bio = bio
        db.session.commit()

        flash("소개글이 수정되었습니다.", "success")
        return redirect(url_for("mypage"))

    return render_template("mypage.html", user=user)

@app.route("/products/new", methods=["GET", "POST"])
def create_product():
    if "user_id" not in session:
        flash("로그인이 필요한 기능입니다.", "error")
        return redirect(url_for("login"))

    user = db.session.get(User, session["user_id"])

    if user is None:
        session.clear()
        flash("사용자 정보를 찾을 수 없습니다.", "error")
        return redirect(url_for("login"))

    if user.is_suspended:
        session.clear()
        flash("정지된 계정은 상품을 등록할 수 없습니다.", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        price_text = request.form.get("price", "").strip()

        if not 2 <= len(title) <= 100:
            flash("상품명은 2자 이상 100자 이하로 입력해주세요.", "error")
            return render_template(
                "product_form.html",
                title=title,
                description=description,
                price=price_text,
            )

        if not 1 <= len(description) <= 2000:
            flash("상품 설명은 1자 이상 2000자 이하로 입력해주세요.", "error")
            return render_template(
                "product_form.html",
                title=title,
                description=description,
                price=price_text,
            )

        try:
            price = int(price_text)
        except ValueError:
            flash("가격은 숫자로 입력해주세요.", "error")
            return render_template(
                "product_form.html",
                title=title,
                description=description,
                price=price_text,
            )

        if not 1 <= price <= 100_000_000:
            flash("가격은 1원 이상 1억 원 이하로 입력해주세요.", "error")
            return render_template(
                "product_form.html",
                title=title,
                description=description,
                price=price_text,
            )

        product = Product(
            title=title,
            description=description,
            price=price,
            seller_id=user.id,
        )

        db.session.add(product)
        db.session.commit()

        flash("상품이 등록되었습니다.", "success")
        return redirect(url_for("product_detail", product_id=product.id))

    return render_template("product_form.html")


@app.route("/products/<int:product_id>")
def product_detail(product_id):
    product = db.get_or_404(Product, product_id)

    if product.is_blocked:
        flash("차단된 상품입니다.", "error")
        return redirect(url_for("index"))

    seller = db.session.get(User, product.seller_id)

    return render_template(
        "product_detail.html",
        product=product,
        seller=seller,
    )

@app.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
def edit_product(product_id):
    if "user_id" not in session:
        flash("로그인이 필요한 기능입니다.", "error")
        return redirect(url_for("login"))

    user = db.session.get(User, session["user_id"])
    product = db.get_or_404(Product, product_id)

    if user is None:
        session.clear()
        flash("사용자 정보를 찾을 수 없습니다.", "error")
        return redirect(url_for("login"))

    if product.seller_id != user.id and not user.is_admin:
        flash("상품을 수정할 권한이 없습니다.", "error")
        return redirect(url_for("product_detail", product_id=product.id))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        price_text = request.form.get("price", "").strip()

        if not 2 <= len(title) <= 100:
            flash("상품명은 2자 이상 100자 이하로 입력해주세요.", "error")
            return render_template(
                "product_form.html",
                product=product,
                title=title,
                description=description,
                price=price_text,
                is_edit=True,
            )

        if not 1 <= len(description) <= 2000:
            flash("상품 설명은 1자 이상 2000자 이하로 입력해주세요.", "error")
            return render_template(
                "product_form.html",
                product=product,
                title=title,
                description=description,
                price=price_text,
                is_edit=True,
            )

        try:
            price = int(price_text)
        except ValueError:
            flash("가격은 숫자로 입력해주세요.", "error")
            return render_template(
                "product_form.html",
                product=product,
                title=title,
                description=description,
                price=price_text,
                is_edit=True,
            )

        if not 1 <= price <= 100_000_000:
            flash("가격은 1원 이상 1억 원 이하로 입력해주세요.", "error")
            return render_template(
                "product_form.html",
                product=product,
                title=title,
                description=description,
                price=price_text,
                is_edit=True,
            )

        product.title = title
        product.description = description
        product.price = price

        db.session.commit()

        flash("상품 정보가 수정되었습니다.", "success")
        return redirect(url_for("product_detail", product_id=product.id))

    return render_template(
        "product_form.html",
        product=product,
        title=product.title,
        description=product.description,
        price=product.price,
        is_edit=True,
    )


@app.route("/products/<int:product_id>/delete", methods=["POST"])
def delete_product(product_id):
    if "user_id" not in session:
        flash("로그인이 필요한 기능입니다.", "error")
        return redirect(url_for("login"))

    user = db.session.get(User, session["user_id"])
    product = db.get_or_404(Product, product_id)

    if user is None:
        session.clear()
        flash("사용자 정보를 찾을 수 없습니다.", "error")
        return redirect(url_for("login"))

    if product.seller_id != user.id and not user.is_admin:
        flash("상품을 삭제할 권한이 없습니다.", "error")
        return redirect(url_for("product_detail", product_id=product.id))

    db.session.delete(product)
    db.session.commit()

    flash("상품이 삭제되었습니다.", "success")
    return redirect(url_for("index"))

@app.route("/messages")
def messages():
    if "user_id" not in session:
        flash("로그인이 필요한 기능입니다.", "error")
        return redirect(url_for("login"))

    current_user = db.session.get(User, session["user_id"])

    if current_user is None:
        session.clear()
        flash("사용자 정보를 찾을 수 없습니다.", "error")
        return redirect(url_for("login"))

    users = (
        User.query
        .filter(User.id != current_user.id)
        .filter_by(is_suspended=False)
        .order_by(User.username.asc())
        .all()
    )

    return render_template(
        "messages.html",
        current_user=current_user,
        users=users,
        selected_user=None,
        conversation=[],
    )


@app.route("/messages/<int:user_id>", methods=["GET", "POST"])
def conversation(user_id):
    if "user_id" not in session:
        flash("로그인이 필요한 기능입니다.", "error")
        return redirect(url_for("login"))

    current_user = db.session.get(User, session["user_id"])
    selected_user = db.get_or_404(User, user_id)

    if current_user is None:
        session.clear()
        flash("사용자 정보를 찾을 수 없습니다.", "error")
        return redirect(url_for("login"))

    if current_user.id == selected_user.id:
        flash("자기 자신에게는 메시지를 보낼 수 없습니다.", "error")
        return redirect(url_for("messages"))

    if selected_user.is_suspended:
        flash("정지된 사용자와는 메시지를 주고받을 수 없습니다.", "error")
        return redirect(url_for("messages"))

    if request.method == "POST":
        content = request.form.get("content", "").strip()

        if not 1 <= len(content) <= 1000:
            flash("메시지는 1자 이상 1000자 이하로 입력해주세요.", "error")
            return redirect(url_for("conversation", user_id=selected_user.id))

        new_message = Message(
            sender_id=current_user.id,
            receiver_id=selected_user.id,
            content=content,
        )

        db.session.add(new_message)
        db.session.commit()

        flash("메시지를 전송했습니다.", "success")
        return redirect(url_for("conversation", user_id=selected_user.id))

    conversation_messages = (
        Message.query
        .filter(
            (
                (Message.sender_id == current_user.id)
                & (Message.receiver_id == selected_user.id)
            )
            |
            (
                (Message.sender_id == selected_user.id)
                & (Message.receiver_id == current_user.id)
            )
        )
        .order_by(Message.created_at.asc())
        .all()
    )

    return render_template(
        "messages.html",
        current_user=current_user,
        users=[],
        selected_user=selected_user,
        conversation=conversation_messages,
    )

@app.route("/report/user/<int:user_id>", methods=["GET", "POST"])
def report_user(user_id):
    if "user_id" not in session:
        flash("로그인이 필요한 기능입니다.", "error")
        return redirect(url_for("login"))

    current_user = db.session.get(User, session["user_id"])
    target_user = db.get_or_404(User, user_id)

    if current_user is None:
        session.clear()
        flash("사용자 정보를 찾을 수 없습니다.", "error")
        return redirect(url_for("login"))

    if current_user.id == target_user.id:
        flash("자기 자신은 신고할 수 없습니다.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        reason = request.form.get("reason", "").strip()

        if not 5 <= len(reason) <= 500:
            flash("신고 사유는 5자 이상 500자 이하로 입력해주세요.", "error")
            return render_template(
                "report.html",
                target_type="user",
                target=target_user,
                reason=reason,
            )

        existing_report = Report.query.filter_by(
            reporter_id=current_user.id,
            target_type="user",
            target_id=target_user.id,
        ).first()

        if existing_report:
            flash("이미 신고한 사용자입니다.", "error")
            return redirect(url_for("messages"))

        report = Report(
            reporter_id=current_user.id,
            target_type="user",
            target_id=target_user.id,
            reason=reason,
        )

        db.session.add(report)
        db.session.commit()

        flash("사용자 신고가 접수되었습니다.", "success")
        return redirect(url_for("messages"))

    return render_template(
        "report.html",
        target_type="user",
        target=target_user,
        reason="",
    )


@app.route("/report/product/<int:product_id>", methods=["GET", "POST"])
def report_product(product_id):
    if "user_id" not in session:
        flash("로그인이 필요한 기능입니다.", "error")
        return redirect(url_for("login"))

    current_user = db.session.get(User, session["user_id"])
    product = db.get_or_404(Product, product_id)

    if current_user is None:
        session.clear()
        flash("사용자 정보를 찾을 수 없습니다.", "error")
        return redirect(url_for("login"))

    if product.seller_id == current_user.id:
        flash("자신이 등록한 상품은 신고할 수 없습니다.", "error")
        return redirect(url_for("product_detail", product_id=product.id))

    if request.method == "POST":
        reason = request.form.get("reason", "").strip()

        if not 5 <= len(reason) <= 500:
            flash("신고 사유는 5자 이상 500자 이하로 입력해주세요.", "error")
            return render_template(
                "report.html",
                target_type="product",
                target=product,
                reason=reason,
            )

        existing_report = Report.query.filter_by(
            reporter_id=current_user.id,
            target_type="product",
            target_id=product.id,
        ).first()

        if existing_report:
            flash("이미 신고한 상품입니다.", "error")
            return redirect(url_for("product_detail", product_id=product.id))

        report = Report(
            reporter_id=current_user.id,
            target_type="product",
            target_id=product.id,
            reason=reason,
        )

        db.session.add(report)
        db.session.commit()

        flash("상품 신고가 접수되었습니다.", "success")
        return redirect(url_for("product_detail", product_id=product.id))

    return render_template(
        "report.html",
        target_type="product",
        target=product,
        reason="",
    )

def get_admin_user():
    if "user_id" not in session:
        return None

    user = db.session.get(User, session["user_id"])

    if user is None or not user.is_admin:
        return None

    return user


@app.route("/admin")
def admin_dashboard():
    admin = get_admin_user()

    if admin is None:
        flash("관리자만 접근할 수 있습니다.", "error")
        return redirect(url_for("index"))

    users = User.query.order_by(User.created_at.desc()).all()
    products = Product.query.order_by(Product.created_at.desc()).all()
    reports = Report.query.order_by(Report.created_at.desc()).all()

    report_rows = []

    for report in reports:
        if report.target_type == "user":
            target = db.session.get(User, report.target_id)
            target_name = target.username if target else "삭제된 사용자"
        else:
            target = db.session.get(Product, report.target_id)
            target_name = target.title if target else "삭제된 상품"

        reporter = db.session.get(User, report.reporter_id)

        report_rows.append(
            {
                "report": report,
                "reporter_name": reporter.username if reporter else "알 수 없음",
                "target_name": target_name,
            }
        )

    return render_template(
        "admin.html",
        users=users,
        products=products,
        report_rows=report_rows,
    )


@app.route("/admin/users/<int:user_id>/toggle-suspend", methods=["POST"])
def toggle_user_suspend(user_id):
    admin = get_admin_user()

    if admin is None:
        flash("관리자만 접근할 수 있습니다.", "error")
        return redirect(url_for("index"))

    target_user = db.get_or_404(User, user_id)

    if target_user.id == admin.id:
        flash("자신의 관리자 계정은 정지할 수 없습니다.", "error")
        return redirect(url_for("admin_dashboard"))

    if target_user.is_admin:
        flash("다른 관리자 계정은 정지할 수 없습니다.", "error")
        return redirect(url_for("admin_dashboard"))

    target_user.is_suspended = not target_user.is_suspended
    db.session.commit()

    if target_user.is_suspended:
        flash(f"{target_user.username} 계정을 정지했습니다.", "success")
    else:
        flash(f"{target_user.username} 계정 정지를 해제했습니다.", "success")

    return redirect(url_for("admin_dashboard"))


@app.route("/admin/products/<int:product_id>/toggle-block", methods=["POST"])
def toggle_product_block(product_id):
    admin = get_admin_user()

    if admin is None:
        flash("관리자만 접근할 수 있습니다.", "error")
        return redirect(url_for("index"))

    product = db.get_or_404(Product, product_id)

    product.is_blocked = not product.is_blocked
    db.session.commit()

    if product.is_blocked:
        flash(f"{product.title} 상품을 차단했습니다.", "success")
    else:
        flash(f"{product.title} 상품 차단을 해제했습니다.", "success")

    return redirect(url_for("admin_dashboard"))


@app.route("/admin/reports/<int:report_id>/resolve", methods=["POST"])
def resolve_report(report_id):
    admin = get_admin_user()

    if admin is None:
        flash("관리자만 접근할 수 있습니다.", "error")
        return redirect(url_for("index"))

    report = db.get_or_404(Report, report_id)

    report.status = "resolved"
    db.session.commit()

    flash("신고를 처리 완료 상태로 변경했습니다.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/transfer", methods=["GET", "POST"])
def transfer():
    if "user_id" not in session:
        flash("로그인이 필요한 기능입니다.", "error")
        return redirect(url_for("login"))

    current_user = db.session.get(User, session["user_id"])

    if current_user is None:
        session.clear()
        flash("사용자 정보를 찾을 수 없습니다.", "error")
        return redirect(url_for("login"))

    if current_user.is_suspended:
        session.clear()
        flash("정지된 계정은 송금할 수 없습니다.", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        receiver_username = request.form.get(
            "receiver_username",
            "",
        ).strip()

        amount_text = request.form.get("amount", "").strip()

        receiver = User.query.filter_by(
            username=receiver_username
        ).first()

        if receiver is None:
            flash("송금받을 사용자를 찾을 수 없습니다.", "error")
            return render_template(
                "transfer.html",
                current_user=current_user,
                receiver_username=receiver_username,
                amount=amount_text,
            )

        if receiver.id == current_user.id:
            flash("자기 자신에게는 송금할 수 없습니다.", "error")
            return render_template(
                "transfer.html",
                current_user=current_user,
                receiver_username=receiver_username,
                amount=amount_text,
            )

        if receiver.is_suspended:
            flash("정지된 사용자에게는 송금할 수 없습니다.", "error")
            return render_template(
                "transfer.html",
                current_user=current_user,
                receiver_username=receiver_username,
                amount=amount_text,
            )

        try:
            amount = int(amount_text)
        except ValueError:
            flash("송금액은 숫자로 입력해주세요.", "error")
            return render_template(
                "transfer.html",
                current_user=current_user,
                receiver_username=receiver_username,
                amount=amount_text,
            )

        if amount <= 0:
            flash("송금액은 1점 이상이어야 합니다.", "error")
            return render_template(
                "transfer.html",
                current_user=current_user,
                receiver_username=receiver_username,
                amount=amount_text,
            )

        if amount > current_user.points:
            flash("보유 포인트가 부족합니다.", "error")
            return render_template(
                "transfer.html",
                current_user=current_user,
                receiver_username=receiver_username,
                amount=amount_text,
            )

        try:
            current_user.points -= amount
            receiver.points += amount

            transaction = Transaction(
                sender_id=current_user.id,
                receiver_id=receiver.id,
                amount=amount,
            )

            db.session.add(transaction)
            db.session.commit()

        except Exception:
            db.session.rollback()
            flash("송금 처리 중 오류가 발생했습니다.", "error")
            return redirect(url_for("transfer"))

        flash(
            f"{receiver.username}님에게 {amount}점을 송금했습니다.",
            "success",
        )
        return redirect(url_for("transactions"))

    return render_template(
        "transfer.html",
        current_user=current_user,
        receiver_username="",
        amount="",
    )


@app.route("/transactions")
def transactions():
    if "user_id" not in session:
        flash("로그인이 필요한 기능입니다.", "error")
        return redirect(url_for("login"))

    current_user = db.session.get(User, session["user_id"])

    if current_user is None:
        session.clear()
        flash("사용자 정보를 찾을 수 없습니다.", "error")
        return redirect(url_for("login"))

    transaction_list = (
        Transaction.query
        .filter(
            (Transaction.sender_id == current_user.id)
            | (Transaction.receiver_id == current_user.id)
        )
        .order_by(Transaction.created_at.desc())
        .all()
    )

    transaction_rows = []

    for transaction in transaction_list:
        sender = db.session.get(User, transaction.sender_id)
        receiver = db.session.get(User, transaction.receiver_id)

        transaction_rows.append(
            {
                "transaction": transaction,
                "sender_name": (
                    sender.username if sender else "삭제된 사용자"
                ),
                "receiver_name": (
                    receiver.username if receiver else "삭제된 사용자"
                ),
            }
        )

    return render_template(
        "transactions.html",
        current_user=current_user,
        transaction_rows=transaction_rows,
    )

with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)