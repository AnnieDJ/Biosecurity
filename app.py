from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import session
from flask import jsonify
import re
from datetime import datetime
from datetime import time
import mysql.connector
from mysql.connector import FieldType
import connect
from flask_hashing import Hashing
import os
import requests
from werkzeug.utils import secure_filename
from flask import flash

app = Flask(__name__)
hashing = Hashing(app)  #create an instance of hashing


# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'your secret key'

# Assume pic saving dir
IMAGE_DIR = 'static/weed-images'

app.config['UPLOAD_FOLDER'] = IMAGE_DIR

dbconn = None
connection = None

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


# define a function to download iamges if we don't have
def download_image(image_url, scientific_name, image_type, weed_id):
     # If the URL is empty, do not perform the download and return None or the default image path
    if not image_url:
        print("No image URL provided for downloading.")
        return None  
    
    # Ensure the directory for storing images exists
    os.makedirs(IMAGE_DIR, exist_ok=True)
    
    # Construct the image file name based on the scientific name and image type
    valid_name = re.sub(r'[^\w\-_\.]', '_', scientific_name)  # Remove illegal file name characters
    suffix_map = {
        "primary": "primaryimg",
        "img1": "img1",
        "img2": "img2",
        "img3": "img3"
    }
    suffix = suffix_map.get(image_type, "unknown")
    extension = image_url.rsplit('.', 1)[-1]  # Get file extension from URL
    image_name = f"{valid_name}_{suffix}.{extension}"
    image_path = os.path.join(IMAGE_DIR, image_name).replace("\\", "/")
    
    # Check if the image already exists
    if os.path.exists(image_path):
        print(f"Image already exists: {image_path}")
        return image_path   # If the image already exists, directly return the path
    
    # Attempt to download the image
    try:
        response = requests.get(image_url)
        response.raise_for_status()  # Ensure the request was successful
        with open(image_path, 'wb') as file:
            file.write(response.content)
        print(f"Image downloaded: {image_path}")
    except requests.RequestException as e:
        print(f"Error downloading {image_url}: {e}")
        image_path = None  # Or set to default image path
    
     # Update the image path in the database
    field_map = {
        "primary": "prImgLocalPath",
        "img1": "img1LocalPath",
        "img2": "img2LocalPath",
        "img3": "img3LocalPath"
    }
    field_name = field_map.get(image_type)
    if field_name and image_path:
        try:
            cursor = getCursor()
            update_query = f"UPDATE weed_guide SET {field_name} = %s WHERE id = %s"
            cursor.execute(update_query, (image_path, weed_id))
            connection.commit()
        except mysql.connector.Error as err:
            print("Error updating database:", err)
    
    return image_path

# ! for upload weed edit images
@app.route('/upload_image', methods=['POST'])
def upload_image():
    weed_id = request.form['weedId']
    image_type = request.form['imageType']  # Image type
    file = request.files['image']

    if file and allowed_file(file.filename):
        cursor = getCursor()
        cursor.execute("SELECT `scientific name` FROM weed_guide WHERE id = %s", (weed_id,))
        weed = cursor.fetchone()

        if not weed:
            return jsonify({'error': 'Weed not found'}), 404

               # Initialize correctString as an empty string
        correctString = ''
        # Set the correct database field name based on the image type
        if image_type == 'primary image':
            correctString = 'primaryimg'
        elif image_type == 'image1':
            correctString = 'img1'
        elif image_type == 'image2':
            correctString = 'img2'
        elif image_type == 'image3':
            correctString = 'img3'

        scientific_name = weed['scientific name']
        filename = f"{scientific_name}_{correctString}.{file.filename.rsplit('.', 1)[1]}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename).replace("\\", "/")

        file.save(save_path)
        
         # Initialize finalString as an empty string
        finalString = ''
        # Set the correct database field name based on the image type
        if image_type == 'primary image':
            finalString = 'prImgLocalPath'
        elif image_type == 'image1':
            finalString = 'img1LocalPath'
        elif image_type == 'image2':
            finalString = 'img2LocalPath'
        elif image_type == 'image3':
            finalString = 'img3LocalPath'

        # Build update query using finalString
        if finalString:
            update_query = f"UPDATE weed_guide SET {finalString} = %s WHERE id = %s"
            cursor.execute(update_query, (os.path.join('static/weed-images', filename).replace("\\", "/"), weed_id))
            connection.commit()

            return jsonify({'success': 'Image upload success!'}), 200
        else:
            return jsonify({'error': 'Invalid image type provided'}), 400
    else:
        return jsonify({'error': 'Invalid file type or no file uploaded'}), 400



