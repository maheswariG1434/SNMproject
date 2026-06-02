from flask import Flask,request,redirect,url_for,render_template,flash,session,send_file,jsonify
from flask_session import Session 
from otp import genotp               #Any file with .py is called as "module"
from mail import sendmail
from stoken import endata,dndata
import mysql.connector
import flask_excel as excel 
from io import BytesIO
import re
mydb=mysql.connector.connect(user='flaskuser',password='password',host='localhost',db='flaskdb')
app=Flask(__name__)
excel.init_excel(app)
app.config['SESSION_TYPE'] = 'filesystem'  #Using to store files in localSystem
Session(app)   #Integration
app.secret_key='OTP0404'
@app.route('/')
def home():
    return render_template('Welcome.html')
@app.route('/Register',methods=['GET','POST'])
def Register():
    if request.method=='POST':
        username=request.form['username']
        useremail=request.form['useremail']
        userpassword=request.form['password']
        try:
            cursor=mydb.cursor()
            cursor.execute('select count(user_email) from userdata where user_email=%s',[useremail])
            count_email=cursor.fetchone() #(1)n or (0)
            cursor.close()
        except Exception as e:
            print(e)
            flash('Could not verify email')
            return redirect(url_for('Register'))
        else:
            if count_email[0]==0:
                gotp=genotp()  #'M2iN8s'
                userdata={'username':username,'useremail':useremail,'userpassword':userpassword,'serverotp':gotp}
                # apppassword='wfuw izkf plms jvfc'
                subject=f'SNM APP VERIFICATION'
                body=f'Use the OTP for verification:{gotp}'
                sendmail(to=useremail,subject=subject,body=body)
                flash('The OTP has been sent to your given mail')
                return redirect(url_for('otpverification',serverdata=endata(userdata)))
            elif count_email[0]==1:
                flash('Email already existed')
    return render_template('Register.html')
@app.route('/otpverification/<serverdata>',methods=['GET','POST'])
def otpverification(serverdata):
    try:
        de_otp=dndata(serverdata)  #It returns the deserialized userdata dictionary
    except Exception as e:
        print(e)
        flash('Could not verify otp')
        return redirect(url_for('Register'))
    else:
        if request.method=='POST':
            user_otp=request.form['otp']
            if user_otp==de_otp['serverotp']:
                cursor=mydb.cursor()  #It is Mysql Cursor creted using mysqldb connection object
                cursor.execute('insert into userdata(username,user_email,userpassword) values(%s,%s,%s)',
                [de_otp['username'],de_otp['useremail'],de_otp['userpassword']])
                mydb.commit()
                cursor.close()
                flash('Details registered successfully')
                return redirect(url_for('Login'))
            else:
                flash('OTP was wrong')
                return redirect(url_for('otpverification',serverdata=serverdata))
        return render_template('otp.html')
@app.route('/Login',methods=['GET','POST'])
def Login():
    if request.method=='POST':
        login_useremail=request.form['email']
        login_password=request.form['password']
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(user_email) from userdata where user_email=%s',[login_useremail])
            count_email=cursor.fetchone()  #(1,) or (0)
            print(count_email)
        except Exception as e:
            print(e)
            flash('could not verify user email')
            return redirect(url_for('Login'))
        else:
            if count_email[0]==1:
                cursor.execute('select userpassword from userdata where user_email=%s',[login_useremail])
                stored_password=cursor.fetchone()
                if stored_password[0]==login_password:
                    session['user']=login_useremail
                    flash('User logged in successfully')
                    return redirect(url_for('Dashboard'))
                else:
                    flash('Password was wrong')
                    return redirect(url_for('Login'))
            elif count_email[0]==0:
                flash('No email found')
                return redirect(url_for('Login'))
    return render_template('Login.html')
@app.route('/Dashbord')
def Dashboard():
    if session.get('user'):
        return render_template('Dashboard.html')
    else:
        flash('please login to view Dashbaord')
        return redirect(url_for('Login'))
