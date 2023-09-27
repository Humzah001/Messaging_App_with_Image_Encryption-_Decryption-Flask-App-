import datetime
import os
import re
import mysql.connector
from flask import Flask, render_template, request, redirect, flash, session, url_for
import secrets
from PIL import Image, ImageDraw, ImageFont
import io
from io import BytesIO
import base64

# from cryptography.fernet import Fernet


app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # 16 bytes will generate a 32-character secret key


# Replace the placeholders with your MySQL database credentials
db = mysql.connector.connect(
    host="localhost",#this is same
    user="root",
    password="a123",
    database="systemtool"
)

@app.route('/login',methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        cursor = db.cursor()
        # Replace 'users' with the name of your table
        cursor.execute(f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}' AND role = '{role}'")  
        user = cursor.fetchone()
        if user:
            session['user_id'] = user[0]
            if role == 'user':
                # Redirect to the user page
                return redirect('/user')
            elif role == 'admin':
                # Redirect to the admin page
                return redirect('/admin')
        else:
            # Redirect to an error page
            flash('Invalid username, password, or role. Please try again.', 'error')
            return redirect('/login')

    return render_template('login.html')

@app.route("/")
@app.route("/home")
def index():
    return render_template('home.html')


@app.route("/signuped", methods=['GET', 'POST'])
def signuped():
    return render_template('signup.html')
   
@app.route("/signup", methods=['GET', 'POST'])
def signup():
     if request.method == 'POST':
        # Get form data
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = request.form['role']

        # Check if password and confirm_password match
        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'error')
        else:
            cursor = db.cursor()
            # Insert the form data into the database
            query = "INSERT INTO users (username, email, phone, password, role) VALUES (%s, %s, %s, %s, %s)"
            values = (username, email, phone, password, role)
            cursor.execute(query, values)
            db.commit()
            flash('Account created successfully.', 'success')
            return redirect('/login')  # Redirect to login page on success
     return render_template('signup.html')

@app.route("/admin/<int:id>",methods=['GET', 'POST'])
@app.route("/admin")
def admin(id=None):
    cursor = db.cursor()
    cursor.execute("SELECT id, Description FROM report")
    repo =[{'id': row[0], 'Description': row[1]} for row in cursor.fetchall()]
    db.commit()


    if id!=None:
       cursor.execute("DELETE FROM report WHERE id = %s", (id,))
       cursor.execute("DELETE FROM message WHERE senderid = %s OR receiverid = %s", (id,id))
       cursor.execute("DELETE FROM users WHERE id = %s", (id,))
       db.commit()

    return render_template('admin.html',repo=repo)

@app.route("/user")
def user():
    return render_template('user.html')


@app.route("/report/<int:id>",methods=['GET', 'POST'])
@app.route("/report",methods=['GET', 'POST'])
def report(id=None):
    users= []
    cursor = db.cursor()
    uid =int(session.get('user_id'))
    cursor.execute("SELECT username, email , id FROM users where id<>1")
    users =[{'id': row[2],'email': row[1], 'username': row[0]} for row in cursor.fetchall()]
    db.commit()

    if id!=None:
        Description = request.form['Description']
        query = "INSERT INTO report(id,Description) VALUES (%s, %s)"
        values = (id, Description)
        cursor.execute(query, values)
        db.commit()

    return render_template('report.html',users=users)



def get_user_data():
    uid =int(session.get('user_id'))
    cursor = db.cursor()
    cursor.execute("SELECT username, password, phone, description, Email FROM users WHERE id = %s", (uid,))
    user_data = cursor.fetchone()
    
    return user_data
@app.route('/myaccount', methods=['GET', 'POST'])
def myaccount():
    uid =int(session.get('user_id'))
    if request.method == 'POST':
        # Handle form submission to update user data in the database
        new_username = request.form['username']
        new_password = request.form['password']
        new_phone = request.form['phone']
        new_description = request.form['description']

        # Update the user's data in the database (use appropriate SQL)
        cursor = db.cursor()
        query="UPDATE users SET username=%s, password=%s, phone=%s, description=%s WHERE id =%s" 
        values=(new_username, new_password, new_phone, new_description,uid)
        cursor.execute(query,values)
        db.commit()
        

    user_data = get_user_data()
    return render_template('myaccount.html', user_data=user_data)

