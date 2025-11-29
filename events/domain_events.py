# Domain Events for SmartFridge
# events are published to the event bus

from datetime import datetime
from typing import List, Dict, Any

class DomainEvent:
    # base class for all domain events
    def __init__(self, event_type: str, data: Dict[str, Any]):
        self.event_type = event_type
        self.data = data
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self):
        return {
            'event_type': self.event_type,
            'data': self.data,
            'timestamp': self.timestamp
        }

# USER EVENTS

class UserCreatedEvent(DomainEvent):
    # Published when a new user registers
    def __init__(self, user_id: str, username: str, dietary_restrictions: List[str]):
        super().__init__('USER_CREATED', {
            'user_id': user_id,
            'username': username,
            'dietary_restrictions': dietary_restrictions
        })

class UserProfileUpdatedEvent(DomainEvent):
    # Published when user profile is updated
    def __init__(self, user_id: str, updated_fields: Dict[str, Any]):
        super().__init__('USER_PROFILE_UPDATED', {
            'user_id': user_id,
            'updated_fields': updated_fields
        })

# INGREDIENT EVENTS

class IngredientAddedEvent(DomainEvent):
    # published when user adds ingredient to pantry
    def __init__(self, user_id: str, ingredient_id: str, ingredient_name: str, amount: float, exp_date: str = None):
        super().__init__('INGREDIENT_ADDED', {
            'user_id': user_id,
            'ingredient_id': ingredient_id,
            'ingredient_name': ingredient_name,
            'amount': amount,
            'exp_date': exp_date
        })

class IngredientRemovedEvent(DomainEvent):
    # published when user removes ingredient from pantry
    def __init__(self, user_id: str, ingredient_id: str):
        super().__init__('INGREDIENT_REMOVED', {
            'user_id': user_id,
            'ingredient_id': ingredient_id
        })

# RECIPE EVENTS

class RecipeSearchPerformedEvent(DomainEvent):
    # published when user searches for recipes
    def __init__(self, user_id: str, ingredients: List[str], filters: Dict[str, Any], result_count: int):
        super().__init__('RECIPE_SEARCH_PERFORMED', {
            'user_id': user_id,
            'ingredients': ingredients,
            'filters': filters,
            'result_count': result_count
        })

class RecipeFavoritedEvent(DomainEvent):
    # published when user favorites a recipe
    def __init__(self, user_id: str, recipe_id: str, recipe_name: str):
        super().__init__('RECIPE_FAVORITED', {
            'user_id': user_id,
            'recipe_id': recipe_id,
            'recipe_name': recipe_name
        })

class RecipeUnfavoritedEvent(DomainEvent):
    # published when user removes recipe from favorites
    def __init__(self, user_id: str, recipe_id: str):
        super().__init__('RECIPE_UNFAVORITED', {
            'user_id': user_id,
            'recipe_id': recipe_id
        })

# APPLIANCE EVENTS

class UserAppliancesUpdatedEvent(DomainEvent):
    # published when user updates their available appliances
    def __init__(self, user_id: str, appliances: List[str]):
        super().__init__('USER_APPLIANCES_UPDATED', {
            'user_id': user_id,
            'appliances': appliances
        })