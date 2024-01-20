import datetime
import re
from itertools import count
from turtle import title
import cursor as cursor
from bson import ObjectId
from flask import Flask, request, render_template, redirect, session
import pymongo
import boto3 as boto3
import os

app = Flask(__name__)
app.secret_key = "grocery"
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
APP_ROOT = APP_ROOT + "/static/"
my_conn = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = my_conn["grocery_management"]
admin_col = mydb["admin"]
customer_col = mydb["customer"]
category_col = mydb["category"]
items_col = mydb["items"]
customer_order_col = mydb["customer_order"]
customer_order_item_col = mydb["customer_order_item"]

grocery_region = 'us-east-1'
grocery_bucket = "grocery-s3-bucket"
grocery_email = 'vinay.kumar.cvk2999@gmail.com@gmail.com'
grocery_s3 = boto3.client('s3', aws_access_key_id="AKIAQXDJYK6PIVFEKVY3", aws_secret_access_key="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")
grocery_ses = boto3.client('ses', aws_access_key_id="AKIAQXDJYK6PIVFEKVY3", aws_secret_access_key="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", region_name=grocery_region)

if admin_col.count_documents({}) == 0:
    admin_col.insert_one({"username": "admin", "password": "admin"})


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/admin_login")
def admin_login():
    return render_template("admin_login.html")


@app.route("/admin_login1", methods=["post"])
def admin_login1():
    username = request.form.get("username")
    password = request.form.get("password")
    print(username, password)
    query = {"username": username, "password": password}
    count = admin_col.count_documents(query)
    if count > 0:
        admin = admin_col.find_one(query)
        session["admin_id"] = str(admin["_id"])
        session["role"] = 'admin'
        return redirect("/admin_home")
    else:
        return render_template("Mmsg.html", message="Invalid Login Details")


@app.route("/admin_home")
def admin_home():
    admin_id = session["admin_id"]
    query = {"_id": ObjectId(admin_id)}
    admin = admin_col.find_one(query)
    return render_template("admin_home.html", admin=admin)


@app.route("/logout")
def logout():
    session.clear()
    return render_template("home.html")


@app.route("/customer_register")
def customer_register():
    return render_template("customer_register.html")


@app.route("/customer_register1", methods=["post"])
def customer_register1():
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    age = request.form.get("age")
    password = request.form.get("password")
    gender = request.form.get("gender")
    query = {"$or": [{"email": email}, {"phone": phone}]}
    count = customer_col.count_documents(query)
    if count == 0:
        grocery_ses.verify_email_address(
            EmailAddress=email
        )
        query = {"name": name, "email": email, "phone": phone, "age": age, "password": password, "gender": gender}
        customer_col.insert_one(query)
        return render_template("Mmsg.html", message="Customer Verify Your Email before Login. Please Check Your Mail Box")
    else:
        return render_template("Mmsg.html", message="Duplicate Entry")


@app.route("/customer_login")
def customer_login():
    return render_template("customer_login.html")


@app.route("/customer_login1", methods=['post'])
def customer_login1():
    email = request.form.get("email")
    password = request.form.get("password")
    query = {"email": email, "password": password}
    count = customer_col.count_documents(query)
    if count > 0:
        customer = customer_col.find_one(query)

        grocery_customer_emails = grocery_ses.list_identities(
            IdentityType='EmailAddress'
        )
        if email in grocery_customer_emails['Identities']:
            grocery_customer_email_add_info = 'You' + '' + ' Have Sucessfully Logged In to Grocery Management System Website'
            grocery_ses.send_email(Source=grocery_email, Destination={'ToAddresses': [email]},
                                            Message={'Subject': {'Data': grocery_customer_email_add_info, 'Charset': 'utf-8'},
                                                     'Body': {'Html': {'Data': grocery_customer_email_add_info, 'Charset': 'utf-8'}}})

            session["customer_id"] = str(customer["_id"])
            session["role"] = 'customer'
            return redirect("/customer_home")
        else:
            return render_template("Mmsg.html", message="Customer Not Verified. Please verify Your EMAIL and Login")
    else:
        return render_template("Mmsg.html", message="Invalid Login Details")



