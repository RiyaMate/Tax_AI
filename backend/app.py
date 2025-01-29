from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional, List
import bcrypt

# FastAPI app initialization
app = FastAPI()

# OAuth2 Configuration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# In-memory Databases
item_db = []
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "",
        "hashed_password": bcrypt.hashpw("password".encode(), bcrypt.gensalt()).decode(),
        "disabled": False,
    }
}

# Models
class User(BaseModel):
    username: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    disabled: Optional[bool] = None

class InDBUser(User):
    hashed_password: str

class Item(BaseModel):
    id: int
    name: str
    price: float
    description: Optional[str] = None

# Utility Functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def get_user(db, username: str) -> Optional[InDBUser]:
    if username in db:
        user_dict = db[username]
        return InDBUser(**user_dict)
    return None

def fake_decode_token(token: str) -> User:
    user = get_user(fake_users_db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user

def current_user(token: str = Depends(oauth2_scheme)) -> User:
    user = fake_decode_token(token)
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive User"
        )
    return user

# Routes
@app.get("/")
async def root():
    return {"message": "Welcome to the Basic FASTAPI App example!"}

@app.post("/greet/")
async def greet_user(user: User):
    if 0 < user.age < 18:
        return {"message": f"Sorry {user.name}, you are too young to use this app."}
    elif user.age >= 18:
        return {"message": f"Welcome {user.name} to the app!"}
    return {"message": "Invalid age."}

@app.get("/square/{number}")
async def square_number(number: int):
    return {"number": number, "square": number ** 2}

# CRUD for Items
@app.get("/items/", response_model=List[Item])
async def read_items():
    return item_db

@app.post("/items/", response_model=Item)
async def create_item(item: Item):
    item_db.append(item)
    return item

@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item: Item):
    for i, db_item in enumerate(item_db):
        if db_item.id == item_id:
            item_db[i] = item
            return item
    raise HTTPException(status_code=404, detail="Item not found")

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    for i, db_item in enumerate(item_db):
        if db_item.id == item_id:
            del item_db[i]
            return {"message": "Item deleted"}
    raise HTTPException(status_code=404, detail="Item not found")
