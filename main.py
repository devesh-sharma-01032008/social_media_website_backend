import json  # to convert json file object into python dictionary
import os  # to save image files and running system commands
from flask import (
    Flask,
    jsonify,
    request,
    send_file,
)  # to make server and send json as response and to get values from request parameters
from MongoController import MongoController  # to control mongodb
from flask_cors import CORS  # allow cross origin
import hashlib  # for hashing passwords into hash


# json to store variables in json file
__variable_json_path__ = (
    r"D:\Github Projects\social_media_website_backend\secret_variables.json"
)

# reads file
file = open(__variable_json_path__, "r")

# converts json file into python dictionary
variables = json.load(file)


app = Flask(__name__)

# configures upload folder from json file folder location
app.config["UPLOAD_FOLDER"] = variables["UPLOAD_FOLDER"]

# allows cross origin
CORS(app)

# class to manage mongodb database
db = MongoController(
    variables["db_uri"],
    variables["db_name"],
    variables["collection_name"],
    variables["admin_name"],
    variables["admin_password"],
)
db.set_collection()


# checks if given filename is in allowed list
def allowed_file(filename, allowed_extension_list=variables["ALLOWED_EXTENSIONS"]):
    """
    ``Usage`` : checks if given filename is in allowed list

    ``FILENAME`` : name of file to check if it has allowed extension
    """
    return (
        "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extension_list
    )


def secure_filename(email, file_extension="png"):
    """
    ``Usage`` : It returns the secure name of file

    ``EMAIL`` : it is the email of the user to save file

    ``FILE_EXTENSION`` : extension of file to save
    """
    return f"avatar.{email}.{file_extension}"


def secure_filename_post(title, email, file_extension="png"):
    """
    ``Usage`` : It returns the secure name of file

    ``TITLE`` : title of the post

    ``EMAIL`` : it is the email of the user to save file

    ``FILE_EXTENSION`` : extension of file to save
    """

    title = title.split(" ")
    title = "".join(title)
    return f"post_file.{title}.{email}.{file_extension}"


def get_extension(filename):
    """
    ``Usage`` : It gives the extension of file

    ``FILENAME`` : it is the name of file for which you want its extension
    """
    return filename.split(".")[len(filename.split(".")) - 1]


@app.route("/login", methods=["GET", "POST"])
def Login():
    """
    ``Usage`` : It is the API for login the user through only post request and stores its information in mongodb
    """
    if request.method == "POST":
        data = request.get_json()
        email = data["email"]
        password = data["password"]
        if len(password) < 8:
            return jsonify(
                {
                    "sucess": False,
                    "message": "It must be at least 8 digits",
                    "title": "Password is too short",
                }
            )
        hash = hashlib.sha256()
        hash.update(password.encode())
        hash = hash.hexdigest()
        db.change_collection("user_details")
        db.set_collection()
        result = db.search({"email": email, "password": hash})
        if result:
            username = result["username"]
            password = result["password"]
            avatar = result["avatar"]
            return jsonify(
                {
                    "sucess": True,
                    "message": "Login Sucessfully.",
                    "Api_Key": password,
                    "User_Name": username,
                    "email": email,
                    "avatar": avatar,
                }
            )
        else:
            return jsonify(
                {"sucess": False, "message": "Please enter correct email or password"}
            )
    else:
        return jsonify({"error": "This method is not allowed."})


@app.route("/signup", methods=["GET", "POST"])
def SignUp():
    if request.method == "POST":
        data = request.form
        db.change_collection("user_details")
        db.set_collection()
        username = data["username"]
        email = data["email"]
        mobile_number = data["mobile_number"]
        if len(mobile_number) < 8:
            return jsonify(
                {
                    "sucess": False,
                    "message": "mobile number must be 10 digits",
                    "title": "Invalid Mobile Number",
                }
            )
        password = data["password"]
        if len(password) < 8:
            return jsonify(
                {
                    "sucess": False,
                    "message": "It must be at least 8 digits",
                    "title": "Password is too short",
                }
            )
        avatar = request.files["userimage"]
        if avatar.filename == "":
            return "No file selected"

        hash = hashlib.sha256()
        hash.update(password.encode())
        hash = hash.hexdigest()
        if avatar and allowed_file(avatar.filename):
            db.insert_unique_data_in_collection(
                {
                    "username": username,
                    "email": email,
                    "mobile_number": mobile_number,
                    "password": hash,
                    "avatar": secure_filename(email, get_extension(avatar.filename)),
                },
                "email",
            )
            os.mkdir(app.config["UPLOAD_FOLDER"] + "\\avatar" "\\" + email + "\\")
            avatar.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"] + "\\avatar" "\\" + email + "\\",
                    secure_filename(email, get_extension(avatar.filename)),
                )
            )
            return jsonify(
                {
                    "sucess": True,
                    "message": "Account created sucessfully.",
                    "Api_Key": hash,
                    "User_Name": username,
                    "email": email,
                    "avatar": secure_filename(email, get_extension(avatar.filename)),
                }
            )

    else:
        return jsonify({"error": "This method is not allowed."})


