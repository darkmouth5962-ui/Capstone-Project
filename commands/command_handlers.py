# Command Handlers - Write Side of CQRS
# commands change state and publish events, but NEVER return data (only success/failure)

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

# simple in-memory write database (in production: PostgreSQL)
_write_db = {
    'users': {},
    'user_ingredients': {},
    'favorites': {},
    'appliances': {}
}

# USER COMMANDS

def handle_create_user(username: str, password: str, dietary_restrictions: List[str] = None) -> Dict[str, Any]:
    # creates a new user
    # returns: {'success': bool, 'user_id': str, 'message': str}
    # publishes UserCreatedEvent

    event_bus = get_event_bus()
    
    # validation
    if not username or not password:
        return {'success': False, 'message': 'Username and password required'}
    
    # check if user exists
    for user in _write_db['users'].values():
        if user['username'] == username:
            return {'success': False, 'message': 'Username already exists'}
    
    # create user
    user_id = str(uuid.uuid4())
    _write_db['users'][user_id] = {
        'user_id': user_id,
        'username': username,
        'password': password,  # In production: hash this!
        'dietary_restrictions': dietary_restrictions or [],
        'skill_level': 'beginner'
    }
    
    # publish event
    event = UserCreatedEvent(user_id, username, dietary_restrictions or [])
    event_bus.publish(event)
    
    return {
        'success': True,
        'user_id': user_id,
        'message': f'User {username} created successfully'
    }

def handle_update_user_profile(user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    # updates user profile
    # returns: {'success': bool, 'message': str}
    # publishes UserProfileUpdatedEvent

    event_bus = get_event_bus()
    
    # validation
    if user_id not in _write_db['users']:
        return {'success': False, 'message': 'User not found'}
    
    # update user
    user = _write_db['users'][user_id]
    allowed_fields = ['dietary_restrictions', 'skill_level']
    
    updated_fields = {}
    for field, value in updates.items():
        if field in allowed_fields:
            user[field] = value
            updated_fields[field] = value
    
    if not updated_fields:
        return {'success': False, 'message': 'No valid fields to update'}
    
    # publish event
    event = UserProfileUpdatedEvent(user_id, updated_fields)
    event_bus.publish(event)
    
    return {
        'success': True,
        'message': 'Profile updated successfully'
    }

# INGREDIENT COMMANDS

def handle_add_ingredient(user_id: str, ingredient_name: str, amount: float = 1.0, exp_date: str = None) -> Dict[str, Any]:
    # adds ingredient to user's pantry
    # returns: {'success': bool, 'ingredient_id': str, 'message': str}
    # publishes IngredientAddedEvent

    event_bus = get_event_bus()
    
    # validation
    if user_id not in _write_db['users']:
        return {'success': False, 'message': 'User not found'}
    
    if not ingredient_name:
        return {'success': False, 'message': 'Ingredient name required'}
    
    # initialize user's ingredient list if needed
    if user_id not in _write_db['user_ingredients']:
        _write_db['user_ingredients'][user_id] = {}
    
    # add ingredient
    ingredient_id = str(uuid.uuid4())
    _write_db['user_ingredients'][user_id][ingredient_id] = {
        'ingredient_id': ingredient_id,
        'name': ingredient_name.lower(),
        'amount': amount,
        'exp_date': exp_date
    }
    
    # publish event
    event = IngredientAddedEvent(user_id, ingredient_id, ingredient_name, amount, exp_date)
    event_bus.publish(event)
    
    return {
        'success': True,
        'ingredient_id': ingredient_id,
        'message': f'Added {ingredient_name} to pantry'
    }

def handle_remove_ingredient(user_id: str, ingredient_id: str) -> Dict[str, Any]:
    # remove ingredient from user's pantry
    # returns: {'success': bool, 'message': str}
    # publishes IngredientRemovedEvent

    event_bus = get_event_bus()
    
    # validation
    if user_id not in _write_db['users']:
        return {'success': False, 'message': 'User not found'}
    
    if user_id not in _write_db['user_ingredients'] or ingredient_id not in _write_db['user_ingredients'][user_id]:
        return {'success': False, 'message': 'Ingredient not found'}
    
    # remove ingredient
    del _write_db['user_ingredients'][user_id][ingredient_id]
    
    # publish event
    event = IngredientRemovedEvent(user_id, ingredient_id)
    event_bus.publish(event)
    
    return {
        'success': True,
        'message': 'Ingredient removed from pantry'
    }

# FAVORITE COMMANDS

def handle_favorite_recipe(user_id: str, recipe_id: str, recipe_name: str) -> Dict[str, Any]:
    # marks recipe as favorite
    # returns: {'success': bool, 'message': str}
    # publishes RecipeFavoritedEvent
    
    event_bus = get_event_bus()
    
    # validation
    if user_id not in _write_db['users']:
        return {'success': False, 'message': 'User not found'}
    
    # initialize favorites if needed
    if user_id not in _write_db['favorites']:
        _write_db['favorites'][user_id] = set()
    
    # check if already favorited
    if recipe_id in _write_db['favorites'][user_id]:
        return {'success': False, 'message': 'Recipe already favorited'}
    
    # add to favorites
    _write_db['favorites'][user_id].add(recipe_id)
    
    # publish event
    event = RecipeFavoritedEvent(user_id, recipe_id, recipe_name)
    event_bus.publish(event)
    
    return {
        'success': True,
        'message': f'Added {recipe_name} to favorites'
    }

def handle_unfavorite_recipe(user_id: str, recipe_id: str) -> Dict[str, Any]:
    # removes recipe from favorites
    # returns: {'success': bool, 'message': str}
    # publishes RecipeUnfavoritedEvent
    
    event_bus = get_event_bus()
    
    # validation
    if user_id not in _write_db['users']:
        return {'success': False, 'message': 'User not found'}
    
    if user_id not in _write_db['favorites'] or recipe_id not in _write_db['favorites'][user_id]:
        return {'success': False, 'message': 'Recipe not in favorites'}
    
    # remove from favorites
    _write_db['favorites'][user_id].remove(recipe_id)
    
    # publish event
    event = RecipeUnfavoritedEvent(user_id, recipe_id)
    event_bus.publish(event)
    
    return {
        'success': True,
        'message': 'Recipe removed from favorites'
    }

# APPLIANCE COMMANDS

def handle_update_appliances(user_id: str, appliances: List[str]) -> Dict[str, Any]:
    # updates user's available appliances
    # returns: {'success': bool, 'message': str}
    # publishes UserAppliancesUpdatedEvent
    
    event_bus = get_event_bus()
    
    # validation
    if user_id not in _write_db['users']:
        return {'success': False, 'message': 'User not found'}
    
    # update appliances
    _write_db['appliances'][user_id] = appliances
    
    # publish event
    event = UserAppliancesUpdatedEvent(user_id, appliances)
    event_bus.publish(event)
    
    return {
        'success': True,
        'message': 'Appliances updated successfully'
    }

# TRACKING COMMAND

def handle_log_recipe_search(user_id: str, ingredients: List[str], filters: Dict[str, Any], result_count: int) -> Dict[str, Any]:
    # logs that a recipe search was performed
    # returns: {'success': bool}
    # publishes RecipeSearchPerformedEvent
    
    event_bus = get_event_bus()
    
    # publish event
    event = RecipeSearchPerformedEvent(user_id, ingredients, filters, result_count)
    event_bus.publish(event)
    
    return {'success': True}