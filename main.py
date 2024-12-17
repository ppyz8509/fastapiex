from sqlalchemy import Column, Integer, String, Text, ForeignKey, DECIMAL ,Boolean
from sqlalchemy.orm import relationship 
from datetime import datetime,timedelta
from fastapi import FastAPI, HTTPException,Depends;
from pydantic import BaseModel;
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm;
from jose import JWTError, jwt;
from fastapi.responses import RedirectResponse;
import mysql.connector;
import os;
from dotenv import load_dotenv

load_dotenv()

#jwt seting
SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def get_db_connection():
   cnx = mysql.connector.connect(
       host=os.getenv("MSQL_HOST"),
       user=os.getenv("MYSQL_USER"),
       database=os.getenv("MYSQL_DATABASE"),
   )
   return cnx

class Attraction(BaseModel):
    name: str
    detail: str
    coverimage: str
    latitude: float
    longitude: float

class User(BaseModel):
    username: str
    password: str
    name: str
    email: str


class Token(BaseModel):
    access_token: str
    token_type: str

class Category(BaseModel):
    Category_name: str
    Category_at: str

# กำหนดโมเดลสำหรับ Product
class Product(BaseModel):
    id: int
    Product_name: str
    Price: float
    Stock_quantity: int
    Freesubject: bool
    Shop_name: str
    Category_name: str
    Created_at: str

class Shop(BaseModel):
    Shop_name: str
    Shop_address: str
    Shop_phone: str
    Created_at: datetime


app = FastAPI()

ouath2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.astimezone() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    

# Login
@app.post("/login", tags=["Authentication"])
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    username = form_data.username
    password = form_data.password
    cnx = get_db_connection()
    cursor = cnx.cursor(dictionary=True)
    query = "SELECT id, username, password FROM users WHERE username = %s AND password = %s"
    cursor.execute(query, (username, password))
    user = cursor.fetchone()
    cursor.close()
    cnx.close()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Create access token
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}
 
#tags=["attractions"]
@app.post("/attractions",tags=["Attractions"])
def create_attraction(attraction: Attraction):
    cnx = get_db_connection()
    cursor = cnx.cursor()
    query = '''INSERT INTO attractions (name, detail, coverimage, latitude, longitude) VALUES (%s, %s, %s, %s, %s)'''
    values = (attraction.name, attraction.detail, attraction.coverimage, attraction.latitude, attraction.longitude)
    cursor.execute(query, (attraction.name, attraction.detail, attraction.coverimage, attraction.latitude, attraction.longitude))
    cnx.commit()
    attraction_id = cursor.lastrowid
    cursor.close()
    cnx.close()
    return {"message": "Attraction created successfully", "id": attraction_id ,"data": attraction}

@app.delete("/attractions/{id}",tags=["Attractions"])
def delete_attraction(id: int):
    cnx = get_db_connection()
    cursor = cnx.cursor()
    query = "DELETE FROM attractions WHERE id = %s"
    cursor.execute(query, (id,))
    cnx.commit()
    cursor.close()
    cnx.close()
    if cursor.rowcount == 0:
        return {"message": "Attraction not found", "id": id,}  
    return {"message": "Attraction deleted successfully", "id": id,} 

@app.get("/attractions",tags=["Attractions"])  
def get_attraction():
     cnx = get_db_connection()
     cursor = cnx.cursor()
     query = "SELECT * FROM attractions"
     cursor.execute(query)
     rows = cursor.fetchall()
     cursor.close()
     cnx.close() 

     attractions = [] 
     for row in rows:
         attractions.append({
             "id": row[0],
             "name" : row[1],
             "detail" : row[2],
             "coverimage" : row[3],
             "latitude" : row[4],
             "longitude" : row[5]
         })

     return attractions