@app.route("/view_customers")
def view_customer():
    customer = customer_col.find()
    customers = list(customer)
    if len(customers) == 0:
        return render_template("Amsg.html", message="No Details Found")
    return render_template("view_customers.html", customers=customers)


@app.route("/customer_profile")
def customer_profile():
    customer = customer_col.find()
    customers = list(customer)
    if len(customers) == 0:
        return render_template("Cmsg.html", message="No Details Found")
    return render_template("customer_profile.html", customers=customers)


@app.route("/Update")
def Update():
    customer_id = request.args.get("customer_id")
    query = {'_id': ObjectId(customer_id)}
    customer = customer_col.find_one(query)
    print(customer)
    return render_template("Update.html", customer=customer)



@app.route("/Update1" ,methods=['post'])
def Update1():
    customer_id = request.form.get("customer_id")
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    password = request.form.get("password")
    age = request.form.get("age")
    gender = request.form.get("gender")
    query = {"_id": ObjectId(customer_id)}
    query1 = {"$set": {"name": name, email: "email" , phone : "phone" , age: "age" , password : "password", gender : "gender"}}
    customer_col.update_one(query,query1)
    return render_template("Cmsg.html", message="Updated Successfully")




@app.route("/customer_home")
def customer_home():
    customer_id = session["customer_id"]
    query = {"_id": ObjectId(customer_id)}
    customer = customer_col.find_one(query)
    return render_template("customer_home.html", customer=customer)

@app.route("/add_categories")
def add_categories():
    categories = category_col.find()
    return render_template("add_categories.html",categories=categories)


@app.route("/add_categories1", methods=['post'])
def add_categories1():
    category_name = request.form.get("category_name")
    category_image = request.files.get("category_image")
    path = APP_ROOT + "/categories/" + category_image.filename
    category_image.save(path)
    grocery_s3.upload_file(path, grocery_bucket, category_image.filename)
    category_image_file_name = category_image.filename
    category_image_s3_url = f'https://{grocery_bucket}.s3.amazonaws.com/{category_image_file_name}'
    try:
        query = {"category_name": category_name, "category_image": category_image_s3_url}
        category_col.insert_one(query)
        return render_template("Amsg.html", message='category added successfully', color='text-success')
    except Exception as e:
        print(e)
        return render_template("Amsg.html", message='something went wrong', color='text-danger')


@app.route("/view_categories")
def view_categories():
    categories = category_col.find()
    categories = list(categories)
    print(categories)
    if len(categories) == 0:
        return render_template("Amsg.html", message="no details are found")
    else:
        return render_template("view_categories.html", categories=categories)


@app.route("/add_items")
def add_items():
    # items = items_col
    categories = category_col.find({})
    categories=list(categories)
    print(categories)
    return render_template("add_items.html", categories=categories)


@app.route("/add_items1", methods=["post"])
def add_items1():
    item_name = request.form.get("item_name")
    item_image = request.files.get("item_image")
    item_price = request.form.get("item_price")
    item_quantity = request.form.get("item_quantity")
    item_description = request.form.get("item_description")
    category_id = request.form.get("category_id")
    path = APP_ROOT + "/items/" + item_image.filename
    item_image.save(path)
    grocery_s3.upload_file(path, grocery_bucket, item_image.filename)
    item_image_s3_file_name = item_image.filename
    item_image_url = f'https://{grocery_bucket}.s3.amazonaws.com/{item_image_s3_file_name}'
    try:
        query = {"item_name": item_name, "item_image": item_image_url, "item_price": item_price,
                 "item_quantity": item_quantity,"item_description": item_description,
                 "category_id": ObjectId(category_id)}
        items_col.insert_one(query)
        return render_template("Amsg.html", message='Item Added Successfully', color='text-primary')
    except Exception as e:
        return render_template("Amsg.html", message='Something Went Wrong', color='text-danger')


@app.route("/view_items")
def view_items():
    item = items_col.find()
    items = list(item)
    if len(items) == 0:
        return render_template("Amsg.html", message="no details are found")
    else:
        return render_template("view_items.html", items=items)


