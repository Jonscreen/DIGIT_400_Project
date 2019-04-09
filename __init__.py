from flask import Flask, render_template, url_for, flash, request, redirect, session, make_response, send_file
from wtforms import Form, BooleanField, TextField, PasswordField, validators
from passlib.hash import sha256_crypt
from pymysql import escape_string as thwart
from functools import wraps
import gc
import os, sys; sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from werkzeug.utils import secure_filename
from content import Content
#from connect import connection
import sqlite3 as lite
from datetime import datetime, timedelta
from bs4 import BeautifulSoup 
import csv
import requests

UPLOAD_FOLDER = "/var/www/FlaskApp/FlaskApp/uploads"

ALLOWED_EXTENSIONS = set(["txt", "pdf", "png", "jpg", "jpeg", "gif"])

DATABASE = "/var/www/FlaskApp/FlaskApp/users/users.db"

app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("Please login.")
            return redirect(url_for('login'))

# Hi Jon, I'm just hacking in your system. I've updated your app with two functions: register and login.
# You should be able to just call these functions whenever you need to login or register. GET the username, password, etc.
# then just pass in the arguments into the system. I'm leaving this last step to you!

def register(username,password,email):
    with lite.connect("/var/www/FlaskApp/FlaskApp/users/users.db") as conn:
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS user_log(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT,password TEXT,email TEXT)')
        test = c.execute("SELECT * FROM user_log WHERE username= ('{0}')".format((thwart(username))))
        if test == True:
            return False
        else:
            c.execute("INSERT INTO user_log (username,password,email) VALUES (?,?,?)",(thwart(username),thwart(password),thwart(email)))
            conn.commit()
            return True
    return

def login(username,password):
    try:
        with lite.connect("/var/www/FlaskApp/FlaskApp/users/users.db") as conn:
            c = conn.cursor()
            data = c.execute("SELECT * FROM user_log WHERE username = ('{0}')".format(thwart(username)))
            data = c.fetchone()[2]
            if sha256_crypt.verify(password, data):
                session['logged_in'] = True
                session['username'] = username
                conn.commit()
                return True
            else:
                return False
    except:
        return False
    return

APP_CONTENT = Content()

APP_CONTENT = {
    "Home":[["Welcome", "/welcome/","Welcome to my awesome app!", "WideEyes.jpg"],
           ["Background", "/background/", "Learn more about the app here!"],
           ["Messages", "/messages/", "Your user messages are waiting..."],],
    "Profile":[["User Profile", "/profile/", "Edit your profile here!", "WideEyes.jpg"],
              ["Settings", "/settings/", "App Settins, no biggie."],
              ["Terms of Sercive", "/tos/", "The legal stuff."],],
    "Messages":[["Messsages", "/messages/", "Your user messages are waiting...", "WideEyes.jpg"],
               ["Alerts", "/alerts/", "!!Urgent Alerts!!"],],
    "Contact":[["Contact", "/contact/", "Contact us for support.", "WideEyes.jpg"],],
}


@app.route("/", methods=["GET", "POST"])
def index():
    error = ""
    try:
        #c, conn = connection()
        con = lite.connect(DATABASE)
        c = con.cursor()
        if request.method == "POST":
            
            data = c.execute("SELECT * FROM users WHERE username (username) VALUES (?)",(thwart(request.form['username'])))

            #data = c.execute("SELECT * FROM users WHERE username = ('{0}')".format(thwart(request.form['username'])))
            
            data = c.fetchone()[2]
            con.commit()
            c.close()
            if sha256_crypt.varify(request.form["password"],data):
                session['logged_in'] = True
                session['username'] = request.form['username']
                
                flash("You are now logged in "+session['username']+"!")
                return redirect(url_for("/dashboard/"))
            else:
                error = "Invalid credentials, try again."
                
        return render_template("main.html", error = error)
    except Exception as e:
        flash(e)
        error = "Invalid credentials, try again."
        return render_template("main.html", error = error)

@login_required
@app.route("/dashboard/")
def dashboard():
    try:
        return render_template("dashboard.html", APP_CONTENT = APP_CONTENT)
    except Exception as e:
        return render_template("500.html", error = e)
    
@app.route("/login/", methods=["GET", "POST"])
def login():
    error = ""
    try:
        #c, conn = connection()
        con = lite.connect(DATABASE)
        c = con.cursor()
        if request.method == "POST":
            
            data = c.execute("SELECT * FROM users WHERE (username) VALUES (?)",(thwart(request.form['username'])))

            #data = c.execute("SELECT * FROM users WHERE username = ('{0}')".format(thwart(request.form['username'])))
            
            data = c.fetchone()[2]
            #con.commit()
            c.close()
            if sha256_crypt.varify(request.form["password"],data):
                session['logged_in'] = True
                session['username'] = request.form['username']
                
                flash("You are now logged in "+session['username']+"!")
                return redirect(url_for("/dashboard/"))
            else:
                error = "Invalid credentials, try again."
                
        return render_template("login.html", error = error)
    except Exception as e:
        flash(e)
        error = "Invalid credentials, try again."
        return render_template("login.html", error = error)  
    
@login_required
@app.route("/logout/")
def logout():
    session.clear()
    flash("You have been logged out!")
    gc.collect()
    return redirect(url_for('index'))
    
