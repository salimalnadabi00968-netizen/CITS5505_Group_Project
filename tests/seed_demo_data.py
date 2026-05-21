"""Reset the local database and seed realistic PerthPins demo data.

This script deletes all application data from the configured database, uploads
fresh demo images to the configured Cloudflare R2 bucket, and inserts users,
check-ins, photos, comments, and favourites.

Run from the project root:

    .venv/bin/python tests/seed_demo_data.py
"""

from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dataclasses import dataclass
from io import BytesIO
import random
import urllib.request

from sqlalchemy import text
from werkzeug.security import generate_password_hash

from backend.app import app
from backend.extensions import db
from backend.models import CheckIn, Comment, Favourite, Photo, User
from backend.routes import upload_image


DEMO_PASSWORD = "Password123!"
RANDOM_SEED = 5505


@dataclass(frozen=True)
class DemoUser:
    username: str
    email: str
    bio: str
    avatar_seed: str


@dataclass(frozen=True)
class DemoCheckIn:
    author: str
    place_name: str
    title: str
    description: str
    category: str
    rating: float
    lat: float
    lng: float
    image_seeds: tuple[str, str]


USERS = [
    DemoUser(
        "mia_wanderer",
        "mia.wanderer@example.com",
        "Weekend explorer chasing quiet parks, river views, and good coffee.",
        "portrait-city-woman",
    ),
    DemoUser(
        "uwa_studybites",
        "studybites@example.com",
        "Collecting study-friendly corners near UWA, preferably with snacks nearby.",
        "student-library",
    ),
    DemoUser(
        "riverlight",
        "riverlight@example.com",
        "Sunset walks, ferry rides, and anything along the Swan River.",
        "river-portrait",
    ),
    DemoUser(
        "coffee_cartographer",
        "coffee.cartographer@example.com",
        "Mapping Perth one flat white and pastry cabinet at a time.",
        "coffee-person",
    ),
    DemoUser(
        "nightowl_perth",
        "nightowl.perth@example.com",
        "Late dinners, live music, night markets, and city lights.",
        "night-city-person",
    ),
    DemoUser(
        "greenloop",
        "greenloop@example.com",
        "Nature trails, gardens, wetlands, and low-key picnic spots.",
        "green-outdoors",
    ),
    DemoUser(
        "market_maven",
        "market.maven@example.com",
        "Small shops, weekend markets, local makers, and gift-hunting routes.",
        "market-face",
    ),
    DemoUser(
        "perth_pins_admin",
        "admin@example.com",
        "Demo curator keeping the map lively for testing and presentations.",
        "admin-desk",
    ),
]


CHECKINS = [
    DemoCheckIn(
        "greenloop",
        "Kings Park and Botanic Garden",
        "Morning wildflower walk above the city",
        "A calm early walk with city views, shaded paths, and plenty of benches. Best before the tour buses arrive.",
        "nature",
        5.0,
        -31.9613,
        115.8324,
        ("kings-park-wildflowers", "kings-park-lookout"),
    ),
    DemoCheckIn(
        "riverlight",
        "Matilda Bay Reserve",
        "Picnic grass by the river",
        "Wide lawns, gentle river breeze, and a reliable sunset glow. Bring a blanket and watch the boats slide past.",
        "nature",
        4.7,
        -31.9813,
        115.8199,
        ("matilda-bay-grass", "matilda-bay-river"),
    ),
    DemoCheckIn(
        "greenloop",
        "Bold Park Zamia Trail",
        "Bush trail with ocean air",
        "A proper reset walk close to the city. Sandy sections, birdsong, and big glimpses toward the coast.",
        "nature",
        4.6,
        -31.9430,
        115.7793,
        ("bold-park-track", "bold-park-view"),
    ),
    DemoCheckIn(
        "mia_wanderer",
        "Lake Monger Reserve",
        "Easy loop for an afternoon walk",
        "Flat, open, and easy to do after class or work. Good for spotting black swans and clearing your head.",
        "nature",
        4.2,
        -31.9277,
        115.8216,
        ("lake-monger-path", "lake-monger-water"),
    ),
    DemoCheckIn(
        "coffee_cartographer",
        "Laika Coffee",
        "Bright brunch and serious coffee",
        "Busy but worth it. The filter coffee was clean and the brunch plates looked polished without feeling fussy.",
        "food",
        4.6,
        -31.9323,
        115.8599,
        ("laika-coffee-cup", "laika-brunch-table"),
    ),
    DemoCheckIn(
        "uwa_studybites",
        "Hackett Cafe",
        "Fast coffee between lectures",
        "Not the quietest spot, but the line moves quickly and it is perfectly placed for a caffeine rescue.",
        "food",
        4.0,
        -31.9787,
        115.8175,
        ("hackett-cafe-counter", "hackett-cafe-cup"),
    ),
    DemoCheckIn(
        "coffee_cartographer",
        "Mary Street Bakery Highgate",
        "Pastry cabinet worth crossing town for",
        "Excellent doughnuts, strong coffee, and a lively weekend crowd. Go early if you want the best pastry choice.",
        "food",
        4.5,
        -31.9395,
        115.8687,
        ("mary-street-pastry", "mary-street-coffee"),
    ),
    DemoCheckIn(
        "market_maven",
        "Fremantle Markets",
        "Snack trail through the old market hall",
        "A cheerful mix of fresh produce, quick bites, buskers, and souvenirs. Easy to lose an hour here.",
        "food",
        4.3,
        -32.0561,
        115.7485,
        ("fremantle-market-food", "fremantle-market-hall"),
    ),
    DemoCheckIn(
        "uwa_studybites",
        "Barry J Marshall Library",
        "Reliable silent study floor",
        "The upper levels are best for deep focus. Power points can disappear quickly during exam season.",
        "study",
        4.8,
        -31.9796,
        115.8183,
        ("barry-j-library-desks", "barry-j-library-shelves"),
    ),
    DemoCheckIn(
        "mia_wanderer",
        "State Library of Western Australia",
        "Big desks and city energy",
        "A dependable city study option with lots of space, natural light, and nearby food when motivation fades.",
        "study",
        4.4,
        -31.9494,
        115.8606,
        ("state-library-desk", "state-library-atrium"),
    ),
    DemoCheckIn(
        "uwa_studybites",
        "UWA Reid Library Courtyard",
        "Fresh air study break",
        "Good for reading between classes when the weather behaves. Close enough to duck back inside if it gets noisy.",
        "study",
        4.1,
        -31.9801,
        115.8176,
        ("reid-courtyard-table", "reid-courtyard-green"),
    ),
    DemoCheckIn(
        "perth_pins_admin",
        "Riverton Library",
        "Suburban study spot with calm lighting",
        "Quiet, practical, and less crowded than the city libraries. A strong option for longer weekend sessions.",
        "study",
        4.2,
        -32.0340,
        115.9040,
        ("riverton-library-table", "riverton-library-books"),
    ),
    DemoCheckIn(
        "nightowl_perth",
        "Elizabeth Quay",
        "Night lights along the water",
        "The city reflections are excellent after dark. Good first stop before dinner or a slow walk toward the foreshore.",
        "nightlife",
        4.4,
        -31.9587,
        115.8570,
        ("elizabeth-quay-night", "elizabeth-quay-bridge"),
    ),
    DemoCheckIn(
        "nightowl_perth",
        "Northbridge Piazza",
        "Easy meeting point before a night out",
        "Central, bright, and surrounded by food options. Best used as a starting point rather than the whole plan.",
        "nightlife",
        3.9,
        -31.9475,
        115.8589,
        ("northbridge-piazza", "northbridge-evening"),
    ),
    DemoCheckIn(
        "riverlight",
        "The Rechabite",
        "Rooftop drinks and live-show buzz",
        "A fun layered venue with a rooftop, theatre energy, and enough nearby options to make a full evening.",
        "nightlife",
        4.5,
        -31.9464,
        115.8613,
        ("rechabite-rooftop", "rechabite-night"),
    ),
    DemoCheckIn(
        "nightowl_perth",
        "Scarborough Beach Sunset Markets",
        "Food trucks with ocean sunset",
        "A very Perth evening: beach air, casual food, music, and a crowd that feels relaxed rather than rushed.",
        "nightlife",
        4.6,
        -31.8945,
        115.7572,
        ("scarborough-market-sunset", "scarborough-food-trucks"),
    ),
    DemoCheckIn(
        "market_maven",
        "Subiaco Farmers Market",
        "Saturday produce and breakfast stop",
        "Fresh fruit, flowers, baked goods, and coffee queues that move faster than expected. Bring a tote.",
        "shopping",
        4.4,
        -31.9488,
        115.8249,
        ("subiaco-market-stalls", "subiaco-market-flowers"),
    ),
    DemoCheckIn(
        "market_maven",
        "Claremont Quarter",
        "Polished shopping and lunch break",
        "Good for errands, gifts, and an easy lunch. More refined than chaotic, which is sometimes exactly right.",
        "shopping",
        4.1,
        -31.9817,
        115.7814,
        ("claremont-quarter-shop", "claremont-quarter-cafe"),
    ),
    DemoCheckIn(
        "mia_wanderer",
        "Oxford Street Leederville",
        "Window-shopping and small bites",
        "A lively strip for browsing, eating, and people-watching. Works well as a casual weekend wander.",
        "shopping",
        4.0,
        -31.9360,
        115.8418,
        ("leederville-street", "leederville-shops"),
    ),
    DemoCheckIn(
        "perth_pins_admin",
        "Watertown Brand Outlet Centre",
        "Practical outlet run near the city",
        "Not glamorous, but useful for discounted basics and last-minute wardrobe fixes before an event.",
        "shopping",
        3.7,
        -31.9468,
        115.8460,
        ("watertown-outlet", "watertown-walkway"),
    ),
    DemoCheckIn(
        "riverlight",
        "Cottesloe Beach",
        "Classic swim and fish-and-chips stop",
        "Clear water, big sky, and an easy evening plan. Wind can pick up quickly, so bring a layer.",
        "other",
        4.8,
        -31.9955,
        115.7520,
        ("cottesloe-beach-water", "cottesloe-beach-sunset"),
    ),
    DemoCheckIn(
        "mia_wanderer",
        "Heirisson Island",
        "Short nature detour from the city",
        "A compact walk with river views and a surprising sense of escape. Good when you only have half an hour.",
        "other",
        4.0,
        -31.9672,
        115.8777,
        ("heirisson-path", "heirisson-river"),
    ),
    DemoCheckIn(
        "greenloop",
        "Perth Cultural Centre",
        "Museum, galleries, and an easy courtyard pause",
        "Useful when the weather changes plans. You can drift between exhibitions, coffee, and open public space.",
        "other",
        4.3,
        -31.9490,
        115.8604,
        ("cultural-centre-courtyard", "cultural-centre-gallery"),
    ),
    DemoCheckIn(
        "coffee_cartographer",
        "South Perth Foreshore",
        "Skyline walk after dinner",
        "One of the easiest ways to make the city feel cinematic. The ferry option makes it feel like a tiny trip.",
        "other",
        4.6,
        -31.9737,
        115.8523,
        ("south-perth-skyline", "south-perth-foreshore"),
    ),
]


COMMENT_TEMPLATES = [
    "Adding this to my weekend list. The practical detail is genuinely helpful.",
    "Visited recently and agree with the rating. Timing makes a big difference here.",
    "Great spot. I would also recommend bringing water and going a little earlier.",
    "This is exactly the kind of place I forget exists until someone posts about it.",
    "Nice write-up. The location pin is accurate enough to find it quickly.",
    "I took a friend here last week and it worked really well.",
    "Good call on the best time to visit. It gets busy later.",
    "Saved this one. Looks like a strong option for a low-effort afternoon.",
]


def download_demo_image(seed: str, width: int = 1200, height: int = 800) -> BytesIO:
    """Download a deterministic real-photo placeholder and return file data."""
    url = f"https://picsum.photos/seed/perthpins-{seed}/{width}/{height}"
    request = urllib.request.Request(url, headers={"User-Agent": "PerthPins demo seeder"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = BytesIO(response.read())
    payload.content_type = "image/jpeg"
    payload.seek(0)
    return payload


def upload_demo_image(seed: str, folder: str) -> str:
    """Upload one downloaded demo image to R2 and return its public URL."""
    image = download_demo_image(seed)
    filename = f"demo-{folder}-{seed}.jpg"
    return upload_image(image, filename)


def reset_database():
    """Delete all app data while keeping the migration table intact."""
    for model in (Favourite, Comment, Photo, CheckIn, User):
        db.session.query(model).delete()

    sequence_table_exists = db.session.execute(text(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'"
    )).scalar()
    if sequence_table_exists:
        db.session.execute(text(
            "DELETE FROM sqlite_sequence "
            "WHERE name IN ('users', 'check_in', 'photos', 'comments')"
        ))
    db.session.commit()


def seed_users() -> dict[str, User]:
    users = {}
    for demo_user in USERS:
        user = User(
            username=demo_user.username,
            email=demo_user.email,
            password_hash=generate_password_hash(DEMO_PASSWORD),
            bio=demo_user.bio,
            avatar_url=upload_demo_image(demo_user.avatar_seed, "avatars"),
        )
        db.session.add(user)
        users[demo_user.username] = user
    db.session.commit()
    return users


def seed_checkins(users: dict[str, User]) -> list[CheckIn]:
    checkins = []
    for demo_checkin in CHECKINS:
        checkin = CheckIn(
            user_id=users[demo_checkin.author].id,
            place_name=demo_checkin.place_name,
            title=demo_checkin.title,
            description=demo_checkin.description,
            category=demo_checkin.category,
            rating=demo_checkin.rating,
            lat=demo_checkin.lat,
            lng=demo_checkin.lng,
        )
        db.session.add(checkin)
        db.session.flush()

        for display_order, seed in enumerate(demo_checkin.image_seeds):
            db.session.add(Photo(
                checkin_id=checkin.id,
                url=upload_demo_image(seed, "checkins"),
                display_order=display_order,
            ))
        checkins.append(checkin)
    db.session.commit()
    return checkins


def seed_comments_and_favourites(users: dict[str, User], checkins: list[CheckIn]):
    rng = random.Random(RANDOM_SEED)
    user_list = list(users.values())

    for checkin in checkins:
        possible_commenters = [user for user in user_list if user.id != checkin.user_id]
        for commenter in rng.sample(possible_commenters, 3):
            db.session.add(Comment(
                user_id=commenter.id,
                checkin_id=checkin.id,
                body=rng.choice(COMMENT_TEMPLATES),
            ))

        possible_savers = [user for user in user_list if user.id != checkin.user_id]
        for saver in rng.sample(possible_savers, 4):
            db.session.add(Favourite(
                user_id=saver.id,
                checkin_id=checkin.id,
            ))

    db.session.commit()


def print_summary():
    print("Seed complete")
    print(f"Users: {User.query.count()}")
    print(f"Check-ins: {CheckIn.query.count()}")
    print(f"Photos: {Photo.query.count()}")
    print(f"Comments: {Comment.query.count()}")
    print(f"Favourites: {Favourite.query.count()}")
    print(f"Demo password for all users: {DEMO_PASSWORD}")


def main():
    with app.app_context():
        reset_database()
        users = seed_users()
        checkins = seed_checkins(users)
        seed_comments_and_favourites(users, checkins)
        print_summary()


if __name__ == "__main__":
    main()
