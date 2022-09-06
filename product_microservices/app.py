from flask import Flask, request, jsonify, json
import sqlite3 as sql
from flask_restful import Resource, Api
import jwt
from functools import wraps

app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = 'ASip3nLsAlAr-YME'


# decorator for verifying the JWT
def token_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = None
        # jwt is passed in the request header
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        # return 401 if token is not passed
        if not token:
            return jsonify({'message' : 'Token is missing !!'})
  
        try:
            # decoding the payload to fetch the stored details
            data = jwt.decode(token, app.config['SECRET_KEY'])
            # current_user_id = data["public_id"]
        except:
            return jsonify({
                'message' : 'Token is invalid !!'
            })
        # returns the current logged in users context to the routes
        return  func(*args, **kwargs)
  
    return decorated


# apis using Flask RESTful
class Products(Resource):
    def get(self):
        con = sql.connect('database.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("Select * from products")
        rows = cur.fetchall()
        con.close()

        data = []
        for row in rows:
            data.append(dict(row))

        return jsonify(data)
    
    @token_required
    def post(self):
        products_json = request.get_json()
        # To insert one or more rows at a time
        # COnvert list of json/dict to list of tuple
        products = [ tuple(product.values()) for product in products_json ]
        try:
            with sql.connect('database.db') as con:
                cur = con.cursor()
                cur.executemany("INSERT INTO products (name, price, quantity) VALUES (?,?,?)", products)
                con.commit()
                message = "Added " + str(cur.rowcount) + " product(s) to database"
                # message = "Product(s) added successfully"
        except:
            message = "Error in insert operation"
        finally:
            con.close()
            return {"message" : message}
        
class Product(Resource):
    @token_required
    def get(self, productid):
        try:
            con = sql.connect('database.db')
            con.row_factory = sql.Row
            cur = con.cursor()
            cur.execute("SELECT * FROM products WHERE id = ?", (productid,))
            row = cur.fetchone()

            if row:
                data = dict(row)
                return jsonify(data)
        except:
            return {"message" : "There is no such product"}
        finally:
            con.close()


    @token_required
    def put(self, productid):
        product_json = request.get_json()
        try:
            con = sql.connect('database.db')
            con.row_factory = sql.Row
            cur = con.cursor()
            cur.execute("UPDATE products SET name = ?, price = ?, quantity = ? WHERE id = ?", (product_json["name"], product_json["price"], product_json["quantity"],productid))
            con.commit()
            return {"message" : "Product updated successfully"}
        except:
            return {"message" : "There is no such product"}
        finally:
            con.close()



    @token_required
    def delete(self, productid):
        try:
            con = sql.connect('database.db')
            con.row_factory = sql.Row
            cur = con.cursor()
            cur.execute("DELETE from products WHERE id = ?", (productid,))
            con.commit()
            con.close()
            return { "message" : "Product deleted successfully" }
        except:
            return { "message" : "There is no such product" }

class ProductAvailability(Resource):
    @token_required
    def post(self):
        productid_quantity = dict(request.get_json())
        print(productid_quantity)
        response_data = []
        try:
            con = sql.connect('database.db')
            con.row_factory = sql.Row
            cur = con.cursor()
            for productid, quantity in productid_quantity.items():

                row = cur.execute("Select name, price, quantity from products WHERE id = ?", (int(productid),)).fetchone()
                
                # product is discontinued
                if not row:
                    response_data.append({"message" : "Product with id " + productid + " is no longer being sold."})
                    continue
                
                a_product = {
                    "id" : int(productid),
                    "name" : row["name"],
                    "price" : row["price"],
                    "quantity" : quantity
                }
                # quantity required by a user is less than or equal to stock quantity i.e. In Stock
                if quantity <= row["quantity"]:
                    a_product["availability"] = "In Stock"
                else:
                    a_product["availability"] = "Out of Stock"

                response_data.append(a_product)

            con.close()
            return jsonify(response_data)

        except:
            return {"message" : "Something went wrong! Please try again"}


api.add_resource(Products, '/products/')
api.add_resource(Product, '/product/<productid>')
api.add_resource(ProductAvailability, '/product/availability')


if __name__ == '__main__':
    app.run(debug=True)



# apis using Flask
# @app.route('/products', methods=['GET', 'POST'])
# def products():
#     if request.method == 'POST':

#         product_json = request.get_json()
        
#         try:
#             with sql.connect('database.db') as con:
#                 cur = con.cursor()
#                 cur.execute("INSERT INTO products (name, price, quantity) VALUES (?,?,?)", (product_json['name'], product_json['price'], product_json['quantity']))

#                 con.commit()

#                 message = "Product added successfully"
#         except:
#             message = "Error in insert operation"
#         finally:
#             con.close()
#             return message
#     else:
#         con = sql.connect('database.db')
#         con.row_factory = sql.Row
#         cur = con.cursor()
#         cur.execute("Select * from products")
#         rows = cur.fetchall()

#         data = []
#         for row in rows:
#             data.append(dict(row))

#         return jsonify(data)
