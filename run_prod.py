from waitress import serve

from mungrade_flask_starter import app

if __name__ == "__main__":

    serve(app, host="0.0.0.0", port=5000)
 