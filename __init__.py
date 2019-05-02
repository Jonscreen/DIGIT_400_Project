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
import pandas as pd

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
        form = RegistrationForm(request.form)
        if request.method == "POST":
            with lite.connect("/var/www/FlaskApp/FlaskApp/users/users.db") as conn:
                c = conn.cursor()

                username = form.username.data
                password = sha256_crypt.encrypt((str(form.password.data)))
                data = c.execute("SELECT * FROM user_log WHERE username = ('{0}')".format(thwart(username)))

                data = c.fetchone()[2]
                if sha256_crypt.verify(request.form["password"],data):
                    session['logged_in'] =True
                    session['username'] = request.form['username']
                    #conn.commit()
                    #c.close()
                    flash("You are now logged in "+session['username']+"!")
                    return redirect(url_for("index"))
                else:
                    error = "invalid credentials, try again."

        return render_template("login.html", error = error)
    except Exception as e:
        flash(e)
        error = "Invalid credentials, try again."
        return render_template("login.html", error = error)   

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
    
@login_required
@app.route("/logout/")
def logout():
    session.clear()
    flash("You have been logged out!")
    gc.collect()
    return redirect(url_for('index'))
    
class RegistrationForm(Form):
    username = TextField("Username", [validators.Length(min=3, max=20)])
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
        if request.method == "POST" and form.validate():
            with lite.connect("/var/www/FlaskApp/FlaskApp/users/users.db") as conn:
                c = conn.cursor()

                username = form.username.data
                email = form.email.data
                password = sha256_crypt.encrypt((str(form.password.data)))

                    #c, conn = connection() # if it runs, it will post a string

                c.execute('CREATE TABLE IF NOT EXISTS user_log(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT,password TEXT,email TEXT)')
                test = c.execute("SELECT * FROM user_log WHERE username= ('{0}')".format((thwart(username))))

                    #x = c.execute("SELECT * FROM users WHERE username = ('{0}')".format((thwart(username))))

                if test == True:
                    flash("That username is already taken, please choose another.")
                    return render_template("register.html", form = form)
                else:
                    c.execute("INSERT INTO user_log (username,password,email) VALUES (?,?,?)",(thwart(username),thwart(password),thwart(email)))
                        #c.execute("INSERT INTO users (username,password,email,tracking) VALUES ('{0}', '{1}', '{2}', '{3}')".format(thwart(username), thwart(password), thwart(email), thwart("/dashboard/")))

                    conn.commit()
                    c.close()
                        #conn.commit()
                    flash("Thanks for registering, "+username+"!")
                        #conn.close()
                    gc.collect()

                    session['logged_in'] = True
                    session['username'] = username

                    return redirect(url_for('dashboard'))
        return render_template("register.html", form = form)
            
    except Exception as e:
            return(str(e)) # remember to remove: for debugging only!
###START MAJORS  

##SCIENCE MAJORS
@app.route('/bio/')
def bio():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/biocourses.csv')
        return render_template("bio.html", table = [df.to_html(classes='bio')])
    except Exception as e:
        return render_template("500.html", error = e)

@app.route('/chem/')
def chem():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/chemcourses.csv')
        return render_template("chem.html", table = [df.to_html(classes='chem')])
    except Exception as e:
        return render_template("500.html", error = e)

@app.route('/ensci/')
def ensci():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/enviroscicourses.csv')
        return render_template("ensci.html", table = [df.to_html(classes='ensci')])
    except Exception as e:
        return render_template("500.html", error = e)

@app.route('/math/')
def math():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/mathcourses.csv')
        return render_template("math.html", table = [df.to_html(classes='math')])
    except Exception as e:
        return render_template("500.html", error = e)

@app.route('/phys/')
def phys():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/physicscourses.csv')
        return render_template("phys.html", table = [df.to_html(classes='phys')])
    except Exception as e:
        return render_template("500.html", error = e)
    
@app.route('/sci/')
def sci():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/scicourses.csv')
        return render_template("sci.html", table = [df.to_html(classes='sci')])
    except Exception as e:
        return render_template("500.html", error = e)
    
@app.route('/seced/')
def seced():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/secedcourses.csv')
        return render_template("seced.html", table = [df.to_html(classes='seced')])
    except Exception as e:
        return render_template("500.html", error = e)
    
##H&SS MAJORS

@app.route('/artsa/')
def artsa():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/aacourses.csv')
        return render_template("artsa.html", table = [df.to_html(classes='artsa')])
    except Exception as e:
        return render_template("500.html", error = e)
    
@app.route('/comm/')
def comm():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/commcourses.csv')
        return render_template("comm.html", table = [df.to_html(classes='comm')])
    except Exception as e:
        return render_template("500.html", error = e)
    
@app.route('/cw/')
def cw():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/cwcourses.csv')
        return render_template("cw.html", table = [df.to_html(classes='cw')])
    except Exception as e:
        return render_template("500.html", error = e)

@app.route('/digit/')
def digit():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/digitcourses.csv')
        return render_template("digit.html", table = [df.to_html(classes='digit')])
    except Exception as e:
        return render_template("500.html", error = e)
    
