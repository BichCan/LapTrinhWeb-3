from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = "abc123"

# Kết nối database
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# Trang tìm kiếm chương trình
@app.route("/")
def search():

    keyword = request.args.get("keyword", "").strip().lower()

    conn = get_db()
    cur = conn.cursor()

    if keyword:
        cur.execute("""
            SELECT * FROM chuongtrinh
            WHERE LOWER(tenct) LIKE ?
            OR LOWER(mact) LIKE ?
            OR LOWER(linhvuc) LIKE ?
        """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
    else:
        cur.execute("SELECT * FROM chuongtrinh")

    data = cur.fetchall()

    conn.close()

    return render_template("search.html", data=data)

# Trang chi tiết chương trình
@app.route("/detail/<mact>")
def detail(mact):

    conn = get_db()
    cur = conn.cursor()

    # lấy thông tin chương trình
    cur.execute("SELECT * FROM chuongtrinh WHERE mact=?", (mact,))
    ct = cur.fetchone()

    # lấy môn học
    cur.execute("""
        SELECT hp.mahp, hp.tenhp, hp.sotc, ct.hocki, ct.loai, ct.hocki, ct.stt
        FROM chuongtrinhct ct
        JOIN hocphan hp ON ct.mahp = hp.mahp
        WHERE ct.mact = ?
        ORDER BY ct.hocki, ct.stt
    """, (mact,))

    rows = cur.fetchall()

    conn.close()

    return render_template("detail.html", rows=rows, ct=ct)
# Trang admin thêm môn
@app.route("/add/<mact>", methods=["GET","POST"])
def add_subject(mact):

    conn = get_db()
    cur = conn.cursor()

    # lấy thông tin chương trình
    cur.execute("SELECT * FROM chuongtrinh WHERE mact=?", (mact,))
    ct = cur.fetchone()

    cur.execute("SELECT * FROM hocphan")
    hocphan = cur.fetchall()

    if request.method == "POST":

        stt = request.form["stt"]
        mahp = request.form["mahp"]
        hocki = request.form["hocki"]

        # kiểm tra đã tồn tại chưa
        cur.execute("""
        SELECT * FROM chuongtrinhct
        WHERE mact=? AND mahp=?
        """,(mact, mahp))

        check = cur.fetchone()

        if check:
            conn.close()
            flash("Môn học đã tồn tại trong chương trình!", "error")
            return redirect(request.url)

        # lấy số tín chỉ
        cur.execute("SELECT sotc FROM hocphan WHERE mahp=?", (mahp,))
        sotc = cur.fetchone()["sotc"]

        cur.execute("""
        INSERT INTO chuongtrinhct (mact, mahp, stt, sotc, hocki, loai)
        VALUES (?, ?, ?, ?, ?, ?)
        """,(mact, mahp, stt, sotc, hocki, "Bắt buộc"))

        conn.commit()
        conn.close()

        flash("Thêm môn học thành công!", "success")

        return redirect(url_for('detail',mact=mact))

    conn.close()

    return render_template("form.html", hocphan=hocphan, ct=ct)
if __name__ == "__main__":
    app.run(debug=True)