@app.route('/Addnotes',methods=['GET','POST'])
def Addnotes():
    if not session.get('user'):
        flash('please login to Addnotes')
        return redirect(url_for('Login'))
    if request.method=='POST':
        title=request.form['title']
        description=request.form['description']
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from userdata where user_email=%s',[session.get('user')])
            user_id=cursor.fetchone()
            if user_id[0]:
                cursor.execute('insert into notesdata(notes_title,notes_description,userid) values(%s,%s,%s)'
                ,[title,description,user_id[0]])
                mydb.commit()
                cursor.close()
            else:
                flash('Could not fetch user details')
                return redirect(url_for('Addnotes'))
        except Exception as e:
            print(e)
            flash('Could not store notes details')
            return redirect(url_for('Addnotes'))
        else:
            flash('Notes added successfully')
            return redirect(url_for('Addnotes'))
    return render_template('Addnotes.html')
@app.route('/Viewallnotes')
def Viewallnotes():
    if not session.get('user'):
        flash('Please login first')
        return redirect(url_for('Login'))
    try:
        cursor = mydb.cursor(buffered=True)
        cursor.execute('''SELECT userid FROM userdata WHERE user_email=%s''',[session.get('user')])
        user_id = cursor.fetchone()
        if user_id:
            cursor.execute('''SELECT notesid, notes_title, notes_description, created_at FROM notesdata 
            WHERE userid=%s ORDER BY notesid DESC''',[user_id[0]])
            stored_allnotesdata = cursor.fetchall()
            cursor.close()
            return render_template('Viewallnotes.html', files_data=stored_allnotesdata)
        else:
            flash('User not found')
            return redirect(url_for('Dashboard'))
    except Exception as e:
        print(e)
        flash('Could not fetch notes details')
        return redirect(url_for('Dashboard'))
@app.route('/Viewnotes/<nid>')
def Viewnotes(nid):
    if not session.get('user'):
        flash('please login to view notes details')
        return redirect(url_for('Login'))
    try:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from userdata where user_email=%s', [session.get('user')])
        user_id=cursor.fetchone()[0] #(1) or (2)
        cursor.execute('select notesid, notes_title, notes_description, created_at from notesdata where userid=%s and notesid=%s',[user_id, nid])
        stored_notesdata=cursor.fetchone()  #it will return a single tuple like ('title1', 'description1', '2023-09-01 10:00:00')
        print(stored_notesdata)
        cursor.close()
    except Exception as e:
        print(e)
        flash('could not fetch notesdata details')
        return redirect(url_for('Dashboard'))
    else:
        return render_template('Viewnotes.html', stored_notesdata=stored_notesdata)
@app.route('/deletenotes/<nid>')
def deletenotes(nid):
    if not session.get('user'):
        flash('please login to access delete notes')
        return redirect(url_for('Login'))
    try:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from userdata where user_email=%s', [session.get('user')])
        user_id=cursor.fetchone()[0] #(1) or (2)
        cursor.execute('delete from notesdata where userid=%s and notesid=%s',[user_id,nid])
        mydb.commit()
        cursor.close()
    except Exception as e:
        print(e)
        flash('could not delete notesdata details')
        return redirect(url_for('Dashboard'))
    else:
        flash('notes deleted successfully')
        return redirect(url_for('Viewallnotes'))
@app.route('/UpdateNotes/<nid>',methods=['GET','POST'])
def UpdateNotes(nid):
    if not session.get('user'):
        flash('Please Login to access dashboard features')
        return redirect(url_for('Login'))
    try:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from userdata where user_email=%s', [session.get('user')])
        user_id=cursor.fetchone()[0] #(1) or (2)
        cursor.execute('select notesid, notes_title, notes_description, created_at from notesdata where userid=%s and notesid=%s',[user_id, nid])
        stored_notesdata=cursor.fetchone()  #it will return a single tuple like ('title1', 'description1', '2023-09-01 10:00:00')
        print(stored_notesdata)
        cursor.close()
    except Exception as e:
        print(e)
        flash('could not fetch notes details')
        return redirect(url_for('Viewallnotes'))
    else:
        if request.method=='POST':
            updated_title=request.form['title']
            updated_description=request.form['description']
            try:      
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select userid from userdata where user_email=%s',[session.get('user')])
                user_id=cursor.fetchone()
                if user_id[0]:
                    cursor.execute('update notesdata set notes_title=%s,notes_description=%s where userid=%s and notesid=%s',[updated_title,updated_description,user_id[0],nid])
                    mydb.commit()
                    cursor.close()
                else:
                    flash('Could not fetch user details')
                    return redirect(url_for('UpdateNotes',nid=nid))
            except Exception as e:
                print(e)
                flash('Could not store notes details')
                return redirect(url_for('UpdateNotes',nid=nid))
            else:
                flash('Notes updates successfully')
                return redirect(url_for('UpdateNotes',nid=nid))
        return render_template('UpdateNotes.html',stored_notesdata=stored_notesdata)
