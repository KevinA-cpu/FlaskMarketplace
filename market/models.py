from market import db, argon2, login_manager
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(length=30), nullable=False, unique=True)
    email_address = db.Column(db.String(length=50), nullable=False, unique=True)
    password_hash = db.Column(db.String(length=60), nullable=False)
    budget = db.Column(db.Integer(), nullable=False, default=1000)
    refresh_token = db.Column(db.String(length=50), nullable=False, default="")
    items = db.relationship("Item", backref="owned_user", lazy=True)

    def __repr__(self) -> str:
        return f"User {self.username}"
    
    @property
    def password(self):
        return self.password
    
    @property
    def prettier_budget(self):
        budget_str = str(self.budget)
        if len(budget_str) < 4:
            return f"${budget_str}$"
        else:
            parts = []
            while budget_str:
                parts.append(budget_str[-3:])
                budget_str = budget_str[:-3]
            return f"${','.join(reversed(parts))}$"

    
    @password.setter
    def password(self, plain_text_password):
        self.password_hash = argon2.generate_password_hash(plain_text_password)

    def check_password_correction(self, attempted_password):
        return argon2.check_password_hash(self.password_hash, attempted_password)
    
    def can_purchase(self, item_obj):
        return self.budget >= item_obj.price
    
    def can_sell(self, item_obj):
        return item_obj in self.items

class Item(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(length=30), nullable=False, unique=True)
    price = db.Column(db.Integer(), nullable=False)
    barcode = db.Column(db.String(length=12), nullable=False, unique=True)
    description = db.Column(db.String(length=1024), nullable=False, unique=True)
    owner = db.Column(db.Integer(), db.ForeignKey("user.id"))

    def __repr__(self) -> str:
        return f"Item {self.name}"
    
    def buy(self, user):
        self.owner = user.id
        user.budget -= self.price
        db.session.commit()
    
    def sell(self, user):
        self.owner = None
        user.budget += self.price
        db.session.commit()