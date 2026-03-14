#Data population script for MySQL database using SQLAlchemy and pandas
from gettext import install
import pip

!pip install sqlalchemy
!pip install mysql-connector-python
!pip install pymysql

from pydoc import text

import pandas as pd
from sqlalchemy import create_engine
# Create a connection to the MySQL database
engine = create_engine("mysql+pymysql://root:12345@localhost:3306/ecommerce")

# Load and insert payments data
payments = pd.read_csv(r"C:\ProgramData\MySQL\MySQL Server 8.0\Uploads\payment_processed.csv")
payments.to_sql('payments', engine, if_exists='append', index=False)

# Load and insert date data
date= pd.read_csv(r"C:\ProgramData\MySQL\MySQL Server 8.0\Uploads\date_processed.csv")
date.to_sql('date', engine, if_exists='append', index=False)


# Fix product_id column type before inserting products
with engine.connect() as conn:
    conn.execute(text("ALTER TABLE products MODIFY COLUMN product_id VARCHAR(100)"))
    conn.commit()
# Load and insert products data
products = pd.read_csv(r"C:\ProgramData\MySQL\MySQL Server 8.0\Uploads\products_processed.csv")
products = products[['product_key', 'product_id', 'product_category', 'product_name', 'brand']]
products.to_sql('products', engine, if_exists='append', index=False)


# Load and insert customers data
customer= pd.read_csv(r"C:\ProgramData\MySQL\MySQL Server 8.0\Uploads\customers_processed.csv")
customer.to_sql('customers', engine, if_exists='append', index=False)

# Load and insert category data
category= pd.read_csv(r"C:\ProgramData\MySQL\MySQL Server 8.0\Uploads\category_processed.csv")
category.to_sql('category', engine, if_exists='append', index=False)

# Load and insert fact data
fact= pd.read_csv(r"C:\ProgramData\MySQL\MySQL Server 8.0\Uploads\Fact_Order_line.csv")
fact = fact.drop(columns=['order_id'])
fact.to_sql('fact', engine, if_exists='append', index=False)