@app.route('/Getexceldata')
def Getexceldata():
    if not session.get('user'):
        flash('Please login first')
        return redirect(url_for('Login'))
    try:
        cursor = mydb.cursor(buffered=True)
        cursor.execute(
            '''
            SELECT userid
            FROM userdata
            WHERE user_email=%s
            ''',
            [session.get('user')])
        user_id = cursor.fetchone()
        if user_id:
            cursor.execute('''
                SELECT notesid, notes_title, notes_description, created_at
                FROM notesdata
                WHERE userid=%s
                ORDER BY notesid DESC
                ''',
                [user_id[0]])
            stored_allnotesdata = cursor.fetchall()
            cursor.close()
    except Exception as e:
        print(e)
        flash('Could not fetch notes details')
        return redirect(url_for('Dashboard'))
    else:
        array_data=[list(i) for i in stored_allnotesdata] #list of list
        columns=['notesid','notes_title','notes_description','created_at']
        array_data.insert(0,columns)
        return excel.make_response_from_array(array_data,'xlsx',file_name='Allnotesdata')
@app.route('/fileupload',methods=['GET','POST'])
def fileupload():
    if not session.get('user'):
        flash('please login to access dashboard features')
        return redirect(url_for('userlogin'))
    if request.method=='POST':
        user_filedata=request.files['filedata'] #accepts client file data
        # print(user_filedata)
        # print(user_filedata.read())
        # print(user_filedata.filename)
        fname=user_filedata.filename
        fdata=user_filedata.read()

        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from userdata where user_email=%s',[session.get('user')])
            user_id=cursor.fetchone()[0]
            cursor.execute('insert into filesdata(filename,filedata,userid) values(%s,%s,%s)',[fname,fdata,user_id])
            mydb.commit()
            cursor.close()
        except Exception as e:
            print(e)
            flash('Could not store file details')
            return redirect(url_for('fileupload'))
        else:
            flash('File upload successfully')
    return render_template('fileupload.html')
@app.route('/Viewallfiles')
def Viewallfiles():
    if not session.get('user'):
        flash('Please login to view all files')
        return redirect(url_for('Login'))
    try:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('SELECT userid FROM userdata WHERE user_email=%s',[session.get('user')])
        user_id=cursor.fetchone()[0]
        cursor.execute('SELECT filesid,filename,created_at from filesdata where userid=%s',[user_id])
        stored_allfilesdata=cursor.fetchall()
        mydb.commit()
        cursor.close()
    except Exception as e:
        print(e)
        flash('Could not fetch notes details') 
        return redirect(url_for('Dashboard'))
    else:
        return render_template('Viewallfiles.html',
        stored_allfilesdata=stored_allfilesdata)
@app.route('/deletefile/<fid>')
def deletefile(fid):
    if not session.get('user'):
        flash('please login to access delete notes')
        return redirect(url_for('Login'))
    try:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from userdata where user_email=%s', [session.get('user')])
        user_id=cursor.fetchone()[0] #(1) or (2)
        cursor.execute('delete from filesdata where filesid=%s and userid=%s',[fid,user_id])
        mydb.commit()
        cursor.close()
    except Exception as e:
        print(e)
        flash('could not delete filesdata details')
        return redirect(url_for('Dashboard'))
    else:
        flash('Notes deleted successfully')
        return redirect(url_for('Viewallfiles'))
@app.route('/Viewfile/<fid>')
def Viewfile(fid):
    if not session.get('user'):
        flash('pls login to view notes details')
        return redirect(url_for('Login'))
    try:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from userdata where user_email=%s',[session.get('user')])
        user_id=cursor.fetchone()[0]
        cursor.execute('''select filesid,filename,filedata,created_at from filesdata
         where userid=%s and filesid=%s''',[user_id,fid])
        stored_filedata=cursor.fetchone() #(1,'otp.py','file conent','time')
        cursor.close()
    except Exception as e:
        print(e)
        flash('Could not fetch file details')
        return redirect(url_for('Dashboard'))
    else:
        bytes_array=BytesIO(stored_filedata[2])
        return send_file(bytes_array,as_attachment=False,download_name=stored_filedata[1])
