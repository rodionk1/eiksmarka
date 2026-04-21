**Functions for filling data tables**

A function to fill Raw_products.

A function to fill or update the Storage_raw table manually. Accepts arguments Raw_name or Raw_id, Quantity, Unit, Min_quantity, Price_pr_unit

A function to fill from a text or csv file
Reads a text file with lines describing Raw_name, Quantity, Unit, Min_quantity, Price_pr_unit and writes item to the table.


A function to fill or update the Preps table.
Reads text file with a recipy. 
First line indicates name of the prep, its standard size The text file contains description of ingredients and their quantities. One ingredient one line each.
The ingredients are searched in the storage_raw or Preps table  and the corresponding json is filled with the right id keys. If a recipy contains quantity in grams, this is checked with default unit for the entry in the storage_raw table.  

A function to fill Storage_prep
Arguments are name and quantity. As a date a system date is inserted. Made_by is optional.


A function to fill Product table by manual entry.
Arguments product name, default quantity, unit. Ingredients and quantity. Sales price is optional.

A function to fill Product table from a text file. 
First line gives name, standard size and unit. 
Next lines describe ingredients with quantities and unit for the quantities.



A function to fill entry to Storage_prod. 
Arguments: prod_id, quantity, date with default from system, made_by is optional.


A function to fill Purchase from a text file. 


A function to add planned production activity. 

A function to add 