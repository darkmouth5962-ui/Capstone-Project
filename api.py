# Commands (POST/PUT/DELETE) go to command handlers
# Queries (GET) go to query handlers

from flask import Flask, request, jsonify
from flask_cors import CORS
from commands.command_handlers import (
    handle_create_user,
    handle_update_user_profile,
    handle_add_ingredient,
    handle_remove_ingredient,
    handle_favorite_recipe,
    handle_unfavorite_recipe,
    handle_update_appliances,
    handle_log_recipe_search
)
from queries.query_handlers import (
    query_user_profile,
    query_user_pantry,
    query_recipe_by_id,
    query_recipes_by_ingredients,
    query_user_favorites,
    query_shopping_suggestions
)
from consumers.event_consumers import setup_event_consumers

app = Flask(__name__)
# enable CORS for all routes - allow any origin for development
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# initialize event consumers
setup_event_consumers()

# USER ENDPOINTS

@app.route('/api/users', methods=['POST'])
def create_user():
    # creates a new user
    # Body: {"username": str, "password": str, "dietary_restrictions": [str]}
    
    data = request.get_json()
    result = handle_create_user(
        username=data.get('username'),
        password=data.get('password'),
        dietary_restrictions=data.get('dietary_restrictions', [])
    )
    
    status_code = 201 if result['success'] else 400
    return jsonify(result), status_code

@app.route('/api/users/<user_id>/profile', methods=['GET'])
def get_user_profile(user_id):
    # QUERY: get user profile
    
    profile = query_user_profile(user_id)
    
    if profile:
        return jsonify(profile), 200
    else:
        return jsonify({'error': 'User not found'}), 404

@app.route('/api/users/<user_id>/profile', methods=['PUT'])
def update_user_profile(user_id):
    # updates user profile
    # Body: {"dietary_restrictions": [str], "skill_level": str}
    
    data = request.get_json()
    result = handle_update_user_profile(user_id, data)
    
    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code

# INGREDIENT ENDPOINTS

@app.route('/api/users/<user_id>/ingredients', methods=['GET'])
def get_user_ingredients(user_id):
    # QUERY: get all ingredients in user's pantry
    
    pantry = query_user_pantry(user_id)
    return jsonify({'ingredients': pantry}), 200

@app.route('/api/users/<user_id>/ingredients', methods=['POST'])
def add_ingredient(user_id):
    # adds ingredient to pantry
    # Body: {"ingredient_name": str, "amount": float, "exp_date": str}
    
    data = request.get_json()
    result = handle_add_ingredient(
        user_id=user_id,
        ingredient_name=data.get('ingredient_name'),
        amount=data.get('amount', 1.0),
        exp_date=data.get('exp_date')
    )
    
    status_code = 201 if result['success'] else 400
    return jsonify(result), status_code

@app.route('/api/users/<user_id>/ingredients/<ingredient_id>', methods=['DELETE'])
def remove_ingredient(user_id, ingredient_id):
    # removes ingredient from pantry
    
    result = handle_remove_ingredient(user_id, ingredient_id)
    
    status_code = 200 if result['success'] else 404
    return jsonify(result), status_code

# RECIPE SEARCH ENDPOINTS

@app.route('/api/recipes/search', methods=['POST'])
def search_recipes():
    # QUERY: search recipes by ingredients
    """
    Body: {
        "user_id": str,
        "ingredient_names": [str],
        "filters": {
            "max_time": int,
            "skill_level": str,
            "dietary_tags": [str],
            "cuisine": str
        }
    }
    """
    data = request.get_json()
    
    user_id = data.get('user_id')
    ingredient_names = data.get('ingredient_names', [])
    filters = data.get('filters', {})
    
    # perform query
    results = query_recipes_by_ingredients(ingredient_names, filters)
    
    # log the search asynchronously
    if user_id:
        handle_log_recipe_search(user_id, ingredient_names, filters, len(results))
    
    return jsonify({
        'results': results,
        'count': len(results)
    }), 200

@app.route('/api/recipes/<recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    # QUERY: get single recipe by ID
    
    recipe = query_recipe_by_id(recipe_id)
    
    if recipe:
        return jsonify(recipe), 200
    else:
        return jsonify({'error': 'Recipe not found'}), 404

# FAVORITES ENDPOINTS

@app.route('/api/users/<user_id>/favorites', methods=['GET'])
def get_favorites(user_id):
    # QUERY: get user's favorite recipes
    
    favorites = query_user_favorites(user_id)
    return jsonify({'favorites': favorites}), 200

@app.route('/api/users/<user_id>/favorites', methods=['POST'])
def add_favorite(user_id):
    # adds recipe to favorites
    # Body: {"recipe_id": str, "recipe_name": str}
    
    data = request.get_json()
    result = handle_favorite_recipe(
        user_id=user_id,
        recipe_id=data.get('recipe_id'),
        recipe_name=data.get('recipe_name')
    )
    
    status_code = 201 if result['success'] else 400
    return jsonify(result), status_code

@app.route('/api/users/<user_id>/favorites/<recipe_id>', methods=['DELETE'])
def remove_favorite(user_id, recipe_id):
    # removes recipe from favorites
    
    result = handle_unfavorite_recipe(user_id, recipe_id)
    
    status_code = 200 if result['success'] else 404
    return jsonify(result), status_code

# SHOPPING SUGGESTIONS ENDPOINT

@app.route('/api/users/<user_id>/suggestions', methods=['GET'])
def get_suggestions(user_id):
    # QUERY: get shopping suggestions
    
    filters = {}
    
    if request.args.get('max_time'):
        filters['max_time'] = int(request.args.get('max_time'))
    
    if request.args.get('skill_level'):
        filters['skill_level'] = request.args.get('skill_level')
    
    top_n = int(request.args.get('max_suggestions', 5))
    
    suggestions = query_shopping_suggestions(user_id, filters, top_n)
    
    return jsonify({
        'suggestions': suggestions,
        'count': len(suggestions)
    }), 200

# APPLIANCES ENDPOINT

@app.route('/api/users/<user_id>/appliances', methods=['PUT'])
def update_appliances(user_id):
    # updates user's available appliances
    # Body: {"appliances": [str]}
    
    data = request.get_json()
    result = handle_update_appliances(
        user_id=user_id,
        appliances=data.get('appliances', [])
    )
    
    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code
 
# HEALTH CHECK

@app.route('/health', methods=['GET'])
def health_check():
    # health check endpoint
    return jsonify({
        'status': 'healthy',
        'message': 'SmartFridge API with CQRS+EDA is running'
    }), 200

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("SmartFridge API Starting")
    print("=" * 70)
    print("=" * 70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)