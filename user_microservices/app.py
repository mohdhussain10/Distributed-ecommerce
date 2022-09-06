from flask import Flask, request, jsonify, json, make_response
# from flask_restful import Resource, Api
import requests
import sqlite3 as sql
from secrets import compare_digest
import jwt
from functools import wraps
# from flask_jwt import JWT, jwt_required, current_identity
# from security import authenticate, identity


app = Flask(__name__)
app.config['SECRET_KEY'] = 'ASip3nLsAlAr-YME'
# api = Api(app)
# jwt = JWT(app, authenticate, identity)


@app.route('/signup', methods=['POST'])
def SignUp():
    data = request.get_json()

    conn = sql.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO users (username, password) VALUES(?,?)",(data['username'],data['password']))

    conn.commit()
    conn.close()

    return {"message":"User created"}


@app.route('/login', methods=['POST'])
def LogIn():
    json_data = request.get_json()

    if not json_data or not json_data["username"] or not json_data["password"]:
        # returns 401 if any email or / and password is missing
        return make_response(
            'Could not verify',
            401,
            {'WWW-Authenticate' : 'Basic realm ="Login required !!"'}
        )

    conn = sql.connect('database.db')
    conn.row_factory = sql.Row
    cursor = conn.cursor()

    result = cursor.execute("SELECT * FROM users WHERE username=?",(json_data["username"],))
    row = result.fetchone()

    if row:
        user = dict(row)
    else:
        user = None
    if not user:
        # returns 401 if user does not exist
        return make_response(
            'Could not verify',
            401,
            {'WWW-Authenticate' : 'Basic realm ="User does not exist !!"'}
        )
    
    if compare_digest(user["password"],json_data["password"]):
        # generates the JWT Token
        token = jwt.encode({
            'public_id': user["id"]
        }, app.config['SECRET_KEY'])
  
        return make_response(jsonify({'token' : token.decode('UTF-8')}), 201)
    
    # returns 403 if password is wrong
    return make_response(
        'Could not verify',
        403,
        {'WWW-Authenticate' : 'Basic realm ="Wrong Password !!"'}
    )



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
            return jsonify({'message' : 'Token is missing !!'}), 401
  
        try:
            # decoding the payload to fetch the stored details
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user_id = data["public_id"]
        except:
            return jsonify({
                'message' : 'Token is invalid !!'
            }), 401
        # returns the current logged in users context to the routes
        return  func(current_user_id,token, *args, **kwargs)
  
    return decorated


@app.route('/wishlist', methods=['GET', 'POST'])
# @jwt_required
@token_required
def Wishlist(current_user_id, token):
    if request.method == 'POST':

        product_id_json = request.get_json()
        
        # Convert list of product id to a comma seperated string
        product_id_csv = ""
        if(len(product_id_json) >=1 ):
            product_id_csv += str(product_id_json[0]["product_id"])

        for i in range(1,len(product_id_json)):
            product_id_csv += "," 
            product_id_csv += str(product_id_json[i]["product_id"])

        try:
            with sql.connect('database.db') as con:
                cur = con.cursor()
                wishlist = cur.execute("SELECT wishlist from users WHERE id = ?", (current_user_id,)).fetchone()
                # if there are already some wishlisted products, attach new ones to it
                if(wishlist[0] != None):
                    updated_wishlist = wishlist[0]
                    updated_wishlist  += ","
                    updated_wishlist += product_id_csv
                    cur.execute("UPDATE users SET wishlist = ? WHERE id = ?", (updated_wishlist,current_user_id))
                # otherwise directly wishlist the new ones
                else:
                    cur.execute("UPDATE users SET wishlist = ? WHERE id = ?", (product_id_csv,current_user_id))

                con.commit()

                message = "Product(s) added to wishlist successfully"
        except:
            message = "Error in insert operation"
        finally:
            con.close()
            return {"message" : message}
            
    # request.method is GET
    else:
        con = sql.connect('database.db')
        # con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("Select wishlist from users where id = ?", (current_user_id,))
        row = cur.fetchone()
        row = row[0]

        product_ids = row.split(',')
        url = "http://localhost:5000/product/{}"
        # products = []
        # for product_id in product_ids:
        #     res =
        #     products.append()
        products = [ requests.get( url.format( int(product_id) ), headers={'x-access-token' : token} ).json() for product_id in product_ids ]
        # data = dict(row)

        return jsonify(products)


@app.route('/update-cart-id', methods=['POST'])
@token_required
def UpdateCartId(current_user_id):
    body_data = request.get_json()
    print(body_data)
    conn = sql.connect('database.db')
    cur = conn.cursor()
    cur.execute("UPDATE users SET cart_id = ? WHERE id = ?", (body_data['cart_id'], current_user_id))
    conn.commit()
    result = cur.execute("SELECT * FROM users WHERE id = ?", (current_user_id,)).fetchone()
    print(result)
    return {"message" : "Cart ID updated in users table."}


if __name__ == '__main__':
    app.run(debug=True, port=5001)