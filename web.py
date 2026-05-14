import requests
from bs4 import BeautifulSoup

from flask import Flask, render_template,request,make_response,jsonify
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

@app.route("/webhook", methods=["POST"])
def webhook():
    # build a request object
    req = request.get_json(force=True)
    # fetch queryResult from json
    action =  req.get("queryResult").get("action")
    msg =  req.get("queryResult").get("queryText")
    info = "動作：" + action + "； 查詢內容：" + msg
    return make_response(jsonify({"fulfillmentText": info}))

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
    link += "<a href=/spider1>爬取子青老師本學期課程</a><hr>"
    link += "<a href=/movie1>爬取即將上映電影</a><hr>"
    link += "<a href=/spidermovie>爬取即將上映電影</a><hr>"
    link += "<a href=/searchmovie>即將上映電影查詢</a><hr>"
    link += "<a href=/road>台中市十大肇事路口</a><hr>"
    link += "<a href=/weather>各縣市天氣查詢</a><hr>"
    link += "<a href=/rate>本週新片進DB</a><hr>"
    return link

@app.route("/rate")
def rate():
    #本週新片
    url = "https://www.atmovies.com.tw/movie/new/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    lastUpdate = sp.find(class_="smaller09").text[5:]
    print(lastUpdate)
    print()

    result=sp.select(".filmList")

    for x in result:
        title = x.find("a").text
        introduce = x.find("p").text

        movie_id = x.find("a").get("href").replace("/", "").replace("movie", "")
        hyperlink = "http://www.atmovies.com.tw/movie/" + movie_id
        picture = "https://www.atmovies.com.tw/photo101/" + movie_id + "/pm_" + movie_id + ".jpg"

        r = x.find(class_="runtime").find("img")
        rate = ""
        if r != None:
            rr = r.get("src").replace("/images/cer_", "").replace(".gif", "")
            if rr == "G":
                rate = "普遍級"
            elif rr == "P":
                rate = "保護級"
            elif rr == "F2":
                rate = "輔12級"
            elif rr == "F5":
                rate = "輔15級"
            else:
                rate = "限制級"

        t = x.find(class_="runtime").text

        t1 = t.find("片長")
        t2 = t.find("分")
        showLength = t[t1+3:t2]

        t1 = t.find("上映日期")
        t2 = t.find("上映廳數")
        showDate = t[t1+5:t2-8]

        doc = {
            "title": title,
            "introduce": introduce,
            "picture": picture,
            "hyperlink": hyperlink,
            "showDate": showDate,
            "showLength": int(showLength),
            "rate": rate,
            "lastUpdate": lastUpdate
        }

        db = firestore.client()
        doc_ref = db.collection("本週新片含分級").document(movie_id)
        doc_ref.set(doc)
    return "本週新片已爬蟲及存檔完畢，網站最近更新日期為：" + lastUpdate

@app.route("/weather", methods=['GET', 'POST'])
def weather():
    keyword = ""
    weather_results = []

    if request.method == 'POST':
        keyword = request.form.get("keyword").strip()
        
        search_city = keyword.replace("台", "臺")
        if not search_city.endswith(("市", "縣")):
            search_city += "市"

        token = "rdec-key-123-45678-011121314" 
        url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization={token}&format=JSON&locationName={search_city}"

        try:
            response = requests.get(url)
            data = response.json()

            if data.get("records") and data["records"].get("location"):
                loc_data = data["records"]["location"][0]
                city_name = loc_data["locationName"]
                
                elements = loc_data["weatherElement"]
                desc = elements[0]["time"][0]["parameter"]["parameterName"]
                rain = elements[1]["time"][0]["parameter"]["parameterName"]
                
                result_str = f"{city_name} 目前天氣：{desc}，降雨機率：{rain}%"
                weather_results.append(result_str)
            else:
                print(f"找不到該地點的資料：{search_city}")
                
        except Exception as e:
            print(f"發生錯誤：{e}")
    return render_template("weather.html", weather=weather_results, keyword=keyword)

