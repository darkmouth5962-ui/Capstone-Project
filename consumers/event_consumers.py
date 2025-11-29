# Event Consumers - Subscribe to events and update read model
# bridge between write side and read side in CQRS+EDA

from events.event_bus import get_event_bus
from queries.query_handlers import get_read_db

def setup_event_consumers():
    # set up all event consumers
    # subscribers update the read model asynchronously
    
    event_bus = get_event_bus()
    read_db = get_read_db()
    
    # USER EVENT CONSUMERS
    
    def on_user_created(event_data):
        # update read model when user is created
        user_id = event_data['data']['user_id']
        read_db['user_profiles'][user_id] = {
            'user_id': user_id,
            'username': event_data['data']['username'],
            'dietary_restrictions': event_data['data']['dietary_restrictions'],
            'skill_level': 'beginner'
        }
        read_db['user_pantries'][user_id] = {}
        read_db['user_favorites'][user_id] = set()
        print(f"Read model updated: User {event_data['data']['username']} profile created")
    
    def on_user_profile_updated(event_data):
        # update read model when user profile changes
        user_id = event_data['data']['user_id']
        if user_id in read_db['user_profiles']:
            read_db['user_profiles'][user_id].update(event_data['data']['updated_fields'])
            print(f"Read model updated: User {user_id} profile updated")
    
    # INGREDIENT EVENT CONSUMERS
    
    def on_ingredient_added(event_data):
        # update read model when ingredient is added
        user_id = event_data['data']['user_id']
        ingredient_id = event_data['data']['ingredient_id']
        
        if user_id not in read_db['user_pantries']:
            read_db['user_pantries'][user_id] = {}
        
        read_db['user_pantries'][user_id][ingredient_id] = {
            'ingredient_id': ingredient_id,
            'name': event_data['data']['ingredient_name'].lower(),
            'amount': event_data['data']['amount'],
            'exp_date': event_data['data'].get('exp_date')
        }
        print(f"Read model updated: Ingredient {event_data['data']['ingredient_name']} added to pantry")
    
    def on_ingredient_removed(event_data):
        # Update read model when ingredient is removed
        user_id = event_data['data']['user_id']
        ingredient_id = event_data['data']['ingredient_id']
        
        if user_id in read_db['user_pantries'] and ingredient_id in read_db['user_pantries'][user_id]:
            del read_db['user_pantries'][user_id][ingredient_id]
            print(f"Read model updated: Ingredient removed from pantry")
    
    # FAVORITE EVENT CONSUMERS
    
    def on_recipe_favorited(event_data):
        # update read model when recipe is favorited
        user_id = event_data['data']['user_id']
        recipe_id = event_data['data']['recipe_id']
        
        if user_id not in read_db['user_favorites']:
            read_db['user_favorites'][user_id] = set()
        
        read_db['user_favorites'][user_id].add(str(recipe_id))
        print(f"Read model updated: Recipe {event_data['data']['recipe_name']} favorited")
    
    def on_recipe_unfavorited(event_data):
        # update read model when recipe is unfavorited
        user_id = event_data['data']['user_id']
        recipe_id = event_data['data']['recipe_id']
        
        if user_id in read_db['user_favorites']:
            read_db['user_favorites'][user_id].discard(str(recipe_id))
            print(f"Read model updated: Recipe unfavorited")
    
    # TRACKING EVENT CONSUMERS
    
    def on_recipe_search_performed(event_data):
        # Track recipe searches for logging
        user_id = event_data['data']['user_id']
        
        if user_id not in read_db['user_analytics']:
            read_db['user_analytics'][user_id] = {
                'search_count': 0,
                'recent_searches': []
            }
        
        read_db['user_analytics'][user_id]['search_count'] += 1
        read_db['user_analytics'][user_id]['recent_searches'].append({
            'timestamp': event_data['timestamp'],
            'ingredients': event_data['data']['ingredients'],
            'result_count': event_data['data']['result_count']
        })
        
        # keep only last 10 searches
        if len(read_db['user_analytics'][user_id]['recent_searches']) > 10:
            read_db['user_analytics'][user_id]['recent_searches'].pop(0)
        
        print(f"Analytics updated: Recipe search logged")
    
    # SUBSCRIBE TO EVENTS
    
    event_bus.subscribe('USER_CREATED', on_user_created)
    event_bus.subscribe('USER_PROFILE_UPDATED', on_user_profile_updated)
    event_bus.subscribe('INGREDIENT_ADDED', on_ingredient_added)
    event_bus.subscribe('INGREDIENT_REMOVED', on_ingredient_removed)
    event_bus.subscribe('RECIPE_FAVORITED', on_recipe_favorited)
    event_bus.subscribe('RECIPE_UNFAVORITED', on_recipe_unfavorited)
    event_bus.subscribe('RECIPE_SEARCH_PERFORMED', on_recipe_search_performed)
    
    print("\n" + "=" * 70)
    print("Event Consumers Initialized")
    print("=" * 70)