@app.route('/Downloadfile/<fid>')
def Downloadfile(fid):
    if not session.get('user'):
        flash('Please login to view all files')
        return redirect(url_for('Login'))
    try:
        cursor = mydb.cursor(buffered=True)
        cursor.execute('SELECT userid FROM userdata WHERE user_email=%s',[session.get('user')])
        user_id = cursor.fetchone()[0]
        cursor.execute('SELECT filesid,filename,filedata,created_at from filesdata where userid=%s and filesid=%s',[user_id,fid])
        stored_filedata=cursor.fetchone()
        cursor.close()
    except Exception as e:
        print(e)
        flash('Could not fetch file details')
        return redirect(url_for('Dashboard'))
    else:
        bytes_array=BytesIO(stored_filedata[2])
        return send_file(bytes_array,as_attachment=True,download_name=stored_filedata[1])
@app.route('/Searchdata',methods=['POST'])
def Searchdata():
    if not session.get('user'):
        flash('Please login to access dashboard')
        return redirect(url_for('Login'))
    try:
        user_search=request.form['search'] #''
        strg=['A-Za-z0-9']
        pattern=re.compile(f'^{strg}',re.IGNORECASE)  #In REGEX= ^ means starting letter
        if pattern.match(user_search):
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select userid from userdata where user_email=%s',[session.get('user')])
                user_id=cursor.fetchone()[0]
                cursor.execute('''select notesid,notes_title,created_at from notesdata where 
                (notesid like %s or notes_title like %s or created_at like %s 
                or notes_description like %s)and userid=%s''',
                [user_search+'%',user_search+'%',user_search+'%',user_search+'%',user_id])
                search_result=cursor.fetchall()
                cursor.close()
            except Exception as e:
                print(e)
                flash('Could not fetch search data please check')
                return redirect(url_for('Dashboard'))
            else:
                return render_template('Viewallnotes.html',files_data=search_result)
        else:
            flash('Invalid search data please check')
            return redirect(url_for('Dashboard'))
    except Exception as e:
        print(e)
        flash('could check Search data please check')
        return redirect(url_for('Dashboard'))
@app.route('/Logout')
def Logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('Login'))
    else:
        flash('Please Login to Logout')
        return redirect(url_for('Login'))
@app.route('/Forgotpassword',methods=['GET','POST'])
def Forgotpassword():
    if request.method=='POST':
        user_email=request.form['email']
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(*) from userdata where user_email=%s',[user_email])
            email_count=cursor.fetchone()
            cursor.close()
        except Exception as e:
            print(e)
            flash('Could not verify user')
            return redirect(url_for('Login'))
        else:
            if email_count[0]==1:
                subject=f'Reset link for SNM forgot password'
                body=f'''Use the given link for New Password update 
                {url_for('newpassword',user_email=endata(user_email),_external=True,)}'''
                sendmail(to=user_email,subject=subject,body=body)
                flash('Reset link has been sent to given mail')
                return redirect(url_for('Forgotpassword'))
            elif email_count[0]==0:
                flash('Email not registered please check')
                return redirect(url_for('Login'))
    return render_template('Forgotpassword.html')
@app.route('/newpassword/<user_email>',methods=['GET','PUT'])
def newpassword(user_email):
    try:
        forgot_email=dndata(user_email)
    except Exception as e:
        flash('Could not verify the email')
        return redirect(url_for('newpassword',user_email=useremail))
    else:
        if request.method=='PUT':
            npassword=request.get_json()['password']
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('Update userdata set userpassword=%s where user_email=%s',[npassword,forgot_email])
                mydb.commit()
                cursor.close()
            except Exception as e:
                print(e)
                flash('Could not update password')
                return redirect(url_for('newpassword',user_email=user_email))
            else:
                flash('password updated successfully')
                return jsonify({"message":"password updates successfully"})
        return render_template('newpassword.html',user_email=user_email)
if __name__=='__main__':
    app.run()