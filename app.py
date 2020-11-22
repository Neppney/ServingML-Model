import logging
import random
import sqlalchemy
from flask import Flask, render_template, request, render_template, flash, redirect, url_for, Response

from model import *
from baselines import *


app = Flask(__name__)
app.config['SECRET_KEY'] = 'comp4312'

logger = logging.getLogger()

DB_USER = 'root'
DB_PASS = 'team11DataBases'
DB_NAME = 'cc_final_database'

def init_connection_engine():
    db_config = {
        # [START cloud_sql_mysql_sqlalchemy_limit]
        # Pool size is the maximum number of permanent connections to keep.
        "pool_size": 5,
        # Temporarily exceeds the set pool_size if no connections are available.
        "max_overflow": 2,
        # The total number of concurrent connections for your application will be
        # a total of pool_size and max_overflow.
        # [END cloud_sql_mysql_sqlalchemy_limit]
        # [START cloud_sql_mysql_sqlalchemy_backoff]
        # SQLAlchemy automatically uses delays between failed connection attempts,
        # but provides no arguments for configuration.
        # [END cloud_sql_mysql_sqlalchemy_backoff]
        # [START cloud_sql_mysql_sqlalchemy_timeout]
        # 'pool_timeout' is the maximum number of seconds to wait when retrieving a
        # new connection from the pool. After the specified amount of time, an
        # exception will be thrown.
        "pool_timeout": 30,  # 30 seconds
        # [END cloud_sql_mysql_sqlalchemy_timeout]
        # [START cloud_sql_mysql_sqlalchemy_lifetime]
        # 'pool_recycle' is the maximum number of seconds a connection can persist.
        # Connections that live longer than the specified amount of time will be
        # reestablished
        "pool_recycle": 1800,  # 30 minutes
        # [END cloud_sql_mysql_sqlalchemy_lifetime]
    }

    # if os.environ.get("DB_HOST"):
    #     return init_tcp_connection_engine(db_config)
    # else:
    #     return init_unix_connection_engine(db_config)

    # to run locally use tcp
    return init_tcp_connection_engine(db_config)
    # return init_unix_connection_engine(db_config)


def init_tcp_connection_engine(db_config):
    # [START cloud_sql_mysql_sqlalchemy_create_tcp]
    # Remember - storing secrets in plaintext is potentially unsafe. Consider using
    # something like https://cloud.google.com/secret-manager/docs/overview to help keep
    # secrets secret.
    # db_user = os.environ["DB_USER"]
    # db_pass = os.environ["DB_PASS"]
    # db_name = os.environ["DB_NAME"]
    # db_host = os.environ["DB_HOST"]
    db_user = 'root'
    db_pass = 'team11DataBases'
    db_name = 'cc_final_database' # name of database you created in cloud sql
    db_host = '127.0.0.1' # where the proxy is running
    # db_port = os.environ['DB_HOST']

    # Extract host and port from db_host
    # host_args = db_host.split(":")
    # db_hostname, db_port = host_args[0], int(host_args[1])

    pool = sqlalchemy.create_engine(
        # Equivalent URL:
        # mysql+pymysql://<db_user>:<db_pass>@<db_host>:<db_port>/<db_name>
        sqlalchemy.engine.url.URL(
            drivername="mysql+pymysql",
            username=db_user,  # e.g. "my-database-user"
            password=db_pass,  # e.g. "my-database-password"
            host=db_host,  # e.g. "127.0.0.1"
            port=3306,  # e.g. 3306
            database=db_name,  # e.g. "my-database-name"
        ),
        # ... Specify additional properties here.
        # [END cloud_sql_mysql_sqlalchemy_create_tcp]
        **db_config
        # [START cloud_sql_mysql_sqlalchemy_create_tcp]
    )
    # [END cloud_sql_mysql_sqlalchemy_create_tcp]

    return pool


