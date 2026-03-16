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
#thêm chương trình đào tạo
@app.route("/add_program", methods=["GET","POST"])
def add_program():
    if request.method == "POST":
        # Lấy dữ liệu từ form
        mact = request.form["mact"].strip().upper()
        tenct = request.form["tenct"].strip()
        chitieu = request.form["chitieu"].strip()
        linhvuc = request.form["linhvuc"].strip()

        # Kiểm tra dữ liệu đầu vào
        if not mact or not tenct or not chitieu or not linhvuc:
            flash("Vui lòng điền đầy đủ thông tin!", "error")
            return redirect(request.url)

        # Kiểm tra chỉ tiêu phải là số
        try:
            chitieu = int(chitieu)
            if chitieu <= 0:
                flash("Chỉ tiêu phải là số lớn hơn 0!", "error")
                return redirect(request.url)
        except ValueError:
            flash("Chỉ tiêu phải là số nguyên!", "error")
            return redirect(request.url)

        conn = get_db()
        cur = conn.cursor()

        # Kiểm tra mã chương trình đã tồn tại chưa
        cur.execute("SELECT * FROM chuongtrinh WHERE mact=?", (mact,))
        existing = cur.fetchone()

        if existing:
            conn.close()
            flash(f"Mã chương trình {mact} đã tồn tại!", "error")
            return render_template("add_program.html",
                                   chuongtrinh=request.form)

        # Thêm chương trình mới
        cur.execute("""
            INSERT INTO chuongtrinh (mact, tenct, chitieu, linhvuc)
            VALUES (?, ?, ?, ?)
        """, (mact, tenct, chitieu, linhvuc))

        conn.commit()
        conn.close()

        flash(f"Thêm chương trình {tenct} thành công!", "success")

        # Chuyển hướng về trang chi tiết của chương trình vừa thêm
        return redirect(url_for('detail', mact=mact))

    # GET request - hiển thị form
    return render_template("formaddprogram.html", chuongtrinh={})


@app.route("/delete_program/<mact>", methods=["POST"])
def delete_program(mact):
    conn = get_db()
    cur = conn.cursor()

    # Kiểm tra chương trình có tồn tại không
    cur.execute("SELECT * FROM chuongtrinh WHERE mact=?", (mact,))
    program = cur.fetchone()

    if not program:
        conn.close()
        flash("Không tìm thấy chương trình!", "error")
        return redirect(url_for('search'))

    # Xóa tất cả môn học trong chương trình (bảng chuongtrinhct)
    cur.execute("DELETE FROM chuongtrinhct WHERE mact=?", (mact,))

    # Xóa chương trình (bảng chuongtrinh)
    cur.execute("DELETE FROM chuongtrinh WHERE mact=?", (mact,))

    conn.commit()
    conn.close()

    flash(f"Đã xóa chương trình {program['tenct']} và các môn học trong chương trình thành công!", "success")
    return redirect(url_for('search'))
@app.route("/sua/<mact>/<mahp>", methods=["GET", "POST"])
def sua_mon(mact, mahp):
    db = get_db()

    db.execute("SELECT * FROM chuongtrinh WHERE mact=?", (mact,))
    ct = db.execute("SELECT * FROM chuongtrinh WHERE mact=?", (mact,)).fetchone()

    mon = db.execute("""
        SELECT ct.*, hp.tenhp, hp.sotc
        FROM chuongtrinhct ct
        JOIN hocphan hp ON ct.mahp = hp.mahp
        WHERE ct.mact=? AND ct.mahp=?
    """, (mact, mahp)).fetchone()

    if not mon:
        db.close()
        flash("Không tìm thấy học phần!", "error")
        return redirect(url_for('detail', mact=mact))

    hocphan = db.execute("SELECT * FROM hocphan").fetchall()

    if request.method == "POST":
        stt = request.form["stt"]
        mahp2 = request.form["mahp"]
        hocki = request.form["hocki"]

        sotc = db.execute("SELECT sotc FROM hocphan WHERE mahp=?", (mahp2,)).fetchone()["sotc"]

        if mahp2 != mahp:
            check = db.execute("SELECT * FROM chuongtrinhct WHERE mact=? AND mahp=?", (mact, mahp2)).fetchone()
            if check:
                db.close()
                flash("Môn học đã tồn tại trong chương trình!", "error")
                return redirect(request.url)

        db.execute("""
            UPDATE chuongtrinhct
            SET mahp=?, stt=?, sotc=?, hocki=?
            WHERE mact=? AND mahp=?
        """, (mahp2, stt, sotc, hocki, mact, mahp))

        db.commit()
        db.close()

        flash("Cập nhật học phần thành công!", "success")
        return redirect(url_for('detail', mact=mact))

    db.close()
    return render_template("edit_subject.html", ct=ct, mon=mon, hocphan=hocphan)

@app.route("/xoa/<mact>/<mahp>", methods=["POST"])
def xoa_mon(mact, mahp):
    db = get_db()

    db.execute("DELETE FROM chuongtrinhct WHERE mact=? AND mahp=?", (mact, mahp))

    db.commit()
    db.close()

    flash("Đã xóa môn học thành công!", "success")
    return redirect(url_for('detail', mact=mact))

if __name__ == "__main__":
    app.run(debug=True)