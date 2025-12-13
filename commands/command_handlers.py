# Command Handlers - Write Side of CQRS with PostgreSQL
# commands change state in database and publish events

from typing import Dict, Any, List
import uuid
from events.domain_events import (
    UserCreatedEvent,
    UserProfileUpdatedEvent,
    IngredientAddedEvent,
    IngredientRemovedEvent,
    RecipeFavoritedEvent,
    RecipeUnfavoritedEvent,
    UserAppliancesUpdatedEvent,
    RecipeSearchPerformedEvent
)
from events.event_bus import get_event_bus
from database.db_connection import execute_update, execute_query

# USER COMMANDS

def handle_create_user(username: str, password: str, dietary_restrictions: List[str] = None) -> Dict[str, Any]:
    """Creates a new user in PostgreSQL"""
    event_bus = get_event_bus()
    
    # validation
    if not username or not password:
        return {'success': False, 'message': 'Username and password required'}
    
    # check if user exists
    check_query = "SELECT u_id FROM \"user\" WHERE username = %s;"
    existing = execute_query(check_query, (username,), fetch_one=True)
    if existing:
        return {'success': False, 'message': 'Username already exists'}
    
    # create user
    user_id = str(uuid.uuid4())
    diet_str = ','.join(dietary_restrictions) if dietary_restrictions else None
    
    insert_query = """
        INSERT INTO "user" (u_id, username, password, diet, skill)
        VALUES (%s, %s, %s, %s, %s);
    """
    execute_update(insert_query, (user_id, username, password, diet_str, 'beginner'))
    
    # publish event
    event = UserCreatedEvent(user_id, username, dietary_restrictions or [])
    event_bus.publish(event)
    
    return {
        'success': True,
        'user_id': user_id,
        'message': f'User {username} created successfully'
    }