@app.get("/attractions/{id}", tags=["Attractions"])
def get_attraction(id: int):
    cnx = get_db_connection()
    cursor = cnx.cursor()
    query = "SELECT * FROM attractions WHERE id = %s"
    cursor.execute(query, (id,))
    row = cursor.fetchone()
    cursor.close()
    cnx.close()
    if row is None:
        return {"message": "Attraction not found", "id": id,}
    return {"id": row[0], "name": row[1], "detail": row[2], "coverimage": row[3], "latitude": row[4], "longitude": row[5]}

@app.put("/attractions/{id}", tags=["Attractions"])
def update_attraction(id: int, attraction: Attraction):
    cnx = get_db_connection()
    cursor = cnx.cursor()
    query = '''UPDATE attractions SET name = %s, detail = %s, coverimage = %s, latitude = %s, longitude = %s WHERE id = %s'''
    values = (attraction.name, attraction.detail, attraction.coverimage, attraction.latitude, attraction.longitude, id)
    cursor.execute(query, values)
    cnx.commit()
    cursor.close()
    cnx.close()
    return {"message": "Attraction updated ", "id": id, "data": attraction}

#user crud
@app.get("/users", tags=["Users"])
def get_users():
    cnx = get_db_connection()
    cursor = cnx.cursor()
    query = "SELECT * FROM users"
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    cnx.close()
    users = []
    for row in rows:
        users.append({
            "id": row[0],
            "username": row[1],
            "password": row[2],
            "name": row[3],
            "email": row[4]
        })
    return users

@app.get("/users/{id}", tags=["Users"])
def get_user(id: int):
    cnx = get_db_connection()
    cursor = cnx.cursor()
    query = "SELECT * FROM users WHERE id = %s"
    cursor.execute(query, (id,))
    row = cursor.fetchone()
    cursor.close()
    cnx.close()
    if row is None:
        return {"message": "User not found", "id": id,}
    return {"id": row[0], "username": row[1], "password": row[2], "name": row[3], "email": row[4]}

@app.post("/users", tags=["Users"])
def create_user(user: User):
    cnx = get_db_connection()
    cursor = cnx.cursor()
    # ตรวจสอบว่า username หรือ email ซ้ำหรือไม่
    check_query = '''SELECT 1 FROM users WHERE username = %s OR email = %s LIMIT 1'''
    cursor.execute(check_query, (user.username, user.email))
    existing_user = cursor.fetchone()
    
    if existing_user:
        cursor.close()
        cnx.close()
        return {"message": "Username or email already exists."}
    
    query = '''INSERT INTO users (username, password, name, email) VALUES (%s, %s, %s, %s)'''
    values = (user.username, user.password, user.name, user.email)
    cursor.execute(query, (user.username, user.password, user.name, user.email))
    cnx.commit()
    user_id = cursor.lastrowid
    cursor.close()
    cnx.close()
    return {"message": "User created successfully", "id": user_id, "data": user}

@app.put("/users/{id}", tags=["Users"])
def update_user(id: int, user: User):
    cnx = get_db_connection()
    cursor = cnx.cursor()
    query = '''UPDATE users SET username = %s, password = %s, name = %s, email = %s WHERE id = %s'''
    values = (user.username, user.password, user.name, user.email, id)
    cursor.execute(query, values)
    cnx.commit()
    cursor.close()
    cnx.close()
    return {"message": "User updated successfully", "id": id, "data": user}

@app.delete("/users/{id}", tags=["Users"])
def delete_user(id: int):
    cnx = get_db_connection()
    cursor = cnx.cursor()
    query = "DELETE FROM users WHERE id = %s"
    cursor.execute(query, (id, ))
    cnx.commit()
    cursor.close()
    cnx.close()
    return {"message": "User deleted successfully", "id": id,}

#test code 
@app.get("/", tags=["Test path"])
def read_root():
    return RedirectResponse(url="/docs")


@app.get("/phpmyadmin",tags=["Test path"])
def read_hello():
    return RedirectResponse(url="http://localhost/phpmyadmin/index.php?route=/sql&pos=0&db=mydb&table=users")

