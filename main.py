import json # to convert json file object into python dictionary
import os
import re # to save image files and running system commands
from flask import Flask, jsonify, request # to make server and send json as response and to get values from request parameters
from MongoController import MongoController # to control mongodb
from flask_cors import CORS # allow cross origin
import hashlib # for hashing passwords into hash



# json to store variables in json file
__variable_json_path__ = r"D:\Github Projects\social_media_website_backend\secret_variables.json"

# reads file
file = open(__variable_json_path__,"r")

# converts json file into python dictionary
variables = json.load(file)


app = Flask(__name__)

# configures upload folder from json file folder location
app.config['UPLOAD_FOLDER'] = variables["UPLOAD_FOLDER"]

# allows cross origin
CORS(app)

# class to manage mongodb database
db = MongoController(variables["db_uri"], variables["db_name"],variables["collection_name"],variables["admin_name"],variables["admin_password"])
db.set_collection()


# checks if given filename is in allowed list
def allowed_file(filename,allowed_extension_list=variables["ALLOWED_EXTENSIONS"]):
    """
    Usage : checks if given filename is in allowed list
    
    FILENAME : name of file to check if it has allowed extension
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extension_list


def secure_filename(email,file_extension="png"):
    """
    Usage : It returns the secure name of file
    
    EMAIL : it is the email of the user to save file
    
    FILE_EXTENSION : extension of file to save
    """
    return f"avatar.{email}.{file_extension}"


def secure_filename_post(title,email,file_extension="png"):
    """
    Usage : It returns the secure name of file
    
    TITLE : title of the post
    
    EMAIL : it is the email of the user to save file
    
    FILE_EXTENSION : extension of file to save
    """
    
    title = title.split(" ")
    title = ''.join(title)
    return f"post_file.{title}.{email}.{file_extension}"


@app.route("/login",methods=['GET', 'POST'])
def Login():
    """
    Usage : It is the API for login the user through only post request and stores its information in mongodb
    """
    if request.method == "POST":
        data = request.get_json()
        email = data["email"]
        password = data["password"]
        if len(password) < 8:
            return jsonify({
                "sucess":False,
                "message":"It must be at least 8 digits",
                "title":"Password is too short"
            })
        hash = hashlib.sha256()
        hash.update(password.encode())
        hash = hash.hexdigest()
        result = db.search({"email":email,"password":hash})
        if result:
            username = result["username"]
            password = result["password"]
            print(username,password)
            return jsonify({
                "sucess":True,
                "message":"Login Sucessfully.",
                "Api_Key":password,
                "User_Name":username,
                "email":email}
                )
        else:
            return jsonify(
                {"sucess":False,
                 "message":"Please enter correct email or password"
                })
    else:
        return jsonify({
            "error":"This method is not allowed."
        })

@app.route("/signup",methods=['GET', 'POST'])
def SignUp():
    if request.method == "POST":
        data = request.form
        print(data)
        username = data["username"]
        email = data["email"]
        mobile_number = data["mobile_number"]
        if len(mobile_number) < 8:
            return jsonify({
                "sucess":False,
                "message":"mobile number must be 10 digits",
                "title":"Invalid Mobile Number"
            })
        password = data["password"]
        if len(password) < 8:
            return jsonify({
                "sucess":False,
                "message":"It must be at least 8 digits",
                "title":"Password is too short"
            })
        avatar = request.files["userimage"]
        if avatar.filename == '':
            print('No selected file')
            return "No file selected"

        hash = hashlib.sha256()
        hash.update(password.encode())
        hash = hash.hexdigest()
        if avatar and allowed_file(avatar.filename):
            # filename = secure_filename(email)
            db.insert_unique_data_in_collection({
                "username":username,
                "email":email,
                "mobile_number":mobile_number,
                "password":hash,
                "avatar":avatar
            },"email")
            return jsonify({"sucess":True,"message":"Account created sucessfully.","Api_Key":hash,"User_Name":username,"email":email,"avatar":avatar})
            
    else:
        return jsonify({
            "error":"This method is not allowed."
        })
   
@app.route("/getfriends",methods=["GET","POST"])
def GetFriends():
    if request.method == "POST":
        data = request.get_json()
        email = data["email"]
        api_key = data["api_key"]
        count = 10
        result = db.search({"password":api_key,"email":email})
        dbemail = result["email"]
        print(dbemail,email)
        if email == dbemail:
            users = db.get_some_data(count,["password","mobile_number","_id"])
            return jsonify({"sucess":True,
                            "message":"User found",
                            "friends" : users})
        else:
            return jsonify({"sucess":False,
                            "message":"Invalid user details",
                            "title":"No such user"})
    else:
        return jsonify({
            "error":"This method is not allowed."
        })


@app.route("/add-post",methods=["GET",'POST'])
def AddPost():
    if request.method == "POST":
        if 'post_file' not in request.files:
            print("No file.")
            return "No file"
        file = request.files["post_file"]
        print(file)
        print(request.form)
        email = request.form["email"]
        api_key = request.form["api_key"]
        post_title = request.form["post_title"]
        post_desc = request.form["post_desc"]
        print(file.filename)
        if file.filename == '':
            print('No selected file')
            return jsonify({"sucess":False,"message":"Invalid user"})

        if file and allowed_file(file.filename):
            filename = secure_filename_post(post_title,email)
            info = {
                "password":api_key,
                "email":email,
                "post_file":secure_filename_post(post_title,email)
            }
            # db.insert_unique_data_in_collection(info,"post_file")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return jsonify({"sucess":False,"message":"Invalid user"})
        else:
            return jsonify({"sucess":False,"message":"Invalid user"})
            
    else:
        print("Wrong Mehtod")
        return jsonify({"sucess":False,"message":"Invalid user"})

@app.route("/add-friend",methods=["GET","POST"])
def AddFriend():
    if request.method == "POST":
        data = request.get_json()
        print(data)
        email = data["email"]
        friend_email = data["friend_email"]
        api_key = data["api_key"]
        info = {"email":email,
                "password":api_key}
        result = db.search(info)
        print(result)
        if result:
            print(result)
            print("returning 3")
            collection_exists = db.search_collection(f"friends-{email}")
            print("returning 1")
            print(collection_exists)
            print("returning 2")
            if collection_exists:
                db.change_collection(f"friends-{email}")
                db.set_collection()
                db.insert_unique_data_in_collection({"friend_email":friend_email})
                print("returning 4")
                return jsonify({"success":True})
            else:
                db.create_collection(f"friends-{email}")
                db.insert_unique_data_in_collection({"friend_email":friend_email})
                return jsonify({"success":True})

    else:
        return "Wrong Method"


    

if __name__ == "__main__":
    app.run(debug=True,port=2500)