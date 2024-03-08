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
    # 如果URL为空，则不执行下载，并返回None或默认图片路径
    if not image_url:
        print("No image URL provided for downloading.")
        return None  # 或者返回默认图片路径，例如 'path/to/default/image.png'
    
    # 确保存储图片的目录存在
    os.makedirs(IMAGE_DIR, exist_ok=True)
    
    # 根据scientific name和image_type构造图片文件名
    valid_name = re.sub(r'[^\w\-_\.]', '_', scientific_name)  # 移除不合法的文件名字符
    suffix_map = {
        "primary": "primaryimg",
        "img1": "img1",
        "img2": "img2",
        "img3": "img3"
    }
    suffix = suffix_map.get(image_type, "unknown")
    extension = image_url.rsplit('.', 1)[-1]  # 从URL获取文件扩展名
    image_name = f"{valid_name}_{suffix}.{extension}"
    image_path = os.path.join(IMAGE_DIR, image_name).replace("\\", "/")
    
    # 检查图片是否已经存在
    if os.path.exists(image_path):
        print(f"Image already exists: {image_path}")
        return image_path  # 如果图片已存在，直接返回路径
    
    # 尝试下载图片
    try:
        response = requests.get(image_url)
        response.raise_for_status()  # 确保请求成功
        with open(image_path, 'wb') as file:
            file.write(response.content)
        print(f"Image downloaded: {image_path}")
    except requests.RequestException as e:
        print(f"Error downloading {image_url}: {e}")
        image_path = None  # 或者设置为默认图片路径，例如 'path/to/default/image.png'
    
    # 更新数据库中的图片路径
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

        # 格式化科学名称以用于文件名
        formatted_sci_name = re.sub(r'[^\w\-_\.]', '_', scientific_name)

        # 初始化路径列表
        image_paths = {'uploadMainImg': None, 'uploadImg1': None, 'uploadImg2': None, 'uploadImg3': None}

        # 处理上传的图片
        for image_field in ['uploadMainImg', 'uploadImg1', 'uploadImg2', 'uploadImg3']:
            file = request.files[image_field]
            if file and allowed_file(file.filename):
                # 获取文件扩展名
                extension = file.filename.rsplit('.', 1)[1].lower()
                # 根据字段名称确定文件名
                if image_field == 'uploadMainImg':
                    filename = f"{formatted_sci_name}_primaryimg.{extension}"
                else:
                    suffix = image_field[-1]  # 获取最后一个字符，即数字
                    filename = f"{formatted_sci_name}_img{suffix}.{extension}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                # 保存文件
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
    #Setting use dictionary true
    dbconn = connection.cursor(dictionary=True)
    return dbconn


