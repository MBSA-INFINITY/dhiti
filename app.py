
import razorpay
import json
import random
from firebase import Firebase
from flask import Flask,render_template,request,redirect, url_for
from pyfcm import FCMNotification
import datetime
from collections import OrderedDict
import os


push_service = FCMNotification(api_key=os.environ['FCMAPIKEY'])

def rand_pass(len):
    pass_data = "qwertyuiopasdfgjklzxcvbnm1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ_"
    password = "".join(random.sample(pass_data, len))
    return password


true = True
false = False
null = None
app = Flask(__name__)

month_number = {"1":"January","2":"February","3":"March","4":"April","5":"May","6":"June","7":"July","8":"August","9":"September","10":"October","11":"November","12":"December"}

day_number = { "1":"Monday","2":"Tuesday","3":"Wednesday","4":"Thursday","5":"Friday","6":"Saturday","7":"Sunday" }

config = {
    "apiKey": "AIzaSyBfKoyQOgxjfusvm7qjhelsEX2n4RdmNE8",
    "authDomain": "dhiti-foundation.firebaseapp.com",
    "databaseURL": "https://dhiti-foundation-default-rtdb.firebaseio.com",
    "projectId": "dhiti-foundation",
   "storageBucket": "dhiti-foundation.appspot.com",
    "messagingSenderId": "312761775781",
    "appId": "1:312761775781:web:1165299bcf2fb9e14dff4c",
    "measurementId": "G-XG9D20WL69"
  };

firebase = Firebase(config)
auth = firebase.auth()
auth.sign_in_with_email_and_password("mbsa@gmail.com", "noonecanstopme")
db = firebase.database()
#razorpay_client = razorpay.Client(auth=("rzp_test_Y8FcD5KSf0vP0L", "hY7esVB4dayaRfLio8YnAes2"))
razorpay_client = razorpay.Client(auth=(os.environ['RZPAPIKEY'], os.environ['RZPSECRET']))

# https://www.dhitifoundation.android/aryomtech/S46iev8qgxXpkhl8al3USm0dlB92/-Mfw0sLrMOv63eJLF2CO
@app.route('/')
def app_create():
    return render_template('mainpage.html')

@app.route('/about')
def app_about():
    return render_template('about.html')

@app.route('/aryomtech/contribute/<string:variable_1>/<string:variable_2>')
def overview (variable_1,variable_2):
    global gl_push_key,gl_uid
    gl_push_key = variable_2
    gl_uid = variable_1
    image_link = db.child("fluid_Cards").child(gl_push_key).child("image_link").get().val()
    goal = db.child("fluid_Cards").child(gl_push_key).child("goal").get().val()
    return render_template('index.html',image_link=image_link,goal=goal)

@app.route('/aryomtech/<string:variable_1>/<string:variable_2>')
def aryomtech (variable_1,variable_2):
    result = db.child("fluid_Cards").child(variable_2).get().val()
    transactions = db.child("fluid_Cards").child(variable_2).child("transactions").get().val()
    dict_result = dict(result)
    if transactions == None:
        result['transactions_count'] = 0
    total_amount = 0
    try:
        contributed = result['contributed']
    except:
        contributed = 0
    total_amount+=int(contributed)
    if "transactions" in dict(result).keys():
        result['transactions_count'] = 1
        for key,val in result['transactions'].items():
                total_amount+=int(val['amount_paid'])

    custom_btns = [i for i in dict_result.keys() if i.find("custom_")!=-1]
    sub_headings = [i for i in dict_result.keys() if i.find("sub_heading_")!=-1 and dict_result[i]!="" ]
    result['custom_btns_info'] = custom_btns
    result['sub_headings_info'] = sub_headings
    result['sub_headings_count'] = len(sub_headings)
    result['callback_url'] = f"/aryomtech/contribute/{variable_1}/{variable_2}"
    result['registration_url'] = f"/register/{variable_2}"
    result['contributors_url'] = f"/aryomtech/contributors/{variable_2}"
    result['total_amount'] = str(total_amount)


    return render_template("overview.html",result = result)
@app.route("/register/<string:variable_1>",methods = ['GET','POST'])
def register(variable_1):
    if request.method == 'POST':
        data = {
            'head1':"0",
            'head2':"0",
            'head3':"0",
            'head4':"0",
            'head5':"0",
            'head6':"0",
            'head7':"0",
            'head8':"0",
            'head9':"0",
            'head10':"0",
            
        }
        temp_uid = db.generate_key()
        db.child("fluid_Cards").child(variable_1).child("registrations").child(temp_uid).set(data)
        db.child("fluid_Cards").child(variable_1).child("registrations").child(temp_uid).update(request.form)
        title =  db.child("fluid_Cards").child(variable_1).child("title").get().val()
        return render_template("reg_success.html",title = title)

@app.route('/aryomtech/contributors/<string:variable_1>')
def contributors (variable_1):
    result = db.child("fluid_Cards").child(variable_1).child("transactions").get().val()
    if result == None:
        return render_template("No_Contributors.html")

    return render_template("contributors.html",result = OrderedDict(reversed(list(result.items()))))


@app.route('/charges/<string:variable_3>/<string:variable_4>', methods=['POST'])
def app_charges(variable_3,variable_4):
    push_key = gl_push_key
    uid = gl_uid
    name = variable_3
    amount = variable_4
    payment_id = request.form['razorpay_payment_id']
    razorpay_client.payment.capture(payment_id, int(amount)*100)
    JSON_String_Payment = json.dumps(razorpay_client.payment.fetch(payment_id))
    JSON_Payment = json.loads(JSON_String_Payment)
    if JSON_Payment["status"]=="captured" and JSON_Payment["captured"]==True:
        in_push_key = db.generate_key()
        tday = datetime.date.today()
        fmt_date = day_number[str(tday.weekday()+1)]+", "+str(tday.day)+" "+month_number[str(tday.month)]+" "+str(tday.year)+", "+datetime.datetime.today().strftime("%H:%M %p")
        data={
            "amount_paid":amount,
            "key":in_push_key,
            "name":name,
            "paid_on":fmt_date,
            "uid":uid,
        }
        db.child("fluid_Cards").child(push_key).child("transactions").child(in_push_key).set(data)
        db.child("fluid_Cards").child(push_key).child("raised_by_share").child(uid).child(in_push_key).set(data)
        cur_xp = db.child("users").child(uid).child("progress").child("xp").get().val()
        db.child("users").child(uid).child("progress").child("xp").set(cur_xp+15)
        device_token = db.child("users").child(uid).child("token").get().val()
        message_title = "Referral Successfull!!"
        message_body = "We got a confirmed donation from "+name+" through your referral link. We are adding some points to your profile."
        result = push_service.notify_single_device(registration_id=device_token, message_title=message_title, message_body=message_body)
        return render_template('success.html')
    else:
        return "FAILURE"



