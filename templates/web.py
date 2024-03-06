from flask import Flask, render_template
app=Flask(__name__)
@app.route("/biosecurity guide/weeds")
def index():
    return render_template("register.html")
if __name__=="main":
    app.run()