class RegistrationForm(Form):
    username = TextField("Username", [validators.Length(min=4, max=20)])
    email = TextField("Email Address", [validators.Length(min=6, max=50)])
    password = PasswordField("New Password", [validators.Required(),
                                             validators.EqualTo('confirm',
                                             message="Passwords must match")])
    confirm = PasswordField("Repeat Password")
    accept_tos = BooleanField("I accept the Terms of Service and Privacy Notice", [validators.Required()])

@app.route('/register/', methods=["GET", "POST"])
def register():
    #c, conn = connection() #if it runs, it will post a string
    try:
        form = RegistrationForm(request.form)
        con = lite.connect(DATABASE)
        c = con.cursor()
        if request.method == "POST" and form.validate():
            username = form.username.data
            email = form.email.data
            password = sha256_crypt.encrypt((str(form.password.data)))
            
            #c, conn = connection() # if it runs, it will post a string
            
            c.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT, email TEXT, settings TEXT, tracking TEXT, rank INT)")
            x = c.execute("SELECT * FROM users WHERE username = (?)",(thwart(username)))

            #x = c.execute("SELECT * FROM users WHERE username = ('{0}')".format((thwart(username))))
            
            if int(x) > 0:
                flash("That username is already taken, please choose another.")
                return render_template("register.html", form = form)
            else:
                c.execute("INSERT INTO users (username,password,email,tracking) VALUES (?,?,?,?)",(username, password, email, "/dashboard/"))
                #c.execute("INSERT INTO users (username,password,email,tracking) VALUES ('{0}', '{1}', '{2}', '{3}')".format(thwart(username), thwart(password), thwart(email), thwart("/dashboard/")))
                
                con.commit()
                c.close()
                #conn.commit()
                flash("Thanks for registering, "+username+"!")
                #conn.close()
                gc.collect()
                
                session['logged_in'] = True
                session['username'] = username
                      
                return redirect(url_for('dashboard'))
            con.commit()
            c.close()
        return render_template("register.html", form = form)
            
    except Exception as e:
            return(str(e)) # remember to remove: for debugging only!

@app.route('/digit/')
def digit():
    try:
        source = requests.get('https://bulletins.psu.edu/undergraduate/colleges/behrend/digital-media-arts-technology-ba/#programrequirementstext').text 
            #using requests to grab text from website

        soup = BeautifulSoup(source, 'lxml') 
            #assigning soup to BeautifulSoup, which is being assigned to the source variable and lxml parcer.

            # just making a list to save your course codes
        course_list = []

        for td in soup.find_all('td', class_='codecol')[:42]: 
            #For loop that looks over the page and takes all of the <td> tags with the "codecol" tag. Stopping the loop after 42 iterations is necessary to prevent loop from attempting to scrap data from other parts of the site.

            coursecode = td.a.text 
                #assigning cousecode as a variable and giving it a path to follow. The added ".text" makes sure it only grabs the text in the <a> tag.
            course_list.append(coursecode.split())
            print(coursecode)
                #prints coursecode and displays them.
        
        output = course_list
        return render_template("digit.html", output = output)
    except Exception as e:
        return render_template("500.html", error = e)

@app.route('/uploads/', methods=["GET", "POST"])
#@login_required
def upload_file():
    try:
        if request.method == "POST":
            if "file" not in request.files:
                flash("No file part")
                return redirect(request.url)
            file = request.files["file"]
            
            if file.filename =="":
                flash("No selected file")
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                flash("File "+ str(filename) +" upload successful!")
                return render_template('uploads.html', filename = filename)
        return render_template('uploads.html')    
            
    except Exception as e:
        return str(e) # remove for production on all of these exceptions
    
@app.route('/welcome/')
def welcome_to_jinja():
    try:
        #This is where all of the python goes!
        def my_function():
            output = ["Digit 400 is good", "Python, Java, php, SQL, C++","<p><strong>hello world!</strong></p>", 42, "42"]
            return output
        
        output = my_function()
        
        return render_template("templating_demo.html", output = output)
    except Exception as e:
        return str(e)

@app.route("/download/")
#@login_required
def download():
    try:
        return send_file('/var/www/FlaskApp/FlaskApp/uploads/LeavesEdited.jpg', attachment_filename="LeavesEdited.jpg")
    except Exception as e:
        return str(e)
    
## Sitemap        
@app.route('/sitemap.xml', methods=["GET"])
def sitemap():
    try:
        pages = []
        week = (datetime.now() - timedelta(days = 7)).date().isoformat()
        for rule in app.url_map.iter_rules():
            if "GET" in rule.methods and len(rule.arguments) ==0:
                pages.append(["http://68.183.30.133"+str(rule.rule), week])
            
        sitemap_xml = render_template('sitemap_template.xml', pages = pages)
        response = make_response(sitemap_xml)
        response.headers["Content-Type"] = "application/xml"
        return response
    except Exception as e:
        return(str(e))
    
@app.route("/robots.txt")
def robots():
    return("User-agents: \nDisallow: /login \nDisallow: /register")
        
## Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")

@app.errorhandler(405)
def method_not_allowed(e):
    return render_template("405.html")

@app.errorhandler(500)
def server_error(e):
    return render_template("500.html", error = e)


if __name__ == "__main__":
    app.run(debug=True) #This should be turned off?False for production.
