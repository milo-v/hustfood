import pyodbc


def connection():
    s = 'localhost'  # Your server name
    d = 'hustfood'
    u = 'sa'  # Your login
    p = ''  # Your login password
    cstr = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + \
        s+';DATABASE='+d+';UID='+u+';PWD=' + p
    conn = pyodbc.connect(cstr)
    return conn
