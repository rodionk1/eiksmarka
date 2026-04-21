
Tables in the database:
Workers
-ID (integer) unique key
-Name (string) Workers name


Raw_products
-Raw_id (integer) unique key
-Raw_name_nor(text) Name of the item in norwegian, like "melk 1%" or "oksekjøtt", or "Sammalt rug finmalt"

-Raw_name_rus(text) Name of the item in russian, like "молоко 1%" or "говядина", or "Ржаная мука цельная, тонкий помол"

-Raw_name_pl(text) Name of raw material in polish.


Storage_raw
-Raw_id (integer) unique key
-Unit(choice) Unit name for measuring quantity can be "stk" for pieces or "kg" for weight quantities
-Quantity(number) Quantity of the item available in the storage
-Min_quantity (number) A quantity after which a warning is issued to include in purchase plan. Zero by default
-Price_pr_unit (number) Price per unit


Preps
A table with possible preps for food preparation. 
-Prep_id (int) A prep 
-Prep_name (text) name of the prep, like "fryst rosinbolle"
-Ingredients_prep (json) a json of id's from preps and their quantities.
-Ingredients_raw (json) a json of id's from storage_raw and their quantities.
-Unit (choice) stk or kg or g
-Default_qty (number) default quantity for the given ingredients set


Storage_prep
A table with prep for dishes
-Prep_id (integer) unique key references Prep_id
-Unit (choice) can be "stk" for pieces or "kg" or "g" for weight quantities
-Made_date (date) production date
-Made_by (int) workers id

Products
-Prod_id (integer) unique key
-Prod_name (text) name of the product
-Unit (choice) stk or kg
-Default_quantity (number) a default quantity for which the ingredients are given
-Ingredients_prep (json) a json of id's from Storage_prep with quantity in appropriate units
-Ingredients_raw (json) a json of id's from Storage_raw and quantity in appropriate units
-Sales_price_pr_unit (number) price in crowns.

Storage_prod
A table with ready products
-ID (integer) unique key for the entry
-Prod_id (int) references products.id
-Quantity (number)
-Made_date (made_date)
-Made_by (int) workers ID

Kafe_1
Shared with main storage, so all references to cafeteria 1 go to Storage_prod.

Kafe_2
Table of ready products sent to cafeteria from main storage.
Same structure as Storage_prod.

Purchase
A table for planning purchases of raw quantities
-ID (int) unique entry id
-Date (date)
-Contents (json) a json with id's from 
-Made by (int) worker's id or 0 for automatically inserted entry
-Control (boolean) Whether the entry has been controlled and purchase approved
-Accomplished (boolean) Whether the purchase has been accomplished

Activity
A table with planned production activity 
-ID (int) unique entry ID
-Product_type (choice) Either prep or ready product
-Product_id (int) an ID of product which will be produced
-Unit (choice) "kg" or "stk"
-Date (date) planned activity date
-Control (bool) control if the entry was controlled manually
-Accomplished (bool) accomplished or not


Customers
-ID (int)
-Phone (int) a 8 digit number for a Norwegian standart phone number.
-Name (string) can be blank
-e-mail (string) a e-mail address with @

Orders
-ID (int) unique order ID
-Customer_id references  Customers.ID
-Content (json) a json of products