# check if file category is Images   
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/Staff/ManageWeed/AddWeed/submit', methods=['POST'])
def add_weed_submit():
    if request.method == 'POST':
        common_name = request.form['common_name']
        scientific_name = request.form['scientific_name']
        weed_type = request.form['weed_type']
        description = request.form['description']
        impacts = request.form['impacts']
        control_methods = request.form['control_methods']

      # Format the scientific name for use in filenames
        formatted_sci_name = re.sub(r'[^\w\-_\.]', '_', scientific_name)

         # Initialize a list for paths
        image_paths = {'uploadMainImg': None, 'uploadImg1': None, 'uploadImg2': None, 'uploadImg3': None}

        # Handle uploaded images
        for image_field in ['uploadMainImg', 'uploadImg1', 'uploadImg2', 'uploadImg3']:
            file = request.files[image_field]
            if file and allowed_file(file.filename):
                # Get file extension
                extension = file.filename.rsplit('.', 1)[1].lower()
                # Determine filename based on field name
                if image_field == 'uploadMainImg':
                    filename = f"{formatted_sci_name}_primaryimg.{extension}"
                else:
                    suffix = image_field[-1]   # Get the last character, i.e., the number
                    filename = f"{formatted_sci_name}_img{suffix}.{extension}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                # Save the file
                file.save(file_path)
                image_paths[image_field] = file_path.replace("\\", "/")

        cursor = getCursor()
        cursor.execute('''INSERT INTO weed_guide (`common name`, `scientific name`, `weed type`, `description`, `impacts`, `control methods`, `prImgLocalPath`, `img1LocalPath`, `img2LocalPath`, `img3LocalPath`)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                       (common_name, scientific_name, weed_type, description, impacts, control_methods, image_paths['uploadMainImg'], image_paths['uploadImg1'], image_paths['uploadImg2'], image_paths['uploadImg3']))
        connection.commit()

        return redirect(url_for('ManageWeed'))



def getCursor():
    global dbconn
    global connection
    connection = mysql.connector.connect(user=connect.dbuser, \
    password=connect.dbpass, host=connect.dbhost, auth_plugin='mysql_native_password ',\
    database=connect.dbname, autocommit=True)
     # Set use dictionary true
    dbconn = connection.cursor(dictionary=True)
    return dbconn


@app.route('/')
def index():
    """
    Redirect to the login page if the user is not logged in,
    otherwise redirect to the user's home page.
    """
    # Check if the user is already logged in, assuming session['loggedin'] is set upon login
    if 'loggedin' in session:
        # Redirect to different home pages based on the user's role
        if session['role'] == 'Staff':
            return redirect(url_for('staff'))
        elif session['role'] == 'Administration':
            return redirect(url_for('staff'))
        else:
            return redirect(url_for('gardner_user'))
    else:
        # If the user is not logged in, redirect to the login page
        return redirect(url_for('login'))



# http://localhost:5000/login/ - this will be the login page, we need to use both GET and POST requests
@app.route('/login/', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # UserEmail for looking up data
    userEmail = ''

    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        user_password = request.form['password']
        # Check if account exists using MySQL
        cursor = getCursor()
        cursor.execute('SELECT * FROM secureaccount WHERE Username = %s', (username,))

        # Fetch one record and return result
        account = cursor.fetchone()
        if account is not None:
            password = account['password']
            if hashing.check_value(password, user_password, salt='abcd'):
            # If account exists in accounts table 
            # Create session data, we can access this data in other routes
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                session['role']=account['role']
                session['email']=account['email']
                # Redirect to home page
                if account['role']=="Staff":
                    cursor.execute('SELECT * FROM staff_admin WHERE SecureAccountID = %s', (account['id'],))
                    staffinfo = cursor.fetchone()
                    if staffinfo['Status'] == 'Active':
                        return redirect(url_for('staff'))
                    else:
                        flash(f'Account {account["username"]} is not active,please contact your administrator!')
                        return render_template('login.html')
                elif account['role']=="Administration":
                    cursor.execute('SELECT * FROM staff_admin WHERE SecureAccountID = %s', (account['id'],))
                    gardnerinfo = cursor.fetchone()
                    if gardnerinfo['Status'] == 'Active':
                        return redirect(url_for('staff'))
                    else:
                        flash(f'Account {account["username"]} is not active,please contact your administrator!')
                        return render_template('login.html')
                else:
                    cursor.execute('SELECT * FROM gardner_profile WHERE secureaccount_id = %s', (account['id'],))
                    gardnerinfo = cursor.fetchone()
                    if gardnerinfo['Status'] == 'Active':
                        return redirect(url_for('gardner_user'))
                    else:
                        flash(f'Account {account["username"]} is not active,please contact your administrator!')
                        return render_template('login.html')
            else:
                #password incorrect
                msg = 'Incorrect password!'
        else:
            # Account doesnt exist or username incorrect
            msg = 'Incorrect username'
    # Show the login form with message (if any)
    return render_template('login.html', msg=msg)


# http://localhost:5000/logout - this will be the logout page
@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   session.pop('role', None)
   session.pop('email', None)
    
   # Redirect to login page
   return redirect(url_for('login'))




# http://localhost:5000/register - this will be the registration page, we need to use both GET and POST requests
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        # Check if account exists using MySQL
        cursor = getCursor()
        cursor.execute('SELECT * FROM secureaccount WHERE username = %s', (username,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            hashed = hashing.hash_value(password, salt='abcd')
            cursor.execute('INSERT INTO secureaccount(UserName,password,email,role) VALUES ( %s, %s, %s,%s)', (username, hashed, email,'Gardener user'))

            secureaccount_id = cursor.lastrowid

            today_date = datetime.now().date()
            midnight_today = datetime.combine(today_date, time())
            
            cursor.execute('INSERT INTO gardner_profile(secureaccount_id,First_Name,Last_Name,Email,Date_Joined,Status) VALUES (%s,%s,%s,%s,%s,%s)', (secureaccount_id, username,username, email,midnight_today, 'Active'))
            connection.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)

# http://localhost:5000/home - this will be the home page, only accessible for loggedin users
@app.route('/home')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('home.html', username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

# http://localhost:5000/profile - this will be the profile page, only accessible for loggedin users
@app.route('/profile')
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = getCursor()
        cursor.execute('SELECT * FROM secureaccount WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('profile.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


# http://localhost:5000/profile - this will be the profile page, only accessible for loggedin users
@app.route('/login/Weedlist')
def weedList():
    # Check if user is loggedin
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = getCursor()
        cursor.execute('SELECT * FROM secureaccount WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('profile.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


# http://localhost:5000/GardnerUser - this will be the GardnerUser page
@app.route('/GardnerUser/')
def gardner_user():
        return render_template('GardnerUser.html')



# http://localhost:5000/GardnerUser/Profile - this will be the GardnerUser Profile page
@app.route('/GardnerUser/Profile')
def showGardnerUserProfile():
        cursor = getCursor()
        cursor.execute('SELECT * FROM gardner_profile WHERE secureaccount_id = %s', (session['id'],))
        account = cursor.fetchone()
        # Show the gardner profile page with account info
        return render_template('GardnerUserProfile.html',account=account)


# http://localhost:5000/GardnerUser/Weedlist - this will be the GardnerUser Weedlist page
@app.route('/GardnerUser/Weedlist')
def showWeedlist():
    cursor = getCursor()
    cursor.execute('SELECT `id`, `common name`, `weed type`, `primary image`, `scientific name`, `description`, `impacts`, `control methods`, `image1`, `image2`, `image3` ,`prImgLocalPath`,`img1LocalPath`,`img2LocalPath`,`img3LocalPath`FROM weed_guide')
    weeds = cursor.fetchall()
    
# For each weed entry, check if the image exists. If it does, attempt to download and update the image path.
    for weed in weeds:
    # Ensure the weed['id'] is passed to the download_image function
    # For each image, check if the URL is not empty
        if weed['primary image']:
            weed['primary image'] = download_image(weed['primary image'], weed['scientific name'], "primary", weed['id'])
        else:
            weed['primary image'] = weed['prImgLocalPath']  # Or set to a default image path
        
        if weed['image1']:
            weed['image1'] = download_image(weed['image1'], weed['scientific name'], "img1", weed['id'])
        else:
            weed['image1'] = weed['img1LocalPath']  # Or set to a default image path
        
        if weed['image2']:
            weed['image2'] = download_image(weed['image2'], weed['scientific name'], "img2", weed['id'])
        else:
            weed['image2'] = weed['img2LocalPath']  # Or set to a default image path
        
        if weed['image3']:
            weed['image3'] = download_image(weed['image3'], weed['scientific name'], "img3", weed['id'])
        else:
            weed['image3'] = weed['img3LocalPath']  # Or set to a default image path
    
    return render_template('Weedlist.html', weeds=weeds)


# http://localhost:5000/GardnerUser/Weedlist/WeedDetail- this will be the GardnerUser WeedDetail page
@app.route('/GardnerUser/Weedlist/WeedDetail/<int:weed_id>')
def weed_detail(weed_id):
    cursor = getCursor()
    cursor.execute('SELECT * FROM weed_guide WHERE id = %s', (weed_id,))
    weed = cursor.fetchone()
    if weed:
        return render_template('WeedDetail.html', weed=weed)
    else:
        return 'Weed not found', 404


@app.route('/Staff/ManageWeed/EditWeed/<int:weed_id>', methods=['GET', 'POST'])
def edit_weed(weed_id):
    # Your logic here to fetch the weed details and handle form submission for editing
    
    cursor = getCursor()
    cursor.execute("SELECT * FROM weed_guide WHERE ID = %s", (weed_id,))
    weed = cursor.fetchone()
    return render_template('ManageWeedEdit.html', weed=weed,weed_id=weed_id)
    

@app.route('/delete_weed/<int:weed_id>', methods=['DELETE'])
def delete_weed(weed_id):
    cursor = getCursor()
    try:
        cursor.execute("DELETE FROM weed_guide WHERE id = %s", (weed_id,))
        connection.commit()
        return jsonify({'success': 'Weed deleted successfully'}), 200
    except mysql.connector.Error as err:
        print(f"Error deleting weed: {err}")
        return jsonify({'error': 'Failed to delete weed'}), 500


# http://localhost:5000/Staff - this will be the Staff page
@app.route('/Staff/')
def staff():
        role = session['role']
        return render_template('Staff.html',role=role)



# http://localhost:5000/Staff/PersonalProfile - this will be the Staff or Adminstrator Profile page
@app.route('/Staff/PersonalProfile')
def ShowPersonalProfile():
        cursor = getCursor()
        cursor.execute('SELECT * FROM staff_admin WHERE SecureAccountId = %s', (session['id'],))
        account = cursor.fetchone()
        # Show the gardner profile page with account info
        return render_template('StaffProfile.html',account=account)


# http://localhost:5000/Staff/GardenerProfile - this will be the All Gardeners Profile page 
@app.route('/Staff/GardenersProfile')
def ShowGardenerProfile():
        cursor = getCursor()
        query = '''SELECT * FROM gardner_profile'''
        cursor.execute(query)
        gardners = cursor.fetchall()
        # Show the gardner profile page with account info
        return render_template('AllGardners.html',gardners=gardners)


# http://localhost:5000/Staff/GardenerProfile - this will be the Gardener Manage Profile page 
@app.route('/Staff/ManageGardenersProfile')
def ManageGardenerProfile():
        cursor = getCursor()
        query = '''SELECT * FROM gardner_profile'''
        cursor.execute(query)
        gardners = cursor.fetchall()
        # Show the gardner profile page with account info
        return render_template('ManageGardners.html',gardners=gardners)




# http://localhost:5000/Staff/ManageStaffProfile - this will be the Staff or Adminstrator Manage Profile page
@app.route('/Staff/ManageStaffProfile')
def ManageStaffProfile():
        
        cursor = getCursor()
        query = '''SELECT * FROM staff_admin '''
        cursor.execute(query)
        staffs = cursor.fetchall()
        # Show the gardner profile page with account info
        return render_template('ManageStaff.html',staffs=staffs)

# ! staff/ManageWeed - this will be the Staff or Adminstrator Manage Weed page
@app.route('/Staff/ManageWeed')
def ManageWeed():
    cursor = getCursor()
    cursor.execute('SELECT `id`, `common name`, `weed type`, `primary image`, `scientific name`, `description`, `impacts`, `control methods`, `image1`, `image2`, `image3` ,`prImgLocalPath`,`img1LocalPath`,`img2LocalPath`,`img3LocalPath`FROM weed_guide')
    weeds = cursor.fetchall()
    
    # For each weed entry, check whether the image exists, and if it exists, try to download and update the image path
    for weed in weeds:
        #make sure pass weed['id'] to download_image function
        # for every image, check whether the URL is not empty
        if weed['primary image']:
            weed['primary image'] = download_image(weed['primary image'], weed['scientific name'], "primary", weed['id'])
        else:
            weed['primary image'] = weed['prImgLocalPath']  # or set to the default image path
        
        if weed['image1']:
            weed['image1'] = download_image(weed['image1'], weed['scientific name'], "img1", weed['id'])
        else:
            weed['image1'] = weed['img1LocalPath']  # or set to the default image path
        
        if weed['image2']:
            weed['image2'] = download_image(weed['image2'], weed['scientific name'], "img2", weed['id'])
        else:
            weed['image2'] = weed['img2LocalPath']  # or set to the default image path
        
        if weed['image3']:
            weed['image3'] = download_image(weed['image3'], weed['scientific name'], "img3", weed['id'])
        else:
            weed['image3'] = weed['img2LocalPath']  # or set to the default image path
    
    return render_template('ManageWeed.html', weeds=weeds)


# ! staff/ManageWeed - this will be the Staff or Adminstrator Manage Weed  add page
@app.route('/Staff/ManageWeed/AddWeed')
def ManageWeedAdd():

    return render_template('ManageWeedAdd.html')




@app.route('/Administration/')
def administration():
        return render_template('Administration.html')


@app.route('/Administration/Profile')
def showAdministrationProfile():
        cursor = getCursor()
        cursor.execute('SELECT * FROM staff_admin WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        # Show the gardner profile page with account info
        return render_template('Administration.html',account=account)



@app.route('/changePassword', methods=['POST'])
def change_password():
    if 'loggedin' in session:
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        # check if the passwords match
        if new_password != confirm_password:
            return "Passwords do not match.", 400  
        # or relocate to the original page,show error message

        # password hashing
        hashed_password = hashing.hash_value(new_password, salt='abcd')

        # update the password in the database
        cursor = getCursor()
        cursor.execute('UPDATE secureaccount SET password = %s WHERE id = %s', (hashed_password, session['id']))
        connection.commit()

        # user logout need to redirect to login page
        return redirect(url_for('logout'))
    else:
        return redirect(url_for('login'))


@app.route('/updateProfile', methods=['POST'])
def update_profile():
    if 'loggedin' in session:
        # role is Gardener user
        if session['role'] == 'Gardener user':
            if "Address" in request.form:
                address = request.form['Address']
                cursor = getCursor()
                cursor.execute('UPDATE gardner_profile SET Address = %s WHERE secureaccount_id = %s', (address, session['id']))
            
            if "Phone_Number" in request.form:
                phone_number = request.form['Phone_Number']
                cursor = getCursor()
                cursor.execute('UPDATE gardner_profile SET Phone_Number = %s WHERE secureaccount_id = %s', (phone_number, session['id']))
            
            connection.commit()
            
            # relocate to the personal profile page after updating successfully
            flash('Profile updated successfully')
            return redirect(url_for('showGardnerUserProfile'))
        # role is Staff or Administrator
        else :           
            if "Phone_Number" in request.form:
                phone_number = request.form['Phone_Number']
                cursor = getCursor()
                cursor.execute('UPDATE staff_admin SET Work_Phone_number = %s WHERE SecureAccountID = %s', (phone_number, session['id']))
            
            connection.commit()
            
            # relocate to the personal profile page after updating successfully
            flash('Profile updated successfully')
            return redirect(url_for('ShowPersonalProfile'))
    else:
        # if user is not logged in, redirect to login page
        return redirect(url_for('login'))

# ! this will be the Gardner Manage Profile add page
@app.route('/Staff/ManageGardenersProfile/add')
def add_gardner():
    return render_template('ManageGardnersAdd.html')

# ! this will be the Gardner Manage Profile add page---to submit
@app.route('/Staff/ManageGardenersProfile/add/submit', methods=['POST'])
def add_gardener_submit():
    if 'loggedin' in session:
        if request.method == 'POST':
    # retrieve the data from the form
            first_name = request.form.get('First_Name')
            last_name = request.form.get('Last_Name')
            username = first_name + last_name
            email = request.form.get('Email')
            address = request.form.get('Address')
            phone_number = request.form.get('PhoneNumber')


            hashed_password = hashing.hash_value(request.form.get('password'), salt='abcd')


            today_date = datetime.now().date()
            midnight_today = datetime.combine(today_date, time())

            cursor = getCursor()

            cursor.execute("INSERT INTO secureaccount(UserName,password,email,role) VALUES (%s,%s,%s,%s)", (username,hashed_password,email,"Gardener user"))

            secure_account_id = cursor.lastrowid

            cursor.execute("INSERT INTO gardner_profile(secureaccount_id, First_Name, Last_Name, Address, Email,Phone_Number,Status,Date_Joined) VALUES (%s, %s, %s, %s, %s,%s,%s,%s)", (secure_account_id, first_name, last_name, address, email,phone_number,"Active",midnight_today))

                # commit the transaction and close the connection
            connection.commit()
            cursor.close()
            connection.close()

            flash('Add Gardners success!')
            # relocate to the gardner manage profile page
            return redirect(url_for('ManageGardenerProfile'))



# ! this will be the Staff Manage Profile add page
@app.route('/Staff/ManageStaff/add')
def add_staff():
    return render_template('ManageStaffsAdd.html')

# ! this will be the Gardner Manage Profile add page---to submit
@app.route('/Staff/ManageStaff/add/submit', methods=['POST'])
def add_staff_submit():
    if 'loggedin' in session:
        if request.method == 'POST':
    # retrieve the data from the form
            first_name = request.form.get('First_Name')
            last_name = request.form.get('Last_Name')
            username = first_name + last_name
            email = request.form.get('Email')
            workphonenumber = request.form.get('WorkPhoneNumber')

            today_date = datetime.now().date()
            midnight_today = datetime.combine(today_date, time())

            department = request.form.get('Department')

            hashed_password = hashing.hash_value(request.form.get('password'), salt='abcd')

            cursor = getCursor()

            cursor.execute("INSERT INTO secureaccount(UserName,password,email,role) VALUES (%s,%s,%s,%s)", (username,hashed_password,email,"Staff"))

            secure_account_id = cursor.lastrowid

            cursor.execute("INSERT INTO staff_admin(SecureAccountID, First_Name, Last_Name, Email,Work_Phone_number,Hire_date,Position,Department,Status) VALUES (%s, %s, %s, %s,%s,%s,%s,%s,%s)", (secure_account_id, first_name, last_name, email,workphonenumber,midnight_today,"Staff",department,"Active"))


                # commit the transaction and close the connection
            connection.commit()
            cursor.close()
            connection.close()

            flash('Add Staff success!')
            # relocate to the staff manage profile page
            return redirect(url_for('ManageStaffProfile'))




# ! this will be the Gardner Manage Profile delete action
@app.route('/delete-gardner/<int:gardner_id>', methods=['DELETE'])
def deleteGardner(gardner_id):

    
    result = delete_gardner_and_account(gardner_id)

    if result:
        return jsonify({'success': True}), 200
    else:
        return jsonify({'error': 'Deletion failed'}), 400



def delete_gardner_and_account(gardner_id):
    cursor = getCursor()
    cursor.execute("SELECT secureaccount_id FROM gardner_profile WHERE ID = %s", (gardner_id,))
    result = cursor.fetchone()

    if result:
        secureaccount_id = result['secureaccount_id']  

        if secureaccount_id is not None:
            
            cursor.execute("DELETE FROM gardner_profile WHERE ID = %s", (gardner_id,))
            
           
            cursor.execute("DELETE FROM secureaccount WHERE id = %s", (secureaccount_id,))
            connection.commit()

        cursor.close()
        connection.close()
        return True
    else:
        cursor.close()
        connection.close()
        return False

# ! this will be the Staff Manage Profile delete action
@app.route('/delete-staff/<int:staff_id>', methods=['DELETE'])
def deleteStaff(staff_id):

    
    result = delete_staff_and_account(staff_id)

    if result:
        return jsonify({'success': True}), 200
    else:
        return jsonify({'error': 'Deletion failed'}), 400



def delete_staff_and_account(staff_id):
    cursor = getCursor()
    cursor.execute("SELECT * FROM staff_admin WHERE ID = %s", (staff_id,))
    result = cursor.fetchone()

    if result:
        SecureAccountID = result['SecureAccountID']  

        if SecureAccountID is not None:
         
            cursor.execute("DELETE FROM staff_admin WHERE ID = %s", (staff_id,))
            
          
            cursor.execute("DELETE FROM secureaccount WHERE id = %s", (SecureAccountID,))
            connection.commit()

        cursor.close()
        connection.close()
        return True
    else:
        cursor.close()
        connection.close()
        return False

@app.route('/Staff/ManageGardenersProfile/edit/<int:gardner_id>')
def edit_gardner(gardner_id):

    cursor = getCursor()
    cursor.execute("SELECT * FROM gardner_profile WHERE ID = %s", (gardner_id,))
    gardner = cursor.fetchone()
    return render_template('ManageGardnersEdit.html', gardner=gardner,gardner_id=gardner_id)


@app.route('/Staff/ManageStaff/edit/<int:staff_id>')
def edit_staff(staff_id):

    cursor = getCursor()
    cursor.execute("SELECT * FROM staff_admin WHERE ID = %s", (staff_id,))
    staff = cursor.fetchone()
    return render_template('ManageStaffsEdit.html', staff=staff,staff_id=staff_id)


@app.route('/update_weed/<int:weed_id>', methods=['POST'])
def update_weed(weed_id):
    # retrieve the data from the form
    common_name = request.form.get('common name')
    scientific_name = request.form.get('scientific name')
    weed_type = request.form.get('weed type')
    description = request.form.get('description')
    impact = request.form.get('impact')
    control_methods = request.form.get('control methods')

 
    cursor = getCursor()

 
    sql = '''
        UPDATE weed_guide
        SET `common name` = %s, `scientific name` = %s, `weed type` = %s, 
            `description` = %s, `impacts` = %s, `control methods` = %s
        WHERE id = %s
    '''
    values = (common_name, scientific_name, weed_type, description, impact, control_methods, weed_id)

    try:
     
        cursor.execute(sql, values)
        connection.commit()
        return redirect(url_for('ManageWeed'))
    except mysql.connector.Error as err:
        print(f"Error updating weed record: {err}")
        
        return redirect(url_for('edit_weed', weed_id=weed_id, message="Failed to update weed information. Please try again."))


@app.route('/update-staff/<int:staff_id>', methods=['POST'])
def update_staff(staff_id):
    if 'loggedin' in session:
        if request.method == 'POST':
            first_name = request.form['First_Name']
            last_name = request.form['Last_Name']
            work_phone_number = request.form['Work_Phone_Number']
            hire_date = request.form['Hire_Date']
            department = request.form['Department']
            status = request.form['Status']
            newpassword_hashing = hashing.hash_value(request.form.get('password'),salt='abcd')
            cursor = getCursor()

            cursor.execute('''SELECT * FROM staff_admin WHERE ID = %s''',(staff_id,))
            result = cursor.fetchone()
            secureaccount_id = result['SecureAccountID']

            if secureaccount_id is not None:
            # Check for duplicates
                query = '''
                SELECT * FROM staff_admin
                WHERE Work_Phone_number = %s  AND ID != %s
                '''
                cursor.execute(query, (work_phone_number,staff_id,))
                duplicate = cursor.fetchone()

                if duplicate:
                    # If duplicate exists, pass a message to the frontend
                    message = "Duplicate record found. Please ensure the data is unique."
                    return render_template('ManageStaffsEdit.html', staff_id=staff_id, message=message)
                else:
                    # If no duplicate, update the gardener's profile
                    update_query = '''
                    UPDATE staff_admin
                    SET First_Name = %s, Last_Name = %s, Work_Phone_number = %s, Hire_date = %s,Department = %s, Status = %s
                    WHERE ID = %s
                    '''
                    updatepassword_query = '''UPDATE secureaccount SET password = %s WHERE ID = %s'''

                    cursor.execute(update_query, (first_name, last_name, work_phone_number, hire_date,department, status, staff_id))
                    cursor.execute(updatepassword_query, (newpassword_hashing, secureaccount_id))
                    connection.commit()

                    positionRole = "Staff"
                    selectQuery = '''SELECT * FROM staff_admin WHERE Position = %s'''
                    cursor.execute(selectQuery, (positionRole,))
                    staffs = cursor.fetchall()
                    flash('staff updated successfully')
                    # Show the gardner profile page with account info
                    return render_template('ManageStaff.html',staffs=staffs)
       

# ! Edit Gardner Profile       
@app.route('/Staff/ManageGardenersProfile/update/<int:gardner_id>', methods=['POST'])
def update_gardener(gardner_id):
    # Extracting form data
    first_name = request.form['First_Name']
    last_name = request.form['Last_Name']
    address = request.form['Address']
    phone_number = request.form['Phone_Number']
    status = request.form['Status']
    # Assuming Date_Joined is part of the form and formatted as 'YYYY-MM-DD'
    date_joined = request.form['Date_Joined']
    newpassword_hashing = hashing.hash_value(request.form.get('password'),salt='abcd')
    # Database connection and cursor
    cursor = getCursor()
    cursor.execute('''SELECT * FROM gardner_profile WHERE ID = %s''',(gardner_id,))
    result = cursor.fetchone()
    secureaccount_id = result['secureaccount_id']
    if secureaccount_id is not None:
    # Preparing the SQL query to update gardener's profile
        update_query = '''
            UPDATE gardner_profile
            SET First_Name = %s, Last_Name = %s, Address = %s, Phone_Number = %s, Status = %s, Date_Joined = %s
            WHERE ID = %s
        '''
        update_password_query = '''        UPDATE secureaccount
            SET password = %s
            WHERE ID = %s'''
        

        try:
            # Executing the update query
            cursor.execute(update_query, (first_name, last_name, address, phone_number, status, date_joined, gardner_id))
            
            cursor.execute(update_password_query, (newpassword_hashing, secureaccount_id))
            connection.commit()
            # Redirecting to the gardener profile management page or showing success message
            flash('Gardner profile updated successfully.')
            return redirect(url_for('ManageGardenerProfile'))
        except mysql.connector.Error as err:
            # Handling potential errors and redirecting back to the edit page with an error message
            print(f"Error updating gardener's profile: {err}")
            # Optional: Pass a message back to the editing page about the error
            return redirect(url_for('edit_gardner', gardner_id=gardner_id, message="Failed to update profile. Please try again."))


if __name__ == '__main__':
    app.run(debug=True)