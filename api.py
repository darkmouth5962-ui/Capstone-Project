# SmartFridge API with PostgreSQL support
# Falls back to in-memory if database not available

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# Try to initialize database
USE_DATABASE = False
try:
    from database.init_db import initialize_database
    USE_DATABASE = initialize_database()
except Exception as e:
    print(f"\n⚠️  Database initialization failed: {e}")
    print("⚠️  Falling back to in-memory storage")
    print("⚠️  See database/DATABASE_SETUP.md for setup instructions\n")

# Import appropriate handlers based on database availability
if USE_DATABASE:
    print("✅ Using PostgreSQL for data storage")
    from commands.command_handlers import *
    from queries.query_handlers import *
else:
    print("⚠️  Using in-memory storage (data will be lost on restart)")
    from commands.command_handlers import *
    from queries.query_handlers import *

# Import appropriate event consumers based on database availability
if USE_DATABASE:
    from consumers.event_consumers import setup_event_consumers
else:
    from consumers.event_consumers import setup_event_consumers

# Initialize event consumers
setup_event_consumers()

# USER ENDPOINTS

@app.route('/api/users', methods=['POST'])
def create_user():
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
    profile = query_user_profile(user_id)
    if profile:
        return jsonify(profile), 200
    else:
        return jsonify({'error': 'User not found'}), 404

@app.route('/api/users/<user_id>/profile', methods=['PUT'])
def update_user_profile(user_id):
    data = request.get_json()
    result = handle_update_user_profile(user_id, data)
    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code

# INGREDIENT ENDPOINTS

@app.route('/api/users/<user_id>/ingredients', methods=['GET'])
def get_user_ingredients(user_id):
    pantry = query_user_pantry(user_id)
    return jsonify({'ingredients': pantry}), 200

@app.route('/api/users/<user_id>/ingredients', methods=['POST'])
def add_ingredient(user_id):
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
    result = handle_remove_ingredient(user_id, ingredient_id)
    status_code = 200 if result['success'] else 404
    return jsonify(result), status_code

# RECIPE SEARCH ENDPOINTS

@app.route('/api/recipes/search', methods=['POST'])
def search_recipes():
    data = request.get_json()
    user_id = data.get('user_id')
    ingredient_names = data.get('ingredient_names', [])
    filters = data.get('filters', {})
    
    results = query_recipes_by_ingredients(ingredient_names, filters)
    
    if user_id:
        handle_log_recipe_search(user_id, ingredient_names, filters, len(results))
    
    return jsonify({
        'results': results,
        'count': len(results)
    }), 200

@app.route('/api/recipes/<recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    recipe = query_recipe_by_id(recipe_id)
    if recipe:
        return jsonify(recipe), 200
    else:
        return jsonify({'error': 'Recipe not found'}), 404

# FAVORITES ENDPOINTS

@app.route('/api/users/<user_id>/favorites', methods=['GET'])
def get_favorites(user_id):
    favorites = query_user_favorites(user_id)
    return jsonify({'favorites': favorites}), 200

@app.route('/api/users/<user_id>/favorites', methods=['POST'])
def add_favorite(user_id):
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
    result = handle_unfavorite_recipe(user_id, recipe_id)
    status_code = 200 if result['success'] else 404
    return jsonify(result), status_code

# SHOPPING SUGGESTIONS ENDPOINT

@app.route('/api/users/<user_id>/suggestions', methods=['GET'])
def get_suggestions(user_id):
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
    storage_type = "PostgreSQL" if USE_DATABASE else "In-Memory"
    return jsonify({
        'status': 'healthy',
        'message': f'SmartFridge API with CQRS+EDA is running',
        'storage': storage_type
    }), 200

# ANALYTICS ENDPOINTS (Event System Demo)

@app.route('/api/analytics/system', methods=['GET'])
def get_system_analytics():
    """Get system-wide analytics tracked by event consumers"""
    if USE_DATABASE:
        from consumers.event_consumers import get_system_analytics
        stats = get_system_analytics()
    else:
        # For in-memory mode, get from read_db
        from queries.query_handlers import get_read_db
        read_db = get_read_db()
        stats = {
            'total_searches': sum(
                analytics.get('search_count', 0) 
                for analytics in read_db.get('user_analytics', {}).values()
            ),
            'total_users_created': len(read_db.get('user_profiles', {})),
            'total_favorites': sum(
                len(favs) for favs in read_db.get('user_favorites', {}).values()
            )
        }
    
    return jsonify({
        'analytics': stats,
        'note': 'Tracked via CQRS event consumers'
    }), 200

@app.route('/api/analytics/users/<user_id>', methods=['GET'])
def get_user_analytics(user_id):
    """Get analytics for specific user tracked by event consumers"""
    if USE_DATABASE:
        from consumers.event_consumers import get_user_analytics
        analytics = get_user_analytics(user_id)
    else:
        from queries.query_handlers import get_read_db
        read_db = get_read_db()
        analytics = read_db.get('user_analytics', {}).get(user_id, {
            'search_count': 0,
            'recent_searches': []
        })
    
    return jsonify({
        'user_id': user_id,
        'analytics': analytics
    }), 200

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("SmartFridge API Starting")
    if USE_DATABASE:
        print("Storage: PostgreSQL")
    else:
        print("Storage: In-Memory (temporary)")
    print("=" * 70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)