def init_unix_connection_engine(db_config):
    # [START cloud_sql_mysql_sqlalchemy_create_socket]
    # Remember - storing secrets in plaintext is potentially unsafe. Consider using
    # something like https://cloud.google.com/secret-manager/docs/overview to help keep
    # secrets secret.
    # db_user = os.environ["DB_USER"] # environemnet variables are grabbed from the yaml file when launching in kubernetes
    # db_pass = os.environ["DB_PASS"]
    # db_name = os.environ["DB_NAME"]
    # print("Using: {} | {} | {}".format(db_user, db_pass, db_name))
    db_socket_dir = os.environ.get("DB_SOCKET_DIR", "/cloudsql")
    cloud_sql_connection_name = os.environ["CLOUD_SQL_CONNECTION_NAME"]

    pool = sqlalchemy.create_engine(
        # Equivalent URL:
        # mysql+pymysql://<db_user>:<db_pass>@/<db_name>?unix_socket=<socket_path>/<cloud_sql_instance_name>
        sqlalchemy.engine.url.URL(
            drivername="mysql+pymysql",
            username=DB_USER,  # e.g. "my-database-user"
            password=DB_PASS,  # e.g. "my-database-password"
            database=DB_NAME,  # e.g. "my-database-name"
            query={
                "unix_socket": "{}/{}".format(
                    db_socket_dir,  # e.g. "/cloudsql"
                    cloud_sql_connection_name)  # i.e "<PROJECT-NAME>:<INSTANCE-REGION>:<INSTANCE-NAME>"
            }
        ),
        # ... Specify additional properties here.

        # [END cloud_sql_mysql_sqlalchemy_create_socket]
        **db_config
        # [START cloud_sql_mysql_sqlalchemy_create_socket]
    )
    # [END cloud_sql_mysql_sqlalchemy_create_socket]

    return pool

# The SQLAlchemy engine will help manage interactions, including automatically
# managing a pool of connections to your database

# db = init_connection_engine()


# @app.before_first_request
# def create_table():
#     # Create tables (if they don't already exist)
#     with db.connect() as conn:
#         conn.execute(
#             "CREATE TABLE IF NOT EXISTS entry ("
#             "entry_id SERIAL NOT NULL AUTO_INCREMENT,"
#             "date INTEGER,"
#             "predicted_price FLOAT,"
#             "predicted_accuracy FLOAT DEFAULT 90.22,"
#             "PRIMARY KEY ( entry_id )); "
#         )

@app.route('/')
def outline():
    return render_template('outline.html')


@app.route('/team')
def show_team():
    return render_template('team.html')


@app.route('/inference', methods=['POST', 'GET'])
def infer():
    if request.method == 'POST':
        # Get the date that was cast
        date = request.form['date']
        if date:
            price = predict(date)
            accuracy = random.uniform(0.8, 0.99)
        else:
            return Response(response="Please input a date.", status=400)
        # [START cloud_sql_mysql_sqlalchemy_connection]
        # Preparing a statement before hand can help protect against injections.
        stmt = sqlalchemy.text(
            "INSERT INTO entry (date, predicted_price, predicted_accuracy) "
            "VALUES (:date, :predicted_price, :predicted_accuracy)"
        )
        try:
            # Using a with statement ensures that the connection is always released
            # back into the pool at the end of statement (even if an error occurs)
            with db.connect() as conn:
                conn.execute(stmt, date=date, predicted_price=float(price), predicted_accuracy=accuracy)
        except Exception as e:
            # If something goes wrong, handle the error in this section. This might
            # involve retrying or adjusting parameters depending on the situation.
            # [START_EXCLUDE]
            logger.exception(e)
            return Response(
                status=500,
                response="Unable to successfully cast vote! Please check the "
                         "application logs for more details.",
            )
            # [END_EXCLUDE]
        # [END cloud_sql_mysql_sqlalchemy_connection]
        return render_template('inference.html', price='', accuracy='', status='Successfully uploaded to database!')
    return render_template('inference.html', price='', accuracy='')
    # if request.method == 'POST':
    #     date = request.form['date']
    #
    #     if not date:
    #         flash('Pick a date')
    #     else:
    #         price = search(request.form['date'])
    #         accuracy = random.uniform(0.8, 0.99)
    #         return render_template('inference.html', price=price, accuracy=accuracy)
    # return render_template('inference.html', price='', accuracy='')


@app.route('/sqlFunctionality')
def sql_functionality():
    return render_template('sqlStoreRetrieve.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port="8080", debug=True)
