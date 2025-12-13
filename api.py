#!/usr/bin/env python3
"""
SmartFridge API with User Authentication and Profile System
PostgreSQL-backed with session management
"""

from flask import Flask, request, jsonify, session
from flask_cors import CORS
import sys
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# CORS configuration for codespaces
CORS(app, 
     resources={r"/*": {"origins": "*"}},  # allow all routes, not just /api/*
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
     expose_headers=["Content-Type"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# try to initialize database
USE_DATABASE = False
try:
    from database.init_db import initialize_database
    USE_DATABASE = initialize_database()
except Exception as e:
    print(f"\n  Database initialization failed: {e}")
    print("  Falling back to in-memory storage")
    print("  See database/DATABASE_SETUP.md for setup instructions\n")

# Import appropriate handlers based on database availability
if USE_DATABASE:
    print(" Using PostgreSQL for data storage")
    from commands.command_handlers import *
    from commands.auth_handlers import *
    from queries.query_handlers import *
    from consumers.event_consumers import setup_event_consumers
else:
    print("  Using in-memory storage (data will be lost on restart)")
    from commands.command_handlers import *
    from queries.query_handlers import *
    from consumers.event_consumers import setup_event_consumers

# initialize event consumers
setup_event_consumers()

# ============================================================================
# AUTHENTICATION DECORATORS
# ============================================================================

def login_required(f):
    # decorator to require authentication
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required', 'login_required': True}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_current_user_id():
    # get the current logged-in user's ID from session
    return session.get('user_id')

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    # register a new user account
    data = request.get_json()
    
    if not USE_DATABASE:
        return jsonify({'error': 'User accounts require PostgreSQL database'}), 503
    
    result = handle_register_user(
        username=data.get('username'),
        password=data.get('password'),
        email=data.get('email')
    )
    
    if result['success']:
        # auto-login after registration
        session['user_id'] = result['user_id']
        session['username'] = result['username']
        return jsonify(result), 201
    else:
        return jsonify(result), 400

@app.route('/api/auth/login', methods=['POST'])
def login():
    # login to existing account
    data = request.get_json()
    
    if not USE_DATABASE:
        return jsonify({'error': 'User accounts require PostgreSQL database'}), 503
    
    result = handle_login_user(
        username=data.get('username'),
        password=data.get('password')
    )
    
    if result['success']:
        # store user info in session
        session['user_id'] = result['user']['user_id']
        session['username'] = result['user']['username']
        return jsonify(result), 200
    else:
        return jsonify(result), 401

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    # logout current user
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'}), 200

@app.route('/api/auth/session', methods=['GET'])
def get_session():
    # get current session info
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user_id': session['user_id'],
            'username': session['username']
        }), 200
    else:
        return jsonify({
            'authenticated': False
        }), 200

# ============================================================================
# USER PROFILE ENDPOINTS
# ============================================================================

@app.route('/api/profile', methods=['GET'])
@login_required
def get_profile():
    # get current user's full profile
    user_id = get_current_user_id()
    
    # get basic profile
    profile = query_user_profile(user_id)
    if not profile:
        return jsonify({'error': 'Profile not found'}), 404
    
    # get pantry
    pantry = query_user_pantry(user_id)
    
    # get favorites
    favorites = query_user_favorites(user_id)
    
    # get equipment
    if USE_DATABASE:
        equipment_result = handle_get_user_equipment(user_id)
        equipment = equipment_result.get('equipment', [])
    else:
        equipment = []
    
    return jsonify({
        'profile': profile,
        'pantry': pantry,
        'favorites': favorites,
        'equipment': equipment
    }), 200

@app.route('/api/profile/dietary-restrictions', methods=['PUT'])
@login_required
def update_dietary_restrictions():
    # update dietary restrictions
    user_id = get_current_user_id()
    data = request.get_json()
    
    result = handle_update_user_dietary_restrictions(
        user_id=user_id,
        dietary_restrictions=data.get('dietary_restrictions', [])
    )
    
    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code

@app.route('/api/profile/skill-level', methods=['PUT'])
@login_required
def update_skill_level():
    # update skill level
    user_id = get_current_user_id()
    data = request.get_json()
    
    result = handle_update_user_skill_level(
        user_id=user_id,
        skill_level=data.get('skill_level')
    )
    
    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code

@app.route('/api/profile/password', methods=['PUT'])
@login_required
def update_password():
    # update password
    user_id = get_current_user_id()
    data = request.get_json()
    
    if not USE_DATABASE:
        return jsonify({'error': 'Password management requires PostgreSQL'}), 503
    
    result = handle_update_user_password(
        user_id=user_id,
        old_password=data.get('old_password'),
        new_password=data.get('new_password')
    )
    
    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code

@app.route('/api/profile/delete', methods=['DELETE'])
@login_required
def delete_account():
    # delete user account
    user_id = get_current_user_id()
    data = request.get_json()
    
    if not USE_DATABASE:
        return jsonify({'error': 'Account management requires PostgreSQL'}), 503
    
    result = handle_delete_user_account(
        user_id=user_id,
        password=data.get('password')
    )
    
    if result['success']:
        session.clear()
        return jsonify(result), 200
    else:
        return jsonify(result), 400

# ============================================================================
# INGREDIENT ENDPOINTS (Protected)
# ============================================================================

@app.route('/api/ingredients', methods=['GET'])
@login_required
def get_ingredients():
    # get current user's ingredients
    user_id = get_current_user_id()
    pantry = query_user_pantry(user_id)
    return jsonify({'ingredients': pantry}), 200