@app.get("/test",tags=["Test path"])
def read_hello():
    return RedirectResponse(url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")

@app.get("/items/{id}",tags=["Test"])
def read_item(id: int):
    return {"items": id}

@app.post("/items/",tags=["Test"])
def create_item(item: dict):
    return {"item": item}

@app.delete("/items/{id}",tags=["Test"])
def read_item(id: int):
    return {"item": id, "message": "Item deleted successfully"}

@app.put("/items/{id}", tags=["Test"])
def update_item(id: int, item: dict):
    return {"item": id, "item": item, "message": "Item updated successfully"}



## Supermarket
@app.get("/shops", tags=["Shops"])
def get_shops():
    cnx = get_db_connection()
    cursor = cnx.cursor()
    query = "SELECT * FROM shop"
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    cnx.close()
    shops = []
    for row in rows:
        shops.append({
            "id": row[0],
            "Shop_name": row[1],
            "Shop_address": row[2],
            "Shop_phone": row[3],
            "Created_at": row[4]
        })
    return shops

@app.get("/shops/{id}", tags=["Shops"])
def get_shop(id: int):
    cnx = get_db_connection()
    cursor = cnx.cursor()
    query = "SELECT * FROM shop WHERE Shop_id = %s;"
    cursor.execute(query, (id, ))
    row = cursor.fetchone()
    cursor.close()
    cnx.close()
    if row is None:
        return {"message": "Shop not found", "id": id,}
    return {"id": row[0], "Shop_name": row[1], "Shop_address": row[2], "Shop_phone": row[3], "Created_at": row[4]}

@app.post("/shops", tags=["Shops"])
def create_shop(shop: Shop):
    cnx = get_db_connection()
    cursor = cnx.cursor()
    query = '''INSERT INTO shop (Shop_name, Shop_address, Shop_phone, Created_at) VALUES (%s, %s, %s, %s)'''
    values = (shop.Shop_name, shop.Shop_address, shop.Shop_phone, shop.Created_at)
    cursor.execute(query, values)
    cnx.commit()
    shop_id = cursor.lastrowid
    cursor.close()
    cnx.close()
    return {"message": "Shop created successfully", "id": shop_id, "data": shop}

@app.put("/shops/{id}", tags=["Shops"])
def update_shop(id: int, shop: Shop):
    cnx = get_db_connection()
    cursor = cnx.cursor()
    query = '''UPDATE shop SET Shop_name = %s, Shop_address = %s, Shop_phone = %s, Created_at = %s WHERE Shop_id = %s'''
    values = (shop.Shop_name, shop.Shop_address, shop.Shop_phone, shop.Created_at, id)
    cursor.execute(query, values)
    cnx.commit()
    cursor.close()
    cnx.close()
    return {"message": "Shop updated successfully", "id": id,"data": shop}

@app.delete("/shops/{id}", tags=["Shops"])
def delete_shop(id: int):
    cnx = get_db_connection()
    cursor = cnx.cursor()
    query = "DELETE FROM shop WHERE Shop_id = %s"
    cursor.execute(query, (id, ))
    cnx.commit()
    cursor.close()
    cnx.close()
    return {"message": "Shop deleted successfully", "id": id,}




#category
@app.get("/categories", tags=["Categories"])
def get_categories():
    cnx = get_db_connection()
    cursor = cnx.cursor()
   
    query = """
    SELECT category.Category_id, category.Category_name, category.Created_at, 
           product.Product_id, product.Product_name, product.Price, product.Stock_quantity
    FROM category
    LEFT JOIN product ON category.Category_id = product.Category_id
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    cnx.close()
    
    categories = []
    for row in rows:
        # สร้างข้อมูลหมวดหมู่ที่มีสินค้าที่เกี่ยวข้อง
        category = {
            "id": row[0],
            "Category_name": row[1],
            "Created_at": row[2],
            "products": []  # เริ่มต้นสินค้าเป็นรายการว่าง
        }
        

        if row[3]: 
            category["products"].append({
                "Product_id": row[3],
                "Product_name": row[4],
                "Price": row[5],
                "Stock_quantity": row[6]
            })
        
        categories.append(category)

    return categories

@app.get("/category/{category_id}", tags=["Categories"])
def get_category_by_id(category_id: int):
    cnx = get_db_connection()
    cursor = cnx.cursor()
    
    #ดึงข้อมูลหมวดหมู่และสินค้าตาม category_id ที่กำหนด
    query = """
    SELECT category.Category_id, category.Category_name, category.Created_at, 
           product.Product_id, product.Product_name, product.Price, product.Stock_quantity
    FROM category
    LEFT JOIN product ON category.Category_id = product.Category_id
    WHERE category.Category_id = %s
    """

    cursor.execute(query, (category_id,))
    rows = cursor.fetchall()
    cursor.close()
    cnx.close()
    
    if not rows:
        return {"message": "Category not found"}
    
    category = {
        "id": rows[0][0],
        "Category_name": rows[0][1],
        "Created_at": rows[0][2],
        "products": [] 
    }
    
    for row in rows:
        if row[3]:  
            category["products"].append({
                "Product_id": row[3],
                "Product_name": row[4],
                "Price": row[5],
                "Stock_quantity": row[6]
            })
    
    return category

@app.post("/categories", tags=["Categories"])
def create_category(category: Category):
    cnx = get_db_connection()
    cursor = cnx.cursor()
    qurey = '''INSERT INTO category (Category_name, Created_at) VALUES (%s, %s)'''
    values = (category.Category_name, category.Created_at)

#product
@app.get("/products", tags=["Products"])
def get_products():
    cnx = get_db_connection()
    cursor = cnx.cursor()
    query = '''
        SELECT 
            p.Product_id, 
            p.Product_name, 
            p.Price, 
            p.Stock_quantity, 
            p.Freesubject, 
            s.Shop_name, 
            c.Category_name, 
            p.Created_at
        FROM product p
        LEFT JOIN shop s ON p.Shop_id = s.Shop_id
        LEFT JOIN category c ON p.Category_id = c.Category_id;
    '''

    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    cnx.close()

    products = []
    for row in rows:
        products.append({
            "id": row[0],
            "Product_name": row[1],
            "Price": row[2],
            "Stock_quantity": row[3],
            "Freesubject": row[4],
            "Shop_name": row[5],
            "Category_name": row[6],
            "Created_at": row[7]
        })

    return products

@app.get("/products/{id}", tags=["Products"])
def get_product(id: int):
    cnx = get_db_connection()
    cursor = cnx.cursor()
    query = '''
        SELECT 
            p.Product_id, 
            p.Product_name, 
            p.Price, 
            p.Stock_quantity, 
            p.Freesubject, 
            s.Shop_name, 
            c.Category_name, 
            p.Created_at
        FROM product p
        LEFT JOIN shop s ON p.Shop_id = s.Shop_id
        LEFT JOIN category c ON p.Category_id = c.Category_id
        WHERE p.Product_id = %s;
    '''

    cursor.execute(query, (id,))
    row = cursor.fetchone()
    cursor.close()
    cnx.close()

    if row is None:
        return {"message": "Product not found", "id": id}

    return {
        "id": row[0],
        "Product_name": row[1],
        "Price": row[2],
        "Stock_quantity": row[3],
        "Freesubject": row[4],
        "Shop_name": row[5],
        "Category_name": row[6],
        "Created_at": row[7]
    }

@app.post("/products", tags=["Products"])
def create_product(product: Product):
    cnx = get_db_connection()
    cursor = cnx.cursor()
    query = '''INSERT INTO product (Product_name, Price, Stock_quantity, Freesubject, Shop_id, Category_id, Created_at) VALUES (%s, %s, %s, %s, %s, %s, %s)'''
    values = (product.Product_name, product.Price, product.Stock_quantity, product.Freesubject, product.Shop_id, product.Category_id, product.Created_at)
    cursor.execute(query, values)
    cnx.commit()
    product_id = cursor.lastrowid
    cursor.close()
    cnx.close()
    return {"message": "Product created successfully", "id": product_id,"data": product}