@app.route('/')
def index():
    """
    Redirect to the login page if the user is not logged in,
    otherwise redirect to the user's home page.
    """
    # 检查用户是否已经登录，这里假设你在登录后会设置 session['loggedin']
    if 'loggedin' in session:
        # 根据用户的角色重定向到不同的首页
        if session['role'] == 'Staff':
            return redirect(url_for('staff'))
        elif session['role'] == 'Administration':
            return redirect(url_for('staff'))
        else:
            return redirect(url_for('gardner_user'))
    else:
        # 如果用户未登录，重定向到登录页面
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
                    return redirect(url_for('staff'))
                elif account['role']=="Administration":
                    return redirect(url_for('staff'))
                else:
                     return redirect(url_for('gardner_user'))
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
            cursor.execute('INSERT INTO secureaccount VALUES (NULL, %s, %s, %s)', (username, hashed, email,))
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
    cursor.execute('SELECT `id`, `common name`, `weed type`, `primary image`, `scientific name`, `description`, `impacts`, `control methods`, `image1`, `image2`, `image3` FROM weed_guide')
    weeds = cursor.fetchall()
    
    # 对每个杂草条目，检查图片是否存在，如果存在则尝试下载并更新图片路径
    for weed in weeds:
        # 确保传递weed['id']给download_image函数
        # 对于每个图像，检查URL是否为空
        if weed['primary image']:
            weed['primary image'] = download_image(weed['primary image'], weed['scientific name'], "primary", weed['id'])
        else:
            weed['primary image'] = None  # 或设置为默认图片路径
        
        if weed['image1']:
            weed['image1'] = download_image(weed['image1'], weed['scientific name'], "img1", weed['id'])
        else:
            weed['image1'] = None  # 或设置为默认图片路径
        
        if weed['image2']:
            weed['image2'] = download_image(weed['image2'], weed['scientific name'], "img2", weed['id'])
        else:
            weed['image2'] = None  # 或设置为默认图片路径
        
        if weed['image3']:
            weed['image3'] = download_image(weed['image3'], weed['scientific name'], "img3", weed['id'])
        else:
            weed['image3'] = None  # 或设置为默认图片路径
    
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
    
    # 对每个杂草条目，检查图片是否存在，如果存在则尝试下载并更新图片路径
    for weed in weeds:
        # 确保传递weed['id']给download_image函数
        # 对于每个图像，检查URL是否为空
        if weed['primary image']:
            weed['primary image'] = download_image(weed['primary image'], weed['scientific name'], "primary", weed['id'])
        else:
            weed['primary image'] = weed['prImgLocalPath']  # 或设置为默认图片路径
        
        if weed['image1']:
            weed['image1'] = download_image(weed['image1'], weed['scientific name'], "img1", weed['id'])
        else:
            weed['image1'] = weed['img1LocalPath']  # 或设置为默认图片路径
        
        if weed['image2']:
            weed['image2'] = download_image(weed['image2'], weed['scientific name'], "img2", weed['id'])
        else:
            weed['image2'] = weed['img2LocalPath']  # 或设置为默认图片路径
        
        if weed['image3']:
            weed['image3'] = download_image(weed['image3'], weed['scientific name'], "img3", weed['id'])
        else:
            weed['image3'] = weed['img2LocalPath']  # 或设置为默认图片路径
    
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

        # 检查两次输入的密码是否一致（尽管前端已做校验，后端校验增加安全性）
        if new_password != confirm_password:
            return "Passwords do not match.", 400  # 或者重定向回原页面，显示错误信息

        # 密码哈希
        hashed_password = hashing.hash_value(new_password, salt='abcd')

        # 更新数据库中的密码
        cursor = getCursor()
        cursor.execute('UPDATE secureaccount SET password = %s WHERE id = %s', (hashed_password, session['id']))
        connection.commit()

        # 登出用户，要求重新登录
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
            
            # 更新成功后重定向到个人资料页面
            return redirect(url_for('showGardnerUserProfile'))
        # role is Staff or Administrator
        else :           
            if "Phone_Number" in request.form:
                phone_number = request.form['Phone_Number']
                cursor = getCursor()
                cursor.execute('UPDATE staff_admin SET Work_Phone_number = %s WHERE SecureAccountID = %s', (phone_number, session['id']))
            
            connection.commit()
            
            # 更新成功后重定向到个人资料页面
            return redirect(url_for('ShowPersonalProfile'))
    else:
        # 如果用户未登录，重定向到登录页面
        return redirect(url_for('login'))

# ! this will be the Gardner Manage Profile add page
@app.route('/Staff/ManageGardenersProfile/add')
def add_gardner():
    return render_template('ManageGardnersAdd.html')

# ! this will be the Gardner Manage Profile add page---to submit
@app.route('/Staff/ManageGardenersProfile/add/submit', methods=['POST'])
def add_gardener_submit():
    # 从表单获取数据
    first_name = request.form.get('First_Name')
    last_name = request.form.get('Last_Name')
    username = first_name + last_name
    email = request.form.get('Email')
    address = request.form.get('Address')
    phone_number = request.form.get('PhoneNumber')


    hashed_password = hashing.hash_value("12345", salt='abcd')
    # 连接数据库并插入新记录
    # 注意：这里假设你已经建立了数据库连接
    # 示例：cursor.execute("INSERT INTO gardner_profile (First_Name, ...) VALUES (%s, ...)", (first_name, ...))

    today_date = datetime.now().date()
    midnight_today = datetime.combine(today_date, time())

    cursor = getCursor()

    cursor.execute("INSERT INTO secureaccount(UserName,password,email,role) VALUES (%s,%s,%s,%s)", (username,hashed_password,email,"Gardener user"))

    secure_account_id = cursor.lastrowid

    cursor.execute("INSERT INTO gardner_profile(secureaccount_id, First_Name, Last_Name, Address, Email,Phone_Number,Status,Date_Joined) VALUES (%s, %s, %s, %s, %s,%s,%s,%s)", (secure_account_id, first_name, last_name, address, email,phone_number,"Active",midnight_today))

        # 提交事务并关闭连接
    connection.commit()
    cursor.close()
    connection.close()

    # 重定向回园丁管理页面
    return redirect(url_for('ManageGardenerProfile'))



# ! this will be the Staff Manage Profile add page
@app.route('/Staff/ManageStaff/add')
def add_staff():
    return render_template('ManageStaffsAdd.html')

