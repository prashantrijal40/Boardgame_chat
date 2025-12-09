import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import db, bcrypt, create_app
from app.models import User, Link, Rating
from datetime import datetime

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    # Create 3 users
    u1 = User(username='alice', password=bcrypt.generate_password_hash('pass').decode('utf-8'))
    u2 = User(username='bob', password=bcrypt.generate_password_hash('pass').decode('utf-8'))
    u3 = User(username='carol', password=bcrypt.generate_password_hash('pass').decode('utf-8'))
    db.session.add_all([u1, u2, u3])
    db.session.commit()

    # Create 5 links
    l1 = Link(title="Boardgame 1", description="Awesome game!", author=u1)
    l2 = Link(title="Boardgame 2", description="Great strategy!", author=u2)
    l3 = Link(title="Boardgame 3", description="Party favorite", author=u2)
    l4 = Link(title="Boardgame 4", description="Relaxing play", author=u3)
    l5 = Link(title="Boardgame 5", description="Underrated gem", author=u1)  # No ratings
    db.session.add_all([l1, l2, l3, l4, l5])
    db.session.commit()

    # Create 10 ratings
    ratings = [
        Rating(user_id=u1.id, link_id=l2.id, value=1),
        Rating(user_id=u1.id, link_id=l3.id, value=-1),
        Rating(user_id=u1.id, link_id=l4.id, value=1),

        Rating(user_id=u2.id, link_id=l1.id, value=1),
        Rating(user_id=u2.id, link_id=l3.id, value=1),
        Rating(user_id=u2.id, link_id=l4.id, value=-1),

        Rating(user_id=u3.id, link_id=l1.id, value=-1),
        Rating(user_id=u3.id, link_id=l2.id, value=1),
        Rating(user_id=u3.id, link_id=l3.id, value=1),
        Rating(user_id=u3.id, link_id=l4.id, value=1),
    ]
    db.session.add_all(ratings)

    # Update boardgame points
    l1.author.boardgame_points += 0  # Net 0 (1 from bob, -1 from carol)
    l2.author.boardgame_points += 2  # (1 from alice, 1 from carol)
    l3.author.boardgame_points += 1  # (-1 from alice, +1 from bob, +1 from carol)
    l4.author.boardgame_points += 1  # (+1 from alice, -1 from bob, +1 from carol)
    db.session.commit()

    print("✅ Demo data seeded.")
