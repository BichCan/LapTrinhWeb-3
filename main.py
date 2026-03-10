from flask import Flask, render_template

app = Flask(__name__)

# trang tìm kiếm
@app.route("/")
def search():
    return render_template("search.html")

# trang chi tiết chương trình
@app.route("/detail")
def detail():
    return render_template("detail.html")

# trang admin thêm chương trình
@app.route("/form")
def form():
    return render_template("form.html")


if __name__ == "__main__":
    app.run(debug=True)