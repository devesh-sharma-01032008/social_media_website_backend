import json
import os
from flask import Flask, flash, jsonify, request
from UserManagementMongoDB import UserManagementMongoDB
from flask_cors import CORS
import hashlib

file = open(r"D:\Github Projects\social_media_website_backend\secret_variables.json","r")
variables = json.load(file)


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = variables["UPLOAD_FOLDER"]

CORS(app)


db = UserManagementMongoDB(variables["db_uri"], variables["db_name"],variables["collection_name"],variables["admin_name"],variables["admin_password"])
db.set_collection()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in variables["ALLOWED_EXTENSIONS"]

def secure_filename(email):
    return f"avatar.{email}.png"

@app.route("/login",methods=['GET', 'POST'])
def Login():
    if request.method == "POST":
        data = request.get_json()
        email = data["email"]
        password = data["password"]
        hash = hashlib.sha256()
        hash.update(password.encode())
        hash = hash.hexdigest()
        result = db.search({"email":email,"password":hash})
        if result:
            username = result["username"]
            password = result["password"]
            print(username,password)
            return jsonify({"sucess":True,"message":"Login Sucessfully.","Api_Key":password,"User_Name":username,"email":email})
        else:
            return jsonify({"sucess":False,"message":"Please enter correct email or password"})
    else:
        return "Wrong Method"

@app.route("/signup",methods=['GET', 'POST'])
def SignUp():
    if request.method == "POST":
        data = request.get_json()
        username = data["username"]
        email = data["email"]
        mobile_number = data["mobile_number"]
        password = data["password"]
        avatar = False
        if secure_filename(email) in os.listdir("./upload/avatar"):
            avatar = True
        hash = hashlib.sha256()
        hash.update(password.encode())
        hash = hash.hexdigest()
        if avatar:
            result = db.insert_unique_data_in_collection({"username":username,"email":email,"mobile_number":mobile_number,"password":hash,"avatar":secure_filename(email)},"email")
        else:
            result = db.insert_unique_data_in_collection({"username":username,"email":email,"mobile_number":mobile_number,"password":hash},"email")
            
        if result:
            return jsonify({"sucess":True,"message":"Account created sucessfully.","Api_Key":hash,"User_Name":username,"email":email,"avatar":"avatar.default.png"})
        else:
            return jsonify({"sucess":False,"message":"Account with this email already exists."})
    else:
        return "Wrong Method"
   
@app.route("/getfriends",methods=["GET","POST"])
def GetFriends():
    if request.method == "POST":
        data = request.get_json()
        email = data["email"]
        api_key = data["api_key"]
        count = data["count"]
        result = db.search({"password":api_key,"email":email})
        dbemail = result["email"]
        print(dbemail,email)
        if email == dbemail:
            print("Hello")
            users = db.get_some_data(count,["password","mobile_number","_id"])
            return jsonify({"sucess":True,"message":"User found", "friends" : users})
        else:
            return jsonify({"sucess":False,"message":"Invalid user"})
    else:
        return "Wrong Method"

@app.route("/upload-avatar",methods=["GET","POST"])
def Upload_Avatar():
    if request.method == "POST":
        if 'userimage' not in request.files:
            print("No file.")
            return "No file"
        file = request.files["userimage"]
        print(file)
        email = request.form["email"]
        if file.filename == '':
            flash('No selected file')
            print('No selected file')
            return "No file selected"

        if file and allowed_file(file.filename):
            filename = secure_filename(email)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return "sucess"

@app.route("/add-post",methods=["GET",'POST'])
def AddPost():
    if request.method == "POST":
        if 'postfile' not in request.files:
            print("No file.")
            return "No file"
        file = request.files["postfile"]
        print(file)
        email = request.form["email"]
        api_key = request.form["api_key"]
        
        if file.filename == '':
            flash('No selected file')
            print('No selected file')
            return "No file selected"

        if file and allowed_file(file.filename):
            filename = secure_filename(email)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return "sucess"

    else:
        return "Wrong Mehtod"

@app.route("/add-friend",methods=["GET","POST"])
def AddFriend():
    if request.method == "POST":
        data = request.get_json()
        email = data["email"]
        friend_email = data["friend_email"]
        api_key = data["api_key"]
        info = {"email":email,
                "password":api_key}
        result = db.search(info)
        if result:
            print(result)
        collection_exists = db.search_collection(f"friends-{email}");
        if collection_exists:
            db.collection(f"friends-{email}")
            db.insert_unique_data_in_collection(info);
        else:
            db.create_collection(f"friends-{email}") # to  implement
            db.insert_unique_data_in_collection(info)
            return jsonfiy({"success":True})
    else:
        return "Wrong Method"


    

if __name__ == "__main__":
    app.run(debug=True,port=2500)