@app.route("/newchat",methods=['GET', 'POST'])
def newchat():
    cursor = db.cursor()
    uid =int(session.get('user_id'))
    cursor.execute("SELECT username, Email , id FROM users where id<>1")
    user_data =[{'id': row[2],'email': row[1], 'username': row[0]} for row in cursor.fetchall()]
    db.commit()
        

    return render_template('newchat.html',user_data=user_data)


@app.route("/newchats/<int:receiver_id>",methods=['GET', 'POST'])
@app.route("/newchats",methods=['GET', 'POST'])
def newchats(receiver_id = None):
    if id!=None:
        message = request.form.get('Description')
        cursor = db.cursor()
        uid =int(session.get('user_id'))
        cursor.execute("insert into message(content, date, receiverid, senderid) values (%s, %s, %s, %s)", (message, datetime.datetime.now(),receiver_id, uid,))
        db.commit()
        
    return redirect(url_for('chats'))

@app.route("/chats/<int:user_id>",methods=['GET', 'POST'])
@app.route('/chats', methods=['GET', 'POST'])
def chats(user_id=None):
    message_data=[]
    sender_message = []
    messages = []
    binary_data_list = []
    image_data = []
    # to show recet chats
    cursor = db.cursor()
    uid =int(session.get('user_id'))
    cursor.execute("SELECT DISTINCT u.username , m.senderid FROM users u join message m on id= m.senderid where m.receiverid = %s", (uid,))
    chat_data = [{'sender_id': row[1], 'username': row[0]} for row in cursor.fetchall()]
    cursor.close()

    if user_id!=None:
        cursor2 = db.cursor()
        cursor2.execute("select content, date, senderid , img from message where senderid = %s and receiverid = %s", (user_id,uid,))
        message_data = [{'content': row[0], 'date': row[1], 'sender_id': row[2], 'img': row[3]} for row in cursor2.fetchall()] 
        cursor2.execute("select content, date, senderid ,img from message where senderid = %s and receiverid = %s", (uid, user_id,))
        sender_message = [{'content': row[0], 'date': row[1], 'sender_id': row[2]} for row in cursor2.fetchall()]
        cursor2.execute("select date, senderid ,img from message where senderid = %s and receiverid = %s", (uid, user_id,))
        image_data1=[ {'img': row[2],'date': row[0], 'sender_id': row[1]} for row in cursor2.fetchall()]
        cursor2.execute("select date, senderid ,img from message where senderid = %s and receiverid = %s", (user_id, uid,))
        image_data2=[ {'img': row[2],'date': row[0], 'sender_id': row[1]} for row in cursor2.fetchall()]
        cursor2.close()
        messages = message_data + sender_message
        
        image_data = image_data1 + image_data2
        image_data = sorted(image_data, key=lambda x: x['date'])
        image_data = [item for item in image_data if item['img'] is not None]
        # Your Base64 encoded string
        for item in image_data:
            if item['img'] is not None:
                base64_data = item['img']
                print("base64_data")
                print(base64_data)
                
                binary_data = base64.b64decode(base64_data)
                print("binary_data")
                print(binary_data)
                binary_data_list.append(base64.b64encode(binary_data).decode('utf-8'))
        
        count = 0
        for item in image_data:
            item['image'] = binary_data_list[count]
            count = count + 1

        print(binary_data_list)
        messages = sorted(messages, key=lambda x: x['date'])

    return render_template('chat.html', recent_chats=chat_data, messages = messages, uid=uid, sender_id = user_id,binary_data_list=image_data)

@app.route("/sendmessage/<int:receiver_id>",methods=['GET', 'POST'])
def sendmessage(receiver_id = None):
    message = request.form.get('message')
    cursor = db.cursor()
    uid =int(session.get('user_id'))
    cursor.execute("insert into message(content, date, receiverid, senderid) values (%s, %s, %s, %s)", (message, datetime.datetime.now(), receiver_id, uid,))
    cursor.close()
    db.commit()
    return redirect(url_for('chats'))

