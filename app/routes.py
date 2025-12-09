from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt
from app.forms import RegistrationForm, LoginForm, LinkForm
from app.models import User, Link, Rating

main = Blueprint('main', __name__)

@main.route('/')
def home():
    sort = request.args.get('sort', 'newest')
    page = request.args.get('page', 1, type=int)

    query = Link.query
    if current_user.is_authenticated:
        query = query.filter(~Link.id.in_([l.id for l in current_user.hidden]))

    if sort == 'top':
        links = sorted(query.all(), key=lambda link: link.aggregate_rating(), reverse=True)
    else:
        links = query.order_by(Link.timestamp.desc()).all()

    per_page = 5
    total_pages = (len(links) + per_page - 1) // per_page
    paginated_links = links[(page-1)*per_page:page*per_page]

    return render_template('home.html', links=paginated_links, sort=sort, page=page, total_pages=total_pages)


@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)


@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('main.home'))
        flash('Login failed. Check username and password.', 'danger')
    return render_template('login.html', form=form)


@main.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.home'))


@main.route('/submit', methods=['GET', 'POST'])
@login_required
def submit():
    form = LinkForm()
    if form.validate_on_submit():
        link = Link(title=form.title.data, description=form.description.data, author=current_user)
        db.session.add(link)
        db.session.commit()
        flash('Link submitted!', 'success')
        return redirect(url_for('main.home'))
    return render_template('submit.html', form=form)





@main.route('/api/rate_link/<int:link_id>', methods=['POST'])
@login_required
def api_rate_link(link_id):
    data = request.get_json()
    value = data.get('value')

    if value not in [1, -1]:
        return jsonify({"error": "Invalid value"}), 400

    link = Link.query.get_or_404(link_id)

    if link.author == current_user:
        return jsonify({"error": "You cannot rate your own link."}), 403

    rating = Rating.query.filter_by(user_id=current_user.id, link_id=link.id).first()

    if rating:
        if rating.value != value:
            link.author.boardgame_points -= rating.value
            rating.value = value
            link.author.boardgame_points += value
    else:
        rating = Rating(user_id=current_user.id, link_id=link.id, value=value)
        db.session.add(rating)
        link.author.boardgame_points += value

    db.session.commit()

    return jsonify({
        "message": "Rating updated",
        "new_rating": link.aggregate_rating(),
        "new_points": link.author.boardgame_points
    }), 200


@main.route('/favorites')
@login_required
def favorites():
    fav_links = [r.link for r in current_user.ratings if r.value == 1 and r.link not in current_user.hidden]
    return render_template('favorites.html', links=fav_links)


@main.route('/profile/<username>')
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    user_links = Link.query.filter_by(user_id=user.id).all()
    return render_template('profile.html', user=user, links=user_links)


@main.route('/edit/<int:link_id>', methods=['GET', 'POST'])
@login_required
def edit_link(link_id):
    link = Link.query.get_or_404(link_id)
    if link.author != current_user:
        flash("Unauthorized!", "danger")
        return redirect(url_for('main.home'))

    form = LinkForm(obj=link)
    if form.validate_on_submit():
        link.title = form.title.data
        link.description = form.description.data
        db.session.commit()
        flash('Link updated!', 'success')
        return redirect(url_for('main.home'))
    return render_template('edit.html', form=form)


@main.route('/delete/<int:link_id>')
@login_required
def delete_link(link_id):
    link = Link.query.get_or_404(link_id)
    if link.author != current_user:
        flash("Unauthorized!", "danger")
        return redirect(url_for('main.home'))

    # 🚨 Delete ratings first to avoid IntegrityError
    Rating.query.filter_by(link_id=link.id).delete()

    db.session.delete(link)
    db.session.commit()
    flash('Link and its ratings deleted.', 'success')
    return redirect(url_for('main.home'))


@main.route('/api/hide_link/<int:link_id>', methods=['POST'])
@login_required
def hide_link(link_id):
    link = Link.query.get_or_404(link_id)
    if link not in current_user.hidden:
        current_user.hidden.append(link)
        db.session.commit()
    return jsonify({"message": "Link hidden"}), 200


@main.route('/leaderboard')
def leaderboard():
    users = User.query.order_by(User.boardgame_points.desc()).all()
    return render_template('leaderboard.html', users=users)
