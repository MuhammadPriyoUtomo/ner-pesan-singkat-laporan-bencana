import pymysql
import helper.App_config as App_config

def get_db_connection():
    connection = pymysql.connect(
        host=App_config.MYSQL_HOST,
        user=App_config.MYSQL_USER,
        password=App_config.MYSQL_PASSWORD,
        port=App_config.MYSQL_PORT,
        database=App_config.MYSQL_DB,
    )
    return connection

def get_db_dict_connection():
    return pymysql.connect(
        host=App_config.MYSQL_HOST,
        user=App_config.MYSQL_USER,
        password=App_config.MYSQL_PASSWORD,
        port=App_config.MYSQL_PORT,
        database=App_config.MYSQL_DB,
        cursorclass=pymysql.cursors.DictCursor
    )