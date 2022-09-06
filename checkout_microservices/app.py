from flask import Flask, request, jsonify, json, make_response
import requests
import sqlite3 as sql
import jwt
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ASip3nLsAlAr-YME'

# decorator for verifying the JWT
def token_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = None
        # return jsonify(request.headers['bearer-token'])
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



@app.route('/cart', methods=['GET', 'POST'])
@token_required
def Cart(current_user_id, token):
    if request.method == 'POST':
        new_items = request.get_json()
        if not new_items or not len(new_items):
            return { "message" : "No items found" }

        conn = sql.connect('database.db')
        conn.row_factory = sql.Row
        cur = conn.cursor()
        result = cur.execute("SELECT items FROM cart WHERE user_id = ?", (current_user_id,)).fetchone()
        
        # cart already has a few items, so append new ones
        if result:
            cart_items = json.loads(result["items"])

            for key in new_items.keys():
                cart_items[key] = new_items[key]

            cur.execute("UPDATE cart SET items = ? WHERE user_id = ?", (json.dumps(cart_items),current_user_id))
            conn.commit()
            return { "message" : "Added new items to cart" }

        # There is no cart for this user so create one and add items to it
        else:
            cur.execute("INSERT into cart VALUES (NULL,?, ?)", (current_user_id, json.dumps(new_items)))
            conn.commit()
            response = requests.post("http://localhost:5001/update-cart-id", json = {"cart_id" : cur.lastrowid}, headers = {"x-access-token" : token})
            print(response.json())
            return { "message" : "Cart items added" }

    else:
        conn = sql.connect('database.db')
        conn.row_factory = sql.Row
        cur = conn.cursor()
        row = cur.execute("SELECT items FROM cart WHERE user_id = ?", (current_user_id,)).fetchone()

        if row:
            # cart_items = json.loads(row[""])
            cart_items = json.loads(row["items"])
            print(cart_items)

            response = requests.post("http://localhost:5000/product/availability", json = cart_items, headers = {"x-access-token" : token}).json()

            

            return jsonify(response)

        return {"message" : "No cart items found"}

    

if __name__ == '__main__':
    app.run(debug=True, port=5002)

