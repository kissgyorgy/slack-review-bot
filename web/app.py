import datetime as dt
import uwsgi
from uwsgidecorators import filemon
from flask import Flask, request, render_template, redirect, url_for


app = Flask(__name__)
START_SIGNUM = 99


@app.route('/')
def index():
    if request.method == 'GET':
        return render_template('index.html')


@app.route('/reload')
def reload():
    uwsgi.reload()
    print("Reloaded")
    return redirect(url_for('index'))


@app.route('/edit')
def edit():
    return render_template('edit.html')


# uwsgi.add_cron(signal, minute, hour, day, month, weekday)
def uwsgi_main():
    def print_ran(signum):
        print("RAN at", dt.datetime.now())
    uwsgi.register_signal(START_SIGNUM, "", print_ran)
    uwsgi.add_cron(START_SIGNUM, -1, -1, -1, -1, -1)
    print("UWSGI STarted")

    filemon("web/templates/index.html")(tmp_has_been_modified)
    filemon("web/templates/edit.html")(tmp_has_been_modified)


def tmp_has_been_modified(num):
    print("web/ directory has been modified. Reloading")
    uwsgi.reload()


def main():
    app.run()


if __name__.startswith('uwsgi_file'):
    uwsgi_main()

elif __name__ == '__main__':
    main()