@app.route("/encrypt", methods=["GET", "POST"])
def encrypt():
    image_path =''
    encoded = ''
    image_name = ''
    if request.method == "POST":
        email = request.form['email']
        text_to_hide = request.form["hidden-text"]
        image = request.files["image"]
        app.config['UPLOAD_FOLDER'] = 'static'
        # Check if all required fields are provided
        try:
            cursor = db.cursor()
            cursor.execute("SELECT id FROM users WHERE Email = %s", (email,))
            user_id = cursor.fetchone()
            cursor.close()
            db.commit()
            user_id = user_id[0]
            if user_id is None:
                # Email does not exist in the database
                flash('User Not Found.', 'error')

            else:
                # Create a directory to store uploaded images (if not exists)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

                # Save the uploaded image to the 'uploads' directory
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
                image_name = image.filename
                image.save(image_path)

                encoded = encode_image(image_path, text_to_hide, app.config['UPLOAD_FOLDER'], image.filename)
                
                # Open and read the image file in binary mode
                with open(encoded, "rb") as image_file:
                    # Read the binary data
                    binary_data = image_file.read()
                
                print("---------------------------------------------------------")
                print("binary data image ->")
                print(binary_data)
                print("---------------------------------------------------------")

                # Encode the binary data into a Base64 string
                base64_data = base64.b64encode(binary_data).decode('utf-8')
                print("---------------------------------------------------------")
                print("Base64 image ->")
                print(base64_data)
                print("---------------------------------------------------------")

                cursor = db.cursor()
                empty= ""
                uid =int(session.get('user_id'))
                
                print("---------------------------------------------------------")
                print("uid ->")
                print(uid)
                print("---------------------------------------------------------")


                cursor.execute("insert into message(content, date, receiverid, senderid,img) values ( %s, %s, %s, %s, %s)", ( empty,datetime.datetime.now(), user_id, uid,base64_data,))
                cursor.close()
                db.commit()
                print("---------------------------------------------------------")
                print("query executed")
                print("---------------------------------------------------------")
                return render_template("encrypt.html", source =image_path, encoded = encoded)

        except Exception as e:
                return str(e)

    return render_template("encrypt.html", source =image_name, encoded = encoded)


def encode_image(image_path, message, output_path, image_name):
    img = Image.open(image_path)
    width, height = img.size
    encoded_image = img.copy()

    # binary_message = ''.join(format(ord(char), '08b') for char in message)
    binary_message = ''.join(format(ord(char), '08b') for char in message)
    print(binary_message)
    message_length = len(binary_message)

    if message_length > (width * height):
        raise ValueError("Message is too long to be encoded in the image")

    # Add the delimiter to the binary message
    binary_message += '1111111111111110'
    print(binary_message)
    message_length = len(binary_message)

    data_index = 0
    for y in range(height):
        for x in range(width):
            pixel = list(encoded_image.getpixel((x, y)))

            for color_channel in range(3):
                if data_index < message_length:
                    bit_to_encode = int(binary_message[data_index])
                    pixel[color_channel] = (pixel[color_channel] & 254) | bit_to_encode
                    data_index += 1

            encoded_image.putpixel((x, y), tuple(pixel))

            if data_index == message_length:
                break
        if data_index == message_length:
            break

    encoded_image.save(output_path+"/encoded.png")
    print("Message encoded successfully.")

    return output_path+"\encoded.png"

@app.route("/decrypt", methods=["GET", "POST"])
def decrypt():
    image_path =''
    secret_message = ''
    if request.method == "POST":
        image = request.files["image"]
        app.config['UPLOAD_FOLDER'] = 'static'

        try:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
            image.save(image_path)
            secret_message = decode_image(image_path)

            return render_template("decrypt.html", message = secret_message)

        except Exception as e:
                return str(e)

    return render_template("decrypt.html", message = secret_message)


def decode_image(image_path):
    img = Image.open(image_path)
    width, height = img.size

    binary_message = ''
    data_index = 0
    delimiter = '1111111111111110'
    delimiter_found = False  # Variable to track if the delimiter is found

    for y in range(height):
        for x in range(width):
            pixel = list(img.getpixel((x, y)))

            for color_channel in range(3):
                binary_message += str(pixel[color_channel] & 1)
                data_index += 1
                # Check for the delimiter in the binary message
                if binary_message[-16:] == delimiter:
                    # print(binary_message)
                    # Remove the delimiter
                    binary_message = binary_message[:-16]
                    delimiter_found = True  # Set the flag to indicate delimiter found
                    break  # Exit the loop when the delimiter is found

            if delimiter_found:
                break  # Exit the loop when the delimiter is found

    if delimiter_found:
        # Convert the binary message to text
        decoded_message = ''.join(chr(int(binary_message[i:i + 8], 2)) for i in range(0, len(binary_message), 8))
        english_characters = re.match(r'[A-Za-z0-9 ]+', decoded_message)

        if english_characters is not None:
            # Join the English characters into a single string
            english_text = english_characters.group()
            return english_text
        else:
            return "No Secret Message Found"
    else:
        return "Delimiter not found in the encoded image."
if __name__ == '__main__':
    app.run(debug=True)