def handle_update_user_profile(user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Updates user profile in PostgreSQL"""
    event_bus = get_event_bus()
    
    # validation
    check_query = "SELECT u_id FROM \"user\" WHERE u_id = %s;"
    if not execute_query(check_query, (user_id,), fetch_one=True):
        return {'success': False, 'message': 'User not found'}
    
    # allowed fields
    allowed_fields = {'dietary_restrictions': 'diet', 'skill_level': 'skill'}
    
    updated_fields = {}
    for field, value in updates.items():
        if field in allowed_fields:
            db_field = allowed_fields[field]
            
            # Handle dietary_restrictions specially (convert list to comma-separated)
            if field == 'dietary_restrictions':
                value = ','.join(value) if isinstance(value, list) else value
            
            query = f'UPDATE "user" SET {db_field} = %s WHERE u_id = %s;'
            execute_update(query, (value, user_id))
            updated_fields[field] = value
    
    if not updated_fields:
        return {'success': False, 'message': 'No valid fields to update'}
    
    # publish event
    event = UserProfileUpdatedEvent(user_id, updated_fields)
    event_bus.publish(event)
    
    return {'success': True, 'message': 'Profile updated successfully'}

# INGREDIENT COMMANDS

def handle_add_ingredient(user_id: str, ingredient_name: str, amount: float = 1.0, exp_date: str = None) -> Dict[str, Any]:
    """Adds ingredient to user's pantry in PostgreSQL"""
    event_bus = get_event_bus()
    
    # validation
    check_user = "SELECT u_id FROM \"user\" WHERE u_id = %s;"
    if not execute_query(check_user, (user_id,), fetch_one=True):
        return {'success': False, 'message': 'User not found'}
    
    if not ingredient_name:
        return {'success': False, 'message': 'Ingredient name required'}
    
    # Get or create ingredient
    ing_name = ingredient_name.lower()
    check_ing = "SELECT i_id FROM ingredients WHERE name = %s;"
    ingredient = execute_query(check_ing, (ing_name,), fetch_one=True)
    
    if not ingredient:
        # Create ingredient if doesn't exist
        insert_ing = "INSERT INTO ingredients (name, cpu, unit) VALUES (%s, 0.00, 'each') RETURNING i_id;"
        ingredient = execute_query(insert_ing, (ing_name,), fetch_one=True)
        execute_update("COMMIT;")
    
    i_id = ingredient['i_id']
    
    # Add to user's pantry (or update if exists)
    insert_pantry = """
        INSERT INTO has_ingredient (u_id, i_id, amt, exp_date)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (u_id, i_id) DO UPDATE SET amt = EXCLUDED.amt, exp_date = EXCLUDED.exp_date;
    """
    execute_update(insert_pantry, (user_id, i_id, amount, exp_date))
    
    ingredient_id = str(i_id)  # Convert to string for consistency with events
    
    # publish event
    event = IngredientAddedEvent(user_id, ingredient_id, ing_name, amount, exp_date)
    event_bus.publish(event)
    
    return {
        'success': True,
        'ingredient_id': ingredient_id,
        'message': f'Added {ing_name} to pantry'
    }

def handle_remove_ingredient(user_id: str, ingredient_id: str) -> Dict[str, Any]:
    """Remove ingredient from user's pantry in PostgreSQL"""
    event_bus = get_event_bus()
    
    # Try to delete
    delete_query = "DELETE FROM has_ingredient WHERE u_id = %s AND i_id = %s;"
    rows = execute_update(delete_query, (user_id, int(ingredient_id)))
    
    if rows == 0:
        return {'success': False, 'message': 'Ingredient not found in pantry'}
    
    # publish event
    event = IngredientRemovedEvent(user_id, ingredient_id)
    event_bus.publish(event)
    
    return {'success': True, 'message': 'Ingredient removed from pantry'}

# FAVORITE COMMANDS

def handle_favorite_recipe(user_id: str, recipe_id: str, recipe_name: str) -> Dict[str, Any]:
    """Marks recipe as favorite in PostgreSQL"""
    event_bus = get_event_bus()
    
    # Insert favorite (ignore if already exists)
    insert_fav = """
        INSERT INTO favorite (u_id, r_id)
        VALUES (%s, %s)
        ON CONFLICT (u_id, r_id) DO NOTHING;
    """
    rows = execute_update(insert_fav, (user_id, int(recipe_id)))
    
    if rows == 0:
        return {'success': False, 'message': 'Recipe already favorited'}
    
    # publish event
    event = RecipeFavoritedEvent(user_id, recipe_id, recipe_name)
    event_bus.publish(event)
    
    return {'success': True, 'message': f'Added {recipe_name} to favorites'}

def handle_unfavorite_recipe(user_id: str, recipe_id: str) -> Dict[str, Any]:
    """Removes recipe from favorites in PostgreSQL"""
    event_bus = get_event_bus()
    
    delete_fav = "DELETE FROM favorite WHERE u_id = %s AND r_id = %s;"
    rows = execute_update(delete_fav, (user_id, int(recipe_id)))
    
    if rows == 0:
        return {'success': False, 'message': 'Recipe not in favorites'}
    
    # publish event
    event = RecipeUnfavoritedEvent(user_id, recipe_id)
    event_bus.publish(event)
    
    return {'success': True, 'message': 'Recipe removed from favorites'}

# APPLIANCE COMMANDS

def handle_update_appliances(user_id: str, appliances: List[str]) -> Dict[str, Any]:
    """Updates user's available appliances in PostgreSQL"""
    event_bus = get_event_bus()
    
    # Clear existing appliances
    delete_query = "DELETE FROM has_app WHERE u_id = %s;"
    execute_update(delete_query, (user_id,))
    
    # Insert new appliances
    if appliances:
        # Ensure appliances exist in appliance table
        for app_name in appliances:
            app_lower = app_name.lower()
            ensure_app = """
                INSERT INTO appliance (name)
                VALUES (%s)
                ON CONFLICT (name) DO NOTHING;
            """
            execute_update(ensure_app, (app_lower,))
            
            # Add to user's appliances
            insert_has = """
                INSERT INTO has_app (name, u_id)
                VALUES (%s, %s)
                ON CONFLICT (name, u_id) DO NOTHING;
            """
            execute_update(insert_has, (app_lower, user_id))
    
    # publish event
    event = UserAppliancesUpdatedEvent(user_id, appliances)
    event_bus.publish(event)
    
    return {'success': True, 'message': 'Appliances updated successfully'}

# TRACKING COMMAND

def handle_log_recipe_search(user_id: str, ingredients: List[str], filters: Dict[str, Any], result_count: int) -> Dict[str, Any]:
    """Logs that a recipe search was performed"""
    event_bus = get_event_bus()
    
    # publish event (analytics tracking)
    event = RecipeSearchPerformedEvent(user_id, ingredients, filters, result_count)
    event_bus.publish(event)
    
    return {'success': True}