# ! this will be the Gardner Manage Profile add page---to submit
@app.route('/Staff/ManageStaff/add/submit', methods=['POST'])
def add_staff_submit():
    # 从表单获取数据
    first_name = request.form.get('First_Name')
    last_name = request.form.get('Last_Name')
    username = first_name + last_name
    email = request.form.get('Email')
    workphonenumber = request.form.get('WorkPhoneNumber')

    today_date = datetime.now().date()
    midnight_today = datetime.combine(today_date, time())

    position = request.form.get('Position')
    department = request.form.get('Department')

    hashed_password = hashing.hash_value("12345", salt='abcd')
    # 连接数据库并插入新记录
    # 注意：这里假设你已经建立了数据库连接
    # 示例：cursor.execute("INSERT INTO gardner_profile (First_Name, ...) VALUES (%s, ...)", (first_name, ...))


    cursor = getCursor()

    cursor.execute("INSERT INTO secureaccount(UserName,password,email,role) VALUES (%s,%s,%s,%s)", (username,hashed_password,email,"Staff"))

    secure_account_id = cursor.lastrowid

    cursor.execute("INSERT INTO staff_admin(SecureAccountID, First_Name, Last_Name, Email,Work_Phone_number,Hire_date,Position,Department,Status) VALUES (%s, %s, %s, %s,%s,%s,%s,%s,%s)", (secure_account_id, first_name, last_name, email,workphonenumber,midnight_today,position,department,"Active"))


        # 提交事务并关闭连接
    connection.commit()
    cursor.close()
    connection.close()

    # 重定向回园丁管理页面
    return redirect(url_for('ManageStaffProfile'))




# ! this will be the Gardner Manage Profile delete action
@app.route('/delete-gardner/<int:gardner_id>', methods=['DELETE'])
def deleteGardner(gardner_id):
    # 连接数据库
    # 删除指定 ID 的园丁
    # 示例：
    # cursor.execute("DELETE FROM gardner_profile WHERE ID = %s", (gardner_id,))
    # conn.commit()
    
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
        secureaccount_id = result['secureaccount_id']  # 提取secureaccount_id的值

        if secureaccount_id is not None:
            # 删除 gardner_profile 表中的记录
            cursor.execute("DELETE FROM gardner_profile WHERE ID = %s", (gardner_id,))
            
            # 删除 secureaccount 表中的记录
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
        SecureAccountID = result['SecureAccountID']  # 提取secureaccount_id的值

        if SecureAccountID is not None:
            # 删除 admin_staff 表中的记录
            cursor.execute("DELETE FROM staff_admin WHERE ID = %s", (staff_id,))
            
            # 删除 secureaccount 表中的记录
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
    # 这里添加获取指定 gardner_id 的园丁信息的逻辑
    # 以及加载编辑表单页面的逻辑
    cursor = getCursor()
    cursor.execute("SELECT * FROM gardner_profile WHERE ID = %s", (gardner_id,))
    gardner = cursor.fetchone()
    return render_template('ManageGardnersEdit.html', gardner=gardner,gardner_id=gardner_id)


@app.route('/Staff/ManageStaff/edit/<int:staff_id>')
def edit_staff(staff_id):
    # 这里添加获取指定 gardner_id 的园丁信息的逻辑
    # 以及加载编辑表单页面的逻辑
    cursor = getCursor()
    cursor.execute("SELECT * FROM gardner_profile WHERE ID = %s", (staff_id,))
    staff = cursor.fetchone()
    return render_template('ManageStaffsEdit.html', staff=staff,staff_id=staff_id)



@app.route('/update-staff/<int:staff_id>', methods=['POST'])
def update_staff(staff_id):
    first_name = request.form['First_Name']
    last_name = request.form['Last_Name']
    work_phone_number = request.form['Work_Phone_Number']
    hire_date = request.form['Hire_Date']
    position = request.form['Position']
    department = request.form['Department']
    status = request.form['Status']

    cursor = getCursor()

    # Check for duplicates
    query = '''
    SELECT * FROM staff_admin
    WHERE phone_number = %s  AND ID != %s
    '''
    cursor.execute(query, (work_phone_number,staff_id,))
    duplicate = cursor.fetchone()

    if duplicate:
        # If duplicate exists, pass a message to the frontend
        message = "Duplicate record found. Please ensure the data is unique."
        return render_template('ManageStaffssEdit.html', staff_id=staff_id, message=message)
    else:
        # If no duplicate, update the gardener's profile
        update_query = '''
        UPDATE staff_admin
        SET First_Name = %s, Last_Name = %s, Work_Phone_number = %s, Hire_date = %s,Department = %s, Status = %s
        WHERE ID = %s
        '''
        cursor.execute(update_query, (first_name, last_name, work_phone_number, hire_date,department, status, staff_id))
        connection.commit()

        positionRole = "Staff"
        selectQuery = '''SELECT * FROM staff_admin WHERE Position = %s'''
        cursor.execute(selectQuery, (positionRole,))
        staffs = cursor.fetchall()
        # Show the gardner profile page with account info
        return render_template('ManageStaff.html',staffs=staffs)
       


if __name__ == '__main__':
    app.run(debug=True)