@app.route('/api/ingredients', methods=['POST'])
@login_required
def add_ingredient():
    # add ingredient to current user's pantry
    user_id = get_current_user_id()
    data = request.get_json()
    
    result = handle_add_ingredient(
        user_id=user_id,
        ingredient_name=data.get('ingredient_name'),
        amount=data.get('amount', 1.0),
        exp_date=data.get('exp_date')
    )
    
    status_code = 201 if result['success'] else 400
    return jsonify(result), status_code

@app.route('/api/ingredients/<ingredient_id>', methods=['DELETE'])
@login_required
def remove_ingredient(ingredient_id):
    # remove ingredient from current user's pantry
    user_id = get_current_user_id()
    result = handle_remove_ingredient(user_id, ingredient_id)
    
    status_code = 200 if result['success'] else 404
    return jsonify(result), status_code

# ============================================================================
# RECIPE SEARCH ENDPOINTS
# ============================================================================

@app.route('/api/recipes/search', methods=['POST'])
def search_recipes():
    # search recipes (public endpoint, but uses session if available)
    data = request.get_json()
    ingredient_names = data.get('ingredient_names', [])
    filters = data.get('filters', {})
    
    # get user_id from session if logged in (for dietary restriction filtering)
    user_id = get_current_user_id()
    
    print(f"\n🔍 Recipe search request:")
    print(f"   User ID: {user_id or 'Not logged in'}")
    print(f"   Ingredients: {ingredient_names}")
    print(f"   Filters: {filters}")
    
    # pass user_id to enable automatic dietary restriction filtering
    results = query_recipes_by_ingredients(ingredient_names, filters, user_id=user_id)
    
    print(f"   Results: {len(results)} recipes found")
    
    # log search if user is logged in
    if user_id:
        handle_log_recipe_search(user_id, ingredient_names, filters, len(results))
    
    return jsonify({
        'results': results,
        'count': len(results)
    }), 200

@app.route('/api/recipes/<recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    # get recipe details (public endpoint)
    recipe = query_recipe_by_id(recipe_id)
    
    if recipe:
        return jsonify(recipe), 200
    else:
        return jsonify({'error': 'Recipe not found'}), 404

# ============================================================================
# FAVORITES ENDPOINTS (Protected)
# ============================================================================

@app.route('/api/favorites', methods=['GET'])
@login_required
def get_favorites():
    # get current user's favorite recipes
    user_id = get_current_user_id()
    favorites = query_user_favorites(user_id)
    return jsonify({'favorites': favorites}), 200

@app.route('/api/favorites', methods=['POST'])
@login_required
def add_favorite():
    # add recipe to current user's favorites
    user_id = get_current_user_id()
    data = request.get_json()
    
    result = handle_favorite_recipe(
        user_id=user_id,
        recipe_id=data.get('recipe_id'),
        recipe_name=data.get('recipe_name')
    )
    
    status_code = 201 if result['success'] else 400
    return jsonify(result), status_code

@app.route('/api/favorites/<recipe_id>', methods=['DELETE'])
@login_required
def remove_favorite(recipe_id):
    # remove recipe from current user's favorites
    user_id = get_current_user_id()
    result = handle_unfavorite_recipe(user_id, recipe_id)
    
    status_code = 200 if result['success'] else 404
    return jsonify(result), status_code

# ============================================================================
# EQUIPMENT ENDPOINTS (Protected)
# ============================================================================

@app.route('/api/equipment', methods=['GET'])
@login_required
def get_equipment():
    # get current user's equipment
    user_id = get_current_user_id()
    
    if USE_DATABASE:
        result = handle_get_user_equipment(user_id)
        return jsonify(result), 200
    else:
        return jsonify({'equipment': []}), 200

@app.route('/api/equipment', methods=['PUT'])
@login_required
def update_equipment():
    # update current user's equipment
    user_id = get_current_user_id()
    data = request.get_json()
    
    result = handle_update_appliances(
        user_id=user_id,
        appliances=data.get('appliances', [])
    )
    
    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code

# ============================================================================
# SHOPPING SUGGESTIONS ENDPOINT (Protected)
# ============================================================================

@app.route('/api/suggestions', methods=['GET'])
@login_required
def get_suggestions():
    # get shopping suggestions for current user
    user_id = get_current_user_id()
    
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

# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@app.route('/api/analytics/system', methods=['GET'])
def get_system_analytics():
    # get system-wide analytics tracked by event consumers
    if USE_DATABASE:
        from consumers.event_consumers import get_system_analytics
        stats = get_system_analytics()
    else:
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

@app.route('/api/analytics/user', methods=['GET'])
@login_required
def get_user_analytics_endpoint():
    # get analytics for current user
    user_id = get_current_user_id()
    
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
        'analytics': analytics
    }), 200

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    # system health check
    storage_type = "PostgreSQL" if USE_DATABASE else "In-Memory"
    return jsonify({
        'status': 'healthy',
        'message': 'SmartFridge API with User Profiles is running',
        'storage': storage_type,
        'features': {
            'authentication': USE_DATABASE,
            'user_profiles': USE_DATABASE,
            'persistent_storage': USE_DATABASE
        }
    }), 200

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("SmartFridge API Starting")
    if USE_DATABASE:
        print("Storage: PostgreSQL")
        print("Features: User Accounts | Profiles | Persistence")
    else:
        print("Storage: In-Memory (temporary)")
        print("Features Lost: User Accounts (PostgreSQL required)")
    print("=" * 70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)