@app.route('/engl/')
def engl():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/englcourses.csv')
        return render_template("engl.html", table = [df.to_html(classes='engl')])
    except Exception as e:
        return render_template("500.html", error = e)
    
@app.route('/hist/')
def hist():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/histcourses.csv')
        return render_template("hist.html", table = [df.to_html(classes='hist')])
    except Exception as e:
        return render_template("500.html", error = e)
    
@app.route('/plsc/')
def plsc():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/plsccourses.csv')
        return render_template("plsc.html", table = [df.to_html(classes='plsc')])
    except Exception as e:
        return render_template("500.html", error = e)
    

@app.route('/psychba/')
def psychba():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/psychbacourses.csv')
        return render_template("psychba.html", table = [df.to_html(classes='psychba')])
    except Exception as e:
        return render_template("500.html", error = e)

@app.route('/psychbs/')
def psychbs():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/psychbscourses.csv')
        return render_template("psychbs.html", table = [df.to_html(classes='psychbs')])
    except Exception as e:
        return render_template("500.html", error = e)
    
##ENGINEERING MAJORS

@app.route('/compeng/')
def compeng():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/compengcourses.csv')
        return render_template("compeng.html", table = [df.to_html(classes='compeng')])
    except Exception as e:
        return render_template("500.html", error = e)
    
@app.route('/compsci/')
def compsci():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/compscicourses.csv')
        return render_template("compsci.html", table = [df.to_html(classes='compsci')])
    except Exception as e:
        return render_template("500.html", error = e)
    
@app.route('/ecet/')
def ecet():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/ecetcourses.csv')
        return render_template("ecet.html", table = [df.to_html(classes='ecet')])
    except Exception as e:
        return render_template("500.html", error = e)
    
@app.route('/elec/')
def elec():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/eleccourses.csv')
        return render_template("elec.html", table = [df.to_html(classes='elec')])
    except Exception as e:
        return render_template("500.html", error = e)
    
@app.route('/indust/')
def indust():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/industcourses.csv')
        return render_template("indust.html", table = [df.to_html(classes='indust')])
    except Exception as e:
        return render_template("500.html", error = e)
    
@app.route('/interd/')
def interd():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/interdcourses.csv')
        return render_template("interd.html", table = [df.to_html(classes='interd')])
    except Exception as e:
        return render_template("500.html", error = e)
    
@app.route('/mecheng/')
def mecheng():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/mechengcourses.csv')
        return render_template("mecheng.html", table = [df.to_html(classes='mecheng')])
    except Exception as e:
        return render_template("500.html", error = e)
    
@app.route('/mechengT/')
def mechengT():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/mechengTcourses.csv')
        return render_template("mechengT.html", table = [df.to_html(classes='mechengT')])
    except Exception as e:
        return render_template("500.html", error = e)
    
@app.route('/plastic/')
def plastic():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/plasticcourses.csv')
        return render_template("plastic.html", table = [df.to_html(classes='plastic')])
    except Exception as e:
        return render_template("500.html", error = e)
    
@app.route('/softeng/')
def softeng():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/softengcourses.csv')
        return render_template("softeng.html", table = [df.to_html(classes='softeng')])
    except Exception as e:
        return render_template("500.html", error = e)

##BUSINESS MAJORS
@app.route('/acctg/')
def acctg():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/acctcourses.csv')
        return render_template("acctg.html", table = [df.to_html(classes='acctg')])
    except Exception as e:
        return render_template("500.html", error = e)
    
@app.route('/busecon/')
def busecon():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/buseconcourses.csv')
        return render_template("busecon.html", table = [df.to_html(classes='busecon')])
    except Exception as e:
        return render_template("500.html", error = e)
    
@app.route('/econ/')
def econ():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/econcourses.csv')
        return render_template("econ.html", table = [df.to_html(classes='econ')])
    except Exception as e:
        return render_template("500.html", error = e)
    
@app.route('/finance/')
def finance():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/financecourses.csv')
        return render_template("finance.html", table = [df.to_html(classes='finance')])
    except Exception as e:
        return render_template("500.html", error = e)
    
@app.route('/intbus/')
def intbus():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/intbuscourses.csv')
        return render_template("intbus.html", table = [df.to_html(classes='intbus')])
    except Exception as e:
        return render_template("500.html", error = e)
    
@app.route('/mis/')
def mis():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/miscourses.csv')
        return render_template("mis.html", table = [df.to_html(classes='mis')])
    except Exception as e:
        return render_template("500.html", error = e)
    
@app.route('/mark/')
def mark():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/markcourses.csv')
        return render_template("mark.html", table = [df.to_html(classes='mark')])
    except Exception as e:
        return render_template("500.html", error = e)
    
@app.route('/pnsm/')
def pnsm():
    try:
        df = pd.read_csv('/var/www/FlaskApp/FlaskApp/templates/pnscourses.csv')
        return render_template("pnsm.html", table = [df.to_html(classes='pnsm')])
    except Exception as e:
        return render_template("500.html", error = e)
###END MAJORS  

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
    
@app.route('/about/')
def about():
    try:
        return render_template("about.html")
    except Exception as e:
        return render_template("500.html", error = e)
    
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