@app.route("/add-friend", methods=["GET", "POST"])
def AddFriend():
    if request.method == "POST":
        data = request.get_json()
        db.change_collection("user_details")
        db.set_collection()
        email = data["email"]
        friend_email = data["friend_email"]
        api_key = data["api_key"]
        info = {"email": email, "password": api_key}
        result = db.search(info)
        if result:
            collection_exists = db.search_collection(f"friends-{email}")
            if collection_exists:
                db.change_collection(f"friends-{email}")
                db.set_collection()
                db.insert_unique_data_in_collection({"friend_email": friend_email})
                return jsonify({"success": True})
            else:
                db.create_collection(f"friends-{email}")
                db.insert_unique_data_in_collection({"friend_email": friend_email})
                return jsonify({"success": True})

    else:
        return "Wrong Method"


@app.route("/getfriends", methods=["GET", "POST"])
def GetFriends():
    if request.method == "POST":
        data = request.get_json()
        email = data["email"]
        api_key = data["api_key"]
        count = 30
        db.change_collection("user_details")
        db.set_collection()
        result = db.search({"password": api_key, "email": email})
        dbemail = result["email"]
        if email == dbemail:
            users = db.get_some_data(count, ["password", "mobile_number", "_id"])
            return jsonify({"sucess": True, "message": "User found", "friends": users})
        else:
            return jsonify(
                {
                    "sucess": False,
                    "message": "Invalid user details",
                    "title": "No such user",
                }
            )
    else:
        return jsonify({"error": "This method is not allowed."})


@app.route("/add-post", methods=["GET", "POST"])
def AddPost():
    if request.method == "POST":
        if "post_file" not in request.files:
            return "No file"
        file = request.files["post_file"]
        email = request.form["email"]
        api_key = request.form["api_key"]
        post_title = request.form["post_title"]
        post_desc = request.form["post_desc"]
        if file.filename == "":
            return jsonify({"sucess": False, "message": "No file selected"})

        if file:
            filename = secure_filename_post(
                post_title, email, get_extension(file.filename)
            )
            info = {
                "password": api_key,
                "email": email,
                "post_file": filename,
                "post_title": post_title,
                "post_desc": post_desc,
            }
            if not db.search_collection("posts-" + email):
                db.create_collection("posts-" + email)

            db.change_collection("posts-" + email)
            db.set_collection()
            db.insert_unique_data_in_collection(info)
            try:
                os.mkdir(app.config["UPLOAD_FOLDER"] + "\\post_files" "\\" + email)
            except Exception as e:
                print(e)
            finally:
                file.save(
                    os.path.join(
                        app.config["UPLOAD_FOLDER"] + "\\post_files"
                        "\\" + email + "\\",
                        filename,
                    )
                )
                return jsonify({"sucess": True})
        else:
            return jsonify({"sucess": False, "message": "Invalid user"})

    else:
        return jsonify({"sucess": False, "message": "Invalid user"})


@app.route("/get_posts", methods=["GET", "POST"])
def GetPosts():
    if request.method == "POST":
        data = request.get_json()
        email = data["email"]
        api_key = data["api_key"]
        info = {
            "password": api_key,
            "email": email,
        }
        if db.search(info):
            posts_collection = db.get_some_posts()
            return jsonify({"sucess": True, "posts": posts_collection})
    else:
        return jsonify({"sucess": False, "message": "Invalid user"})


@app.route("/get_image_file")
def get_image_file():
    arguments = request.args
    email = arguments["email"]
    file_name = arguments["file_name"]
    directory = arguments["image_category"]
    file_dir = f"{os.getcwd()}\\upload\\{directory}\\{email}\\{file_name}"
    return send_file(file_dir, mimetype="image/jpg")


if __name__ == "__main__":
    app.run(debug=True, port=2500)