@app.route("/view_items_customer")
def view_items_customer():
    categories = category_col.find()
    categories = list(categories)
    return render_template("view_items_customer.html",categories=categories)


@app.route("/get_items")
def get_items():
    category_id = request.args.get("category_id")
    keyword = request.args.get("keyword")
    if category_id == None:
        category_id = ""
    query = {}
    if category_id == "" and keyword == "" :
        query = {}
    elif category_id == "" and keyword != "":
        keyword = re.compile(".*" + keyword + ".*", re.IGNORECASE)
        query = {"item_name": keyword}
    elif category_id != "" and keyword == "":
        query = {"category_id": ObjectId(category_id)}
    elif category_id != "" and keyword != "":
        keyword = re.compile(".*" + keyword + ".*", re.IGNORECASE)
        query = {"category_id":ObjectId(category_id),"item_name":keyword}

    items = items_col.find(query)
    items = list(items)
    categories = category_col.find()
    return render_template("get_items.html", items=items,categories=categories, get_category_name=get_category_name)#get_category_by_category_id=get_category_by_category_id

def get_category_name(category_id):
    query = {"_id": ObjectId(category_id)}
    category = category_col.find_one(query)
    return category

@app.route("/cart", methods=['post'])
def cart():
    item_id = request.form.get("item_id")
    item_quantity = request.form.get("item_quantity")
    customer_id = session["customer_id"]
    query = {"customer_id": ObjectId(customer_id), "status": "cart"}
    count = customer_order_col.count_documents(query)
    if count == 0:
        query = {"customer_id": ObjectId(customer_id), "status": "cart", "date": datetime.datetime.now()}
        result = customer_order_col.insert_one(query)
        customer_order_id = result.inserted_id
    else:
        customer_order = customer_order_col.find_one(query)
        customer_order_id = customer_order['_id']
    query = {"customer_order_id": customer_order_id, "item_id": ObjectId(item_id)}
    count = customer_order_item_col.count_documents(query)

    if count == 0:
        query = {"customer_order_id": customer_order_id, "item_id": ObjectId(item_id), "item_quantity": item_quantity}
        result = customer_order_item_col.insert_one(query)
        return render_template("Cmsg.html", message="product added to cart")
    else:
        query = {"customer_order_id": customer_order_id, "item_id": ObjectId(item_id)}
        customer_order_item = customer_order_item_col.find_one(query)
        query2 = {"$set": {"item_quantity": str(int(customer_order_item['item_quantity'])) + str(item_quantity)}}
        customer_order_item_col.update_one(query,query2)
        return render_template("Cmsg.html", message="Product Updated Successfully")

@app.route("/view_cart")
def view_cart():
    role = session['role']
    type = request.args.get("type")
    query = ""
    if role == 'customer':
        customer_id = session['customer_id']
        if type == 'cart':
            query = {"customer_id": ObjectId(customer_id),"status": "cart"}
        elif type == 'ordered':
            query = {"$or": [{"customer_id": ObjectId(customer_id), "status":"ordered"},{"customer_id": ObjectId(customer_id), "status":"dispatched"}]}
        elif type == 'history':
            query = {"$or": [{"customer_id": ObjectId(customer_id), "status":"delivered"},{"customer_id": ObjectId(customer_id), "status":"cancelled"}]}
    else:
        if type == 'ordered':
            query = {"status": "ordered"}
        elif type == 'dispatched':
            query = {"status": "dispatched"}
        elif type == 'history':
            query = {"$or": [{"status": "delivered"},{"status": "cancelled"}]}
    customer_orders = customer_order_col.find(query)
    return render_template("view_cart.html", customer_orders=customer_orders,get_customer_by_customer_id=get_customer_by_customer_id,get_customer_order_items_by_customer_order_id=get_customer_order_items_by_customer_order_id,get_item_by_item_id=get_item_by_item_id,get_category_by_category_id=get_category_by_category_id, int=int)


def get_customer_by_customer_id(customer_id):
    query = {"_id": ObjectId(customer_id)}
    customers = customer_col.find_one(query)
    return customers


def get_customer_order_items_by_customer_order_id(customer_order_id):
    query = {"customer_order_id": customer_order_id}
    customer_order_items = customer_order_item_col.find(query)
    customer_order_items = list(customer_order_items)
    return customer_order_items


def get_item_by_item_id(item_id):
    print(item_id)
    query = {'_id': item_id}
    item = items_col.find_one(query)
    return item


def get_category_by_category_id(category_id):
    query = {"category_id": category_id}
    category_id = category_col.find(query)
    return category_id


@app.route("/order", methods=["get"])
def order():
    customer_order_id = request.args.get("customer_order_id")
    total_price = request.args.get("total_price")
    delivery_type = request.args.get("delivery_types")
    query = {"_id": ObjectId(customer_order_id)}
    query1 = {"$set": {"delivery_type": delivery_type, "status": "Ordered Items"}}
    customer_order_col.update_one(query, query1)
    return render_template("order.html", customer_order_id=customer_order_id, total_price=total_price)

@app.route("/update_status", methods=["post"])
def update_status():
    customer_order_id = request.form.get("customer_order_id")
    query = {"_id": ObjectId(customer_order_id)}
    query2 = {"$set": {"status": 'ordered'}}
    customer_order_col.update_one(query, query2)
    query = {"customer_order_id" : ObjectId(customer_order_id)}
    customer_order_items = customer_order_item_col.find(query)
    for customer_order_item in customer_order_items:
        query = {"_id": customer_order_item['item_id']}
        item = items_col.find_one(query)
        if int(item['item_quantity']) < int(customer_order_item['item_quantity']):
            query1 = {"_id": customer_order_id}
            query2 = {"$set": {"status": "not available"}}
            customer_order_item_col.update_one(query1,query2)
        else:
            query1 = {"_id": item['_id']}
            query2 = {"$set": {"item_quantity": int(item['item_quantity'])-int(customer_order_item['item_quantity'])}}
            items_col.update_one(query1,query2)
    return render_template("Cmsg.html", message="Order Placed Successfully")

@app.route("/pay_now")
def pay_now():
    customer_order_id = request.form.get("customer_order_id")
    query = {"_id": ObjectId(customer_order_id)}
    query2 = {"$set": {"status": "ordered"}}
    customer_order_col.update_one(query, query2)
    return render_template("Cmsg.html", message="Payment done  successfull")


@app.route("/update_ordered")
def update_ordered():
    customer_order_id = request.args.get("customer_order_id")
    query = {"_id": ObjectId(customer_order_id)}
    query2 = {"$set": {"status": 'Delivered'}}
    customer_order_col.update_one(query,query2)
    return render_template("Amsg.html", message="Order Delivered")


# @app.route("/update_dispatched")
# def update_dispatched():
#     customer_order_id = request.args.get("customer_order_id")
#     query = {"_id": ObjectId(customer_order_id)}
#     query2 = {"$set": {"status": 'delivered'}}
#     customer_order_col.update_one(query, query2)
#     return render_template("Cmsg.html", message="Order Received")


@app.route("/update_ordered1", methods=["post"])
def update_ordered1():
    customer_order_id = request.form.get("customer_order_id")
    query = {"_id": ObjectId(customer_order_id)}
    query2 = {"$set": {"status": 'cancelled'}}
    customer_order_col.update_one(query, query2)
    return render_template("Cmsg.html",message="Order Cancelled")


@app.route("/remove")
def remove():
    customer_order_item_id = request.args.get("customer_order_item_id")
    query = {'_id': ObjectId(customer_order_item_id)}
    customer_order_item = customer_order_item_col.find_one(query)
    customer_order_item_col.delete_one(query)
    query2 = {'customer_order_id': customer_order_item['customer_order_id']}
    count = customer_order_item_col.count_documents(query2)
    if count == 0:
        query = {"_id": customer_order_item['customer_order_id']}
        customer_order_col.delete_one(query)
    return render_template("Cmsg.html", message="Item Removed From The Cart")


@app.route("/about")
def about():
    return render_template("about.html")


app.run(debug=True)
