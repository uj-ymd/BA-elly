import requests
from bs4 import BeautifulSoup

from flask import Flask, render_template,request
from datetime import datetime

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# 判斷是在 Vercel 還是本地
if os.path.exists('serviceAccountKey.json'):
    # 本地環境：讀取檔案
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    # 雲端環境：從環境變數讀取 JSON 字串
    firebase_config = os.getenv('FIREBASE_CONFIG')
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)

firebase_admin.initialize_app(cred)

app = Flask(__name__)

@app.route("/")
def index():
    link = "<h1>歡迎進入陳語婕的網站20260409</h1>"
    link += "<a href=/mis>課程</a><hr>"
    link += "<a href=/today>現在日期時間</a><hr>"
    link += "<a href=/me>關於我</a><hr>"
    link += "<a href=/welcome?u=語婕&d=靜宜資管&c=資訊管理導論>Get傳值</a><hr>"
    link += "<a href=/account>POST傳值</a><hr>"
    link += "<a href=/math2>次方根號計算</a><hr>"
    link += "<a href=/read>讀取Firestore資料</a><hr>"
    link += "<a href=/read2>靜宜資管老師查詢</a><hr>"
    link += "<a href=/spider1>爬曲子青老師本學期課程</a><hr>"
    return link

@app.route("/spider1")
def spider1():
    R = ""
    url = "https://www1.pu.edu.tw/~tcyang/course.html"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    #print(Data.text)
    sp = BeautifulSoup(Data.text, "html.parser")
    result=sp.select(".team-box a")

    for i in result:
        R += i.text + i.get("href") + "<br>"
    return R

@app.route("/read2", methods=["GET", "POST"])
def read2():
    
    if request.method == "POST":
        # 接收從網頁表單傳來的老師姓名
        keyword = request.form.get("teacher_name")
        
        Result = f"<h3>關於「{keyword}」的查詢結果：</h3>"
        found = False
        
        # 讀取 Firebase 資料庫
        collection_ref = db.collection("靜宜資管2026")
        docs = collection_ref.get()
        
        for doc in docs:
            teacher = doc.to_dict()
            # 模糊比對老師姓名 (只要包含輸入字元即可)
            if keyword in teacher.get("name", ""):
                found = True
                Result += f"<b>老師姓名：</b>{teacher.get('name')}<br>"
                Result += f"<b>研究室：</b>{teacher.get('lab', '無資料')}<br>"
                Result += f"<b>Email：</b>{teacher.get('mail', '無資料')}<br>"
                Result += "<hr>"

        if not found:
            Result = f"抱歉，資料庫中找不到名為「{keyword}」的老師資料。"
        
        return Result + "<br><a href='/read2'>返回重新查詢</a>"
    return render_template("read2.html")

@app.route("/read")
def read():
    Result = ""
    db = firestore.client()
    collection_ref = db.collection("靜宜資管2026")    
    docs = collection_ref.get()    
    docs = collection_ref.order_by("lab", direction=firestore.Query.DESCENDING).limit(5).get()
    for doc in docs:         
        Result += str(doc.to_dict()) + "<br>"    
    return Result


@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href=/>返回首頁</a>"

@app.route("/today")
def today():
    now = datetime.now()
    return render_template("today.html", datetime=str(now))

@app.route("/me")
def me():
    return render_template("mis2026b.html")

@app.route("/welcome", methods=["GET"])
def welcome():
    user = request.values.get("u")
    d = request.values.get("d")
    c = request.values.get("c")
    return render_template("welcome.html", name = user ,dep = d,course = c)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        result = "您輸入的帳號是：" + user + "; 密碼為：" + pwd 
        return result
    else:
        return render_template("account.html")

@app.route("/math2")
def math2():
    return render_template("math2.html")


if __name__ == "__main__":
    app.run(debug=True)
