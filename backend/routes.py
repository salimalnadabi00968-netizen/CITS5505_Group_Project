"""Routes and request handlers"""

import os
import re
import uuid

import boto3
from dotenv import load_dotenv
from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from flask_wtf.csrf import CSRFError
from werkzeug.security import check_password_hash, generate_password_hash

from . import models
from .extensions import db, login_manager
from .models import CheckIn, Comment, Photo, User

load_dotenv()


EXPLORE_CATEGORIES = {
    "food": "Food & Drink",
    "study": "Study Spot",
    "nature": "Nature",
    "nightlife": "Nightlife",
    "shopping": "Shopping",
    "other": "Other",
}
EXPLORE_SORT_OPTIONS = {
    "newest": "Newest First",
    "rating": "Highest Rated",
}
CATETORIES = ["food", "study", "nature", "nightlife", "shopping", "other"]
R2_REQUIRED_ENV_VARS = (
    "CLOUDFLARE_ACCOUNT_ID",
    "CLOUDFLARE_ACCESS_KEY_ID",
    "CLOUDFLARE_SECRET_ACCESS_KEY",
    "CLOUDFLARE_BUCKET_NAME",
    "CLOUDFLARE_PUBLIC_URL",
)


def escape_like_search(value):
    """Escape SQL LIKE wildcard characters before building a search pattern."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def get_current_user_favourite_ids():
    """Return check-in IDs favourited by the logged-in user."""
    if not current_user.is_authenticated:
        return set()
    return {
        favourite.checkin_id
        for favourite in models.Favourite.query.filter_by(user_id=current_user.id).all()
    }


def get_safe_redirect_target(default_endpoint, **default_values):
    """Use a local POST return path when available, otherwise fall back safely."""
    target = request.form.get("next", "").strip()
    if target.startswith("/") and not target.startswith("//"):
        return target
    return url_for(default_endpoint, **default_values)


def get_r2_client():
    """Build the Cloudflare R2 client only when an upload/delete is requested."""
    missing = [name for name in R2_REQUIRED_ENV_VARS if not os.getenv(name)]
    if missing:
        raise RuntimeError(
            "Cloudflare R2 is not configured. Missing environment variables: "
            + ", ".join(missing)
        )
    return boto3.client(
        "s3",
        endpoint_url=f"https://{os.getenv('CLOUDFLARE_ACCOUNT_ID')}.r2.cloudflarestorage.com",
        aws_access_key_id=os.getenv("CLOUDFLARE_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("CLOUDFLARE_SECRET_ACCESS_KEY"),
        region_name="auto",
    )


def upload_image(file, filename):
    """Upload an image to R2 and return the public URL."""
    bucket = os.getenv("CLOUDFLARE_BUCKET_NAME")

    get_r2_client().upload_fileobj(
        file,
        bucket,
        filename,
        ExtraArgs={"ContentType": file.content_type},
    )

    public_url = os.getenv("CLOUDFLARE_PUBLIC_URL").rstrip("/")
    return f"{public_url}/{filename}"


def delete_image(image_url):
    """Delete an image from R2 using its public URL."""
    bucket = os.getenv("CLOUDFLARE_BUCKET_NAME")
    filename = image_url.split("/")[-1]

    get_r2_client().delete_object(
        Bucket=bucket,
        Key=filename,
    )


def register_routes(app):
    """Register Flask routes, error handlers, and login callbacks."""
    @login_manager.user_loader
    def load_user(user_id):
        """Load the current user for Flask-Login from the SQLAlchemy model."""
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None
    
    
    # this seems doesn't work
    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        """Show a friendly message when a submitted form is missing/has bad CSRF."""
        flash("Security check failed. Please refresh the page and try again.", "danger")
        return redirect(request.referrer or url_for("index"))
    
    
    @app.route("/")
    @app.route("/index.html")
    def index():
        check_ins = CheckIn.query.order_by(CheckIn.created_at.desc()).all()
        markers = [
            {
                "id": c.id,
                "lat": c.lat,
                "lng": c.lng,
                "title": c.title,
                "place_name": c.place_name,
                "category": c.category,
                "rating": c.rating,
            }
            for c in check_ins if c.lat is not None and c.lng is not None
        ]
        return render_template(
            "index.html",
            check_ins=check_ins,
            markers=markers,
            favourited_checkin_ids=get_current_user_favourite_ids(),
        )
    
    @app.route("/explore")    
    def explore_alias():
        return redirect(url_for("explore"))
    @app.route("/explore.html")
    def explore():
        """Render the explore page with database-backed filters and sorting."""
        selected_category = request.args.get("category", "").strip()
        selected_min_rating = request.args.get("min_rating", "").strip()
        selected_sort = request.args.get("sort", "newest").strip() or "newest"
    
        if selected_category not in EXPLORE_CATEGORIES:
            selected_category = ""
        if selected_sort not in EXPLORE_SORT_OPTIONS:
            selected_sort = "newest"
    
        min_rating_value = None
        if selected_min_rating:
            try:
                min_rating_value = float(selected_min_rating)
            except ValueError:
                selected_min_rating = ""
    
        query = CheckIn.query
        if selected_category:
            query = query.filter(CheckIn.category == selected_category)
        if min_rating_value is not None:
            query = query.filter(CheckIn.rating >= min_rating_value)
    
        if selected_sort == "rating":
            query = query.order_by(CheckIn.rating.desc(), CheckIn.created_at.desc())
        else:
            query = query.order_by(CheckIn.created_at.desc())
    
        check_ins = query.all()
        filters = {
            "category": selected_category,
            "min_rating": selected_min_rating,
            "sort": selected_sort,
        }
        return render_template(
            "explore.html",
            check_ins=check_ins,
            filters=filters,
            category_options=EXPLORE_CATEGORIES,
            sort_options=EXPLORE_SORT_OPTIONS,
            favourited_checkin_ids=get_current_user_favourite_ids(),
        )
    
    
    @app.route("/checkin-details")
    def checkin_details_alias():
        return redirect(url_for("checkin_details"))
    @app.route("/checkin_details.html")
    def checkin_details():
        """Redirect the old prototype URL to the latest available detail page."""
        check_in = CheckIn.query.order_by(CheckIn.created_at.desc()).first()
        if not check_in:
            return redirect(url_for("explore"))
        return redirect(url_for("checkin_detail", checkin_id=check_in.id))
    
    
    @app.route("/checkins/<int:checkin_id>")
    def checkin_detail(checkin_id):
        """Render one selected check-in from the database."""
        check_in = db.get_or_404(CheckIn, checkin_id)
        photos = check_in.photos.order_by(Photo.display_order.asc(), Photo.id.asc()).all()
        comments = check_in.comments.order_by(Comment.created_at.desc()).all()
        comments_count = len(comments)
        favourites_count = check_in.favourites.count()
        is_favourited = False
        if current_user.is_authenticated:
            is_favourited = models.Favourite.query.filter_by(
                user_id=current_user.id,
                checkin_id=check_in.id,
            ).first() is not None
        category = check_in.category if check_in.category in EXPLORE_CATEGORIES else "other"
        detail_map = {
            "lat": check_in.lat,
            "lng": check_in.lng,
            "title": check_in.title,
            "place_name": check_in.place_name,
            "category": EXPLORE_CATEGORIES.get(category, category.title()),
        }
        return render_template(
            "checkin_details.html",
            check_in=check_in,
            photos=photos,
            comments=comments,
            comments_count=comments_count,
            favourites_count=favourites_count,
            is_favourited=is_favourited,
            category_key=category,
            category_label=EXPLORE_CATEGORIES.get(category, category.title()),
            detail_map=detail_map,
        )
    
        
    @app.route("/checkins/<int:checkin_id>/comments", methods=["POST"])
    @login_required
    def add_comment(checkin_id):
        """Save a logged-in user's comment for one check-in."""
        check_in = db.get_or_404(CheckIn, checkin_id)
        body = request.form.get("body", "").strip()
        if not body:
            flash("Please write a comment before posting.", "danger")
            return redirect(url_for("checkin_detail", checkin_id=check_in.id))
        if len(body) > 1000:
            flash("Comments must be 1000 characters or fewer.", "danger")
            return redirect(url_for("checkin_detail", checkin_id=check_in.id))
        comment = Comment(
            user_id=current_user.id,
            checkin_id=check_in.id,
            body=body,
        )
        db.session.add(comment)
        db.session.commit()
        flash("Comment posted successfully.", "success")
        return redirect(url_for("checkin_detail", checkin_id=check_in.id))
    
    
    @app.route("/checkins/<int:checkin_id>/favourite", methods=["POST"])
    @login_required
    def toggle_favourite(checkin_id):
        """Toggle the current user's favourite on a check-in."""
        check_in = db.get_or_404(CheckIn, checkin_id)
        existing = models.Favourite.query.filter_by(
            user_id=current_user.id,
            checkin_id=checkin_id,
        ).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
            flash("Removed from favourites.", "info")
        else:
            db.session.add(models.Favourite(
                user_id=current_user.id,
                checkin_id=checkin_id,
            ))
            db.session.commit()
            flash("Added to favourites!", "success")
        return redirect(get_safe_redirect_target("checkin_detail", checkin_id=checkin_id))
    
    
    @app.route("/new-checkin")
    def new_checkin_alias():
        return redirect(url_for("new_checkin"))
    
    @app.route("/new-checkin.html", methods=["GET", "POST"])
    @login_required
    def new_checkin():
        if request.method == "POST":
            # get information from the front end by id
            place_name = request.form.get("place_name", "").strip()
            if not place_name:
                flash("Place name is required")
                print("Place name is required")
                return redirect(url_for('new_checkin'))

            title = request.form.get("title")
            if not title:
                flash("Title is required")
                print("Title is required")
                return redirect(url_for('new_checkin'))
            
            category = request.form.get("category")
            if category not in CATETORIES:
                flash("Category is wrong")
                print("Category is wrong")
                return redirect(url_for('new_checkin'))
    
            description = request.form.get("description")
            if not description:
                flash("Description is required")
                print("Description is required")
                return redirect(url_for('new_checkin'))
            
            try:
                rating = float(request.form.get("rating"))
                if rating < 1 or rating > 5:
                    raise Exception("Bad rating")
            except:
                flash("Invalid rating")
                print("Invalid rating")
                return redirect(url_for('new_checkin'))
            
            try:
                lat = float(request.form.get("lat"))
                lng = float(request.form.get("lng"))
            except:
                flash("Invalid location")
                print("Invalid location")
                return redirect(url_for('new_checkin'))
    
    
    
            # for all data into a dictionary
            form_data = {
                "user_id": current_user.id,
                "place_name": place_name,
                "title": title,
                "description": description,
                "category": category,
                "rating": rating,
                "lat": lat,
                "lng": lng
            }
    
            # get the user id who issue this post
            user = User.query.filter(
                (User.id == form_data["user_id"])
            ).first()
    
            check_in = CheckIn(
                user_id = user.id,
                place_name = form_data["place_name"],
                title = form_data["title"],
                description = form_data["description"],
                category = form_data["category"],
                rating = form_data["rating"],
                lat = form_data["lat"],
                lng = form_data["lng"]
            )
    
            db.session.add(check_in)
            # db.session.commit()
            db.session.flush()
    
            # image test
            images = request.files.getlist("input_image")
            try:
                for image in images:
                    if image and image.filename != '':
                        # generate unqiue filename to avoid conflicts
                        ext = image.filename.rsplit('.', 1)[1].lower()
                        filename = f"{uuid.uuid4()}.{ext}"
                        image_url = upload_image(image, filename)
    
                        new_photo = Photo(
                            checkin_id = check_in.id,
                            url = image_url
                        )
                        db.session.add(new_photo)
            except Exception as error:
                db.session.rollback()
                flash(f"Image upload failed: {error}", "danger")
                return redirect(url_for("new_checkin"))
            
            db.session.commit()
            return redirect(url_for("index"))
            
    
        """Render the new check-in page prototype"""
        return render_template("new-checkin.html")
    
    
    @app.route("/profile")
    @login_required
    def profile_alias():
        return redirect(url_for("profile"))
    @app.route("/profile.html")
    @login_required
    def profile():
        """Render the user profile page prototype"""
        user_id = current_user.id
        user = User.query.filter(User.id == user_id).first()
        
        if not user:
            flash("Please login first", "baduser")
            return render_template("profile.html")
        else:
            check_ins = CheckIn.query.filter(CheckIn.user_id == user.id).all()
            favourites = user.favourites.all()
            # find out the favourite checkins
            favourite_checkin_ids = [f.checkin_id for f in favourites]
            # following is the code to check which checkin ids are in the favourite_checkin_ids
            favourite_check_ins = CheckIn.query.filter(CheckIn.id.in_(favourite_checkin_ids)).all()
            sum_rating = 0
            avg_rating = 0
            if len(check_ins) != 0:
                for check_in in check_ins:
                    sum_rating += check_in.rating
                avg_rating = sum_rating / len(check_ins)
            return render_template(
                "profile.html",
                user = user,
                check_ins = check_ins,
                avg_rating = round(avg_rating, 1),
                favourite_check_ins = favourite_check_ins,
                is_profile = True,
                favourited_checkin_ids=set(favourite_checkin_ids))
    
    @app.route("/update_profile", methods = ["POST"])
    @login_required
    def update_profile():
        new_username = request.form.get("new_username", "").strip()
        new_bio = request.form.get("new_bio", "").strip()
        is_changed = request.form.get("is_changed")
        new_img_url = None
        
        user_id = current_user.id
        user = User.query.filter(User.id == user_id).first()
    
        if not user:
            flash("Please login first", "baduser")
            return render_template("profile.html")
        else:
            if not new_username:
                flash("Please type username")
                print("Please type username")
                return redirect(url_for("profile"))
            
            duplicated_user = User.query.filter_by(username = new_username).first()
            if duplicated_user and duplicated_user != current_user:
                flash("The username already exist")
                print("The username already exist")
                return redirect(url_for("profile"))
            
            if not new_bio:
                flash("Please type username")
                print("Please type username")
                return redirect(url_for("profile"))

            old_avatar_url = user.avatar_url
            if is_changed == "True":
                img = request.files.get("avatar_image")
                if not img or not img.filename:
                    flash("Please choose an image", "danger")
                    return redirect(url_for("profile"))
                if "." not in img.filename:
                    flash("Avatar image must have a file extension.", "danger")
                    return redirect(url_for("profile"))

                ext = img.filename.rsplit(".", 1)[1].lower()
                filename = f"{uuid.uuid4()}.{ext}"
                try:
                    new_img_url = upload_image(img, filename)
                except Exception as error:
                    current_app.logger.exception("Avatar upload failed")
                    flash(f"Avatar upload failed: {error}", "danger")
                    return redirect(url_for("profile"))
        
            user.username = new_username
            user.bio = new_bio
            if is_changed == "True":
                user.avatar_url = new_img_url
    
            db.session.commit()

            if is_changed == "True" and old_avatar_url:
                try:
                    delete_image(old_avatar_url)
                except Exception:
                    current_app.logger.warning(
                        "Old avatar cleanup failed for user %s", user.id, exc_info=True
                    )
                    flash("Profile updated, but the old avatar could not be removed from storage.", "warning")
    
        return redirect(url_for("profile"))
    
    @app.route("/delete_checkin/<int:checkin_id>", methods=["POST"])
    @login_required
    def delete_checkin(checkin_id):
        # checkin = CheckIn.query.filter(CheckIn.id == checkin_id).first()
        checkin = CheckIn.query.filter_by(
            id=checkin_id,
            user_id=current_user.id
        ).first_or_404()
    
        photos = checkin.photos.all()
        failed_deletes = 0
        for photo in photos:
            try:
                delete_image(photo.url)
            except Exception:
                failed_deletes += 1
                current_app.logger.warning(
                    "Check-in photo cleanup failed for photo %s", photo.id, exc_info=True
                )
    
        db.session.delete(checkin)
        db.session.commit()

        if failed_deletes:
            flash(
                f"Check-in deleted, but {failed_deletes} image file(s) could not be removed from storage.",
                "warning",
            )
        else:
            flash("Check-in deleted successfully.", "success")
    
        return redirect(url_for("profile"))
    
    
    # Original prototype-only login route:
    # @app.route("/login")
    # def login_alias():
    #     return redirect(url_for("login"))
    #
    # @app.route("/login.html")
    # def login():
    #     """Render the login page prototype"""
    #     return render_template("login.html")
    
    
    @app.route("/login")
    def login_alias():
        """Redirect to the login page"""
        return redirect(url_for("login"))
    
    
    @app.route("/login.html", methods=["GET", "POST"])
    def login():
        """Log in an existing user and store their identity in the session."""
        if current_user.is_authenticated:
            return redirect(url_for("index"))
    
        if request.method == "POST":
            identifier = request.form.get("identifier", "").strip()
            password = request.form.get("password", "")
            form_data = {"identifier": identifier}
    
            if not identifier or not password:
                flash("Please enter your username/email and password.", "danger")
                return render_template("login.html", form_data=form_data)
    
            user = User.query.filter(
                (User.username == identifier) | (User.email == identifier.lower())
            ).first()
    
            if not user or not check_password_hash(user.password_hash, password):
                flash("Invalid username/email or password.", "danger")
                return render_template("login.html", form_data=form_data)
    
            login_user(user)
    
            flash("Logged in successfully.", "success")
            return redirect(url_for("index"))
    
        return render_template("login.html", form_data={})
    
    
    @app.route("/logout", methods=["POST"])
    @login_required
    def logout():
        """Log out the current user with Flask-Login."""
        logout_user()
        flash("You have been logged out.", "success")
        return redirect(url_for("index"))

    @app.route("/register")
    def register_alias():
        """Redirect to the registration page"""
        return redirect(url_for("register"))
    @app.route("/register.html", methods=["GET", "POST"])
    def register():
        """Create a new user account from the registration form."""
        if current_user.is_authenticated:
            return redirect(url_for("index"))
    
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")
    
            form_data = {"username": username, "email": email}
    
            if not username or not email or not password or not confirm_password:
                flash("Please complete all required fields.", "danger")
                return render_template("register.html", form_data=form_data)
    
            if password != confirm_password:
                flash("Passwords do not match!", "danger")
                return render_template("register.html", form_data=form_data)

            if len(password) < 8:
                flash("Password must be at least 8 characters.", "danger")
                return render_template("register.html", form_data=form_data)
            if not re.search(r"[A-Z]", password):
                flash("Password must contain at least one uppercase letter.", "danger")
                return render_template("register.html", form_data=form_data)
            if not re.search(r"[0-9]", password):
                flash("Password must contain at least one number.", "danger")
                return render_template("register.html", form_data=form_data)

            existing_user = User.query.filter(
                (User.username == username) | (User.email == email)
            ).first()
    
            if existing_user:
                flash("Username or email is already registered.", "danger")
                return render_template("register.html", form_data=form_data)
    
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
            )
            db.session.add(user) # Add the new user to the session
            db.session.commit() # Commit the session to save the user to the database
    
            flash("Account created successfully. Please log in.", "success")
            return redirect(url_for("login"))
    
        return render_template("register.html", form_data={})
    @app.route("/search")
    def search():
        query = request.args.get("q", "").strip()
        if not query:
            return redirect(url_for("explore"))
    
        search_pattern = f"%{escape_like_search(query)}%"
        check_ins = CheckIn.query.filter(
            (CheckIn.title.ilike(search_pattern, escape="\\")) |
            (CheckIn.description.ilike(search_pattern, escape="\\")) |
            (CheckIn.place_name.ilike(search_pattern, escape="\\"))
        ).order_by(CheckIn.created_at.desc()).all()
        return render_template(
            "explore.html",
            check_ins=check_ins,
            search_query=query,
            filters={"category": "", "min_rating": "", "sort": "newest"},
            category_options=EXPLORE_CATEGORIES,
            sort_options=EXPLORE_SORT_OPTIONS,
            favourited_checkin_ids=get_current_user_favourite_ids(),
        )
    @app.route("/navbar.html")
    def navbar():
        """Render the navigation bar prototype"""
        return render_template("navbar.html")
    
    
    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html"), 404
    
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("500.html"), 500
