Create database Ecommerce;
use Ecommerce;
-- creating Dimension tables
-- 1 creating products dim
Create Table Products(
product_key int primary key,
product_id  varchar(100),
product_category varchar(100),
product_name varchar(100),
brand varchar(100)
);
-- 2 creating customers dim
create table Customers(
customer_key int primary key,
customer_id varchar(100),
customer_unique_id varchar(100),
registration_date date,
customer_zip_code_prefix varchar(10),
customer_city_english varchar(100),
customer_state varchar(10),
gender varchar(2),
age_group varchar(10)
);

-- creating category dim
create table Category(
category_key int primary key,
product_category varchar(100),
parent_category varchar(100),
seasonal_flag int
);

-- creating date dim
create table Date(
date_key int primary key,
full_date date,
day int,
day_of_week varchar(10),
month int,
month_name varchar(20),
year int,
quarter int,
week_of_year int
);

-- creating payment dim
Create table Payments(
payment_key int primary key,
payment_type varchar(50)
);

-- creating shipping dim
create table Shipping(
shipping_key int primary key,
shipping_type varchar(50),
delivery_days int,
order_status varchar(50)
);

-- creating fact table
create table Fact(
fact_id int auto_increment primary key,
customer_key int,
product_key int,
date_key int,
shipping_key int,
payment_key int,
category_key int,
quantity int,
gross_amount decimal,
discount_amount decimal,
net_amount decimal,
cost_amount decimal,
profit_amount decimal,
foreign key (customer_key) references Customers(customer_key),
foreign key(product_key) references Products(product_key),
foreign key(date_key) references Date(date_key),
foreign key(shipping_key) references Shipping(shipping_key),
foreign key(payment_key) references Payments(payment_key),
foreign key (category_key) references Category(category_key)
);