@app.route("/road")
def road():
    R = "<h1>台中市十大肇事路口(113年10月)作者:陳語婕</h1><br>"
    url = "https://datacenter.taichung.gov.tw/swagger/OpenData/a1b899c0-511f-4e3d-b22b-814982a97e41"
    Data = requests.get(url)
    #print(Data.text)

    JsonData = json.loads(Data.text)
    R = ""
    for item in JsonData:
        R += item["路口名稱"] + "：發生" + item["總件數"] + "件，主因是" + item["主要肇因"] + "\n\n"

    return R

@app.route("/searchmovie", methods=['GET', 'POST'])
def searchmovie():
    keyword = ""
    movies = [] 

    if request.method == 'POST':
        keyword = request.form.get("keyword")

        url = "http://www.atmovies.com.tw/movie/next/"
        Data = requests.get(url)
        Data.encoding = "utf-8"
        sp = BeautifulSoup(Data.text, "html.parser")
        result = sp.select(".filmListAllX li")

        for item in result:
            try:
                # 取得編號與資料
                movie_id = item.find("a").get("href").replace("/movie/", "").replace("/", "")
                title = item.find(class_="filmtitle").text
                picture = "https://www.atmovies.com.tw" + item.find("img").get("src")
                hyperlink = "https://www.atmovies.com.tw" + item.find("a").get("href")
                
                runtime_text = item.find(class_="runtime").text
                showDate = runtime_text[5:15] if "上映日期" in runtime_text else "未提供"

                if keyword in title:
                    movies.append({
                        "movie_id": movie_id,
                        "title": title,
                        "picture": picture,
                        "hyperlink": hyperlink,
                        "showDate": showDate
                    })
            except:
                continue

    return render_template("serchmovie.html", movies=movies, keyword=keyword)

@app.route("/spidermovie")
def spidermovie():
    R = ""
    db = firestore.client()

    import requests
    from bs4 import BeautifulSoup
    url = "http://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    Data.encoding = "utf-8"

    sp = BeautifulSoup(Data.text, "html.parser")
    lastUpdate = sp.find(class_="smaller09").text.replace("更新時間：", "")

    result=sp.select(".filmListAllX li")
    total = 0
    for item in result:
        total += 1 
        movie_id = item.find("a").get("href").replace("/movie/", "").replace("/", "")
        title = item.find(class_="filmtitle").text
        picture = "https://www.atmovies.com.tw"+ item.find("img").get("src")
        hyperlink = "https://www.atmovies.com.tw"+ item.find("a").get("href")
        showDate = item.find(class_="runtime").text[5:15]

        doc = {
            "title": title,
            "picture": picture,
            "hyperlink": hyperlink,
            "showDate": showDate,
            "lastUpdate": lastUpdate
        }

        doc_ref = db.collection("電影2B").document(movie_id)
        doc_ref.set(doc)

        R += "網站最近更新日期：" + lastUpdate + "<br>"
        R += ("總共爬取" + str(total) + "部電影到資料庫")
    return R


@app.route("/movie1", methods=['GET', 'POST'])
def movie1():
    keyword = ""
    movies = []  # 用來存放篩選後的電影資料
    
    if request.method == 'POST':
        keyword = request.form.get("keyword")
        
        url = "http://www.atmovies.com.tw/movie/next/"
        Data = requests.get(url)
        Data.encoding = "utf-8"
        sp = BeautifulSoup(Data.text, "html.parser")
        result = sp.select(".filmListAllX li")
        
        for item in result:
            title = item.find("img").get("alt") # 電影名稱
            
            # 關鍵字篩選：如果名稱包含關鍵字，才加入清單
            if keyword in title:
                link = "https://www.atmovies.com.tw" + item.find("a").get("href")
                img_src = "https://www.atmovies.com.tw" + item.find("img").get("src")
                
                # 存成字典方便 HTML 讀取
                movies.append({
                    "title": title,
                    "link": link,
                    "img": img_src
                })

    return render_template("movie1.html", movies=movies, keyword=keyword)

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
