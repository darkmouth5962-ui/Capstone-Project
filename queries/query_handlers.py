# Query Handlers - Read Side of CQRS
# queries retrieve state but never change it

from typing import Dict, Any, List, Optional
import json

# read database
# updated by event consumers, not queries
_read_db = {
    'user_profiles': {},      # denormalized user data
    'user_pantries': {},      # user ingredients with metadata
    'user_favorites': {},     # user's favorited recipes with match %
    'recipe_cache': {},       # pre-aggregated recipe data
    'user_analytics': {}      # user search history
}

# load base recipe data
def _load_base_recipes():
    # load recipes from JSON file into read cache
    try:
        with open('recipes.json', 'r') as f:
            data = json.load(f)
            for recipe in data['recipes']:
                _read_db['recipe_cache'][str(recipe['id'])] = recipe
    except FileNotFoundError:
        print("  recipes.json not found, read model empty")

_load_base_recipes()

# USER QUERIES

def query_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    # QUERY: get user profile
    # Returns: user profile dict or None
    
    return _read_db['user_profiles'].get(user_id)

def query_user_pantry(user_id: str) -> List[Dict[str, Any]]:
    # QUERY: get all ingredients in user's pantry
    # Returns: list of ingredient dicts
    
    if user_id not in _read_db['user_pantries']:
        return []
    
    return list(_read_db['user_pantries'][user_id].values())

# RECIPE QUERIES

def query_recipe_by_id(recipe_id: str) -> Optional[Dict[str, Any]]:
    # QUERY: get single recipe by ID
    # Returns: recipe dict or None
    
    return _read_db['recipe_cache'].get(recipe_id)

def query_recipes_by_ingredients(ingredient_names: List[str], filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    # QUERY: search recipes by ingredients with filters
    # Returns: list of recipes ranked by match percentage
    
    filters = filters or {}
    results = []
    
    # normalize ingredient names
    user_ingredients = [ing.lower().strip() for ing in ingredient_names]
    
    # search through cached recipes
    for recipe in _read_db['recipe_cache'].values():
        # apply filters
        if not _passes_filters(recipe, filters):
            continue
        
        # calculate match
        match_data = _calculate_match(recipe['ingredients'], user_ingredients)
        
        if match_data['percentage'] > 0:
            results.append({
                'id': recipe['id'],
                'name': recipe['name'],
                'match_percentage': match_data['percentage'],
                'matched_ingredients': match_data['matched'],
                'missing_ingredients': match_data['missing'],
                'prep_time': recipe.get('prep_time', 0),
                'cook_time': recipe.get('cook_time', 0),
                'total_time': recipe.get('total_time', 0),
                'servings': recipe.get('servings', 0),
                'skill_level': recipe.get('skill_level', 'unknown'),
                'cuisine': recipe.get('cuisine', 'unknown'),
                'dietary_tags': recipe.get('dietary_tags', []),
                'equipment': recipe.get('equipment', [])
            })
    
    # sort by match percentage
    results.sort(key=lambda x: x['match_percentage'], reverse=True)
    
    return results

def query_user_favorites(user_id: str) -> List[Dict[str, Any]]:
    # QUERY: get user's favorite recipes with current match percentages
    # Returns: list of favorited recipes
    
    if user_id not in _read_db['user_favorites']:
        return []
    
    favorites = []
    user_pantry = query_user_pantry(user_id)
    user_ingredients = [ing['name'] for ing in user_pantry]
    
    for recipe_id in _read_db['user_favorites'][user_id]:
        recipe = _read_db['recipe_cache'].get(recipe_id)
        if recipe:
            match_data = _calculate_match(recipe['ingredients'], user_ingredients)
            favorites.append({
                'id': recipe['id'],
                'name': recipe['name'],
                'match_percentage': match_data['percentage'],
                'matched_ingredients': match_data['matched'],
                'missing_ingredients': match_data['missing']
            })
    
    return favorites

def query_shopping_suggestions(user_id: str, filters: Dict[str, Any] = None, top_n: int = 5) -> List[Dict[str, Any]]:
    # QUERY: get shopping suggestions based on current pantry
    # Returns: list of suggested ingredients with unlock counts
    
    filters = filters or {}
    user_pantry = query_user_pantry(user_id)
    user_ingredients = [ing['name'] for ing in user_pantry]
    
    # track ingredient impact
    ingredient_impact = {}
    
    for recipe in _read_db['recipe_cache'].values():
        if not _passes_filters(recipe, filters):
            continue
        
        match_data = _calculate_match(recipe['ingredients'], user_ingredients)
        
        # consider recipes 50%+ matched
        if 50 <= match_data['percentage'] < 100:
            for missing_ing in match_data['missing']:
                if missing_ing not in ingredient_impact:
                    ingredient_impact[missing_ing] = {
                        'name': missing_ing,
                        'unlock_count': 0,
                        'recipes': []
                    }
                ingredient_impact[missing_ing]['unlock_count'] += 1
                ingredient_impact[missing_ing]['recipes'].append(recipe['name'])
    
    # sort and limit
    suggestions = sorted(ingredient_impact.values(), key=lambda x: x['unlock_count'], reverse=True)
    return suggestions[:top_n]

# HELPER FUNCTIONS

def _calculate_match(recipe_ingredients: List[str], user_ingredients: List[str]) -> Dict[str, Any]:
    # calculate match percentage between recipe and user ingredients
    lower_recipe = [ing.lower() for ing in recipe_ingredients]
    matched = [ing for ing in lower_recipe if ing in user_ingredients]
    missing = [ing for ing in lower_recipe if ing not in user_ingredients]
    
    total = len(lower_recipe)
    percentage = (len(matched) / total * 100) if total > 0 else 0
    
    return {
        'percentage': round(percentage, 1),
        'matched': matched,
        'missing': missing
    }

def _passes_filters(recipe: Dict[str, Any], filters: Dict[str, Any]) -> bool:
    # Check if recipe passes all filters
    if 'max_time' in filters and recipe.get('total_time', 999) > filters['max_time']:
        return False
    
    if 'skill_level' in filters and recipe.get('skill_level', '').lower() != filters['skill_level'].lower():
        return False
    
    if 'dietary_tags' in filters:
        recipe_tags = [tag.lower() for tag in recipe.get('dietary_tags', [])]
        required = [tag.lower() for tag in filters['dietary_tags']]
        if not all(tag in recipe_tags for tag in required):
            return False
    
    if 'cuisine' in filters and recipe.get('cuisine', '').lower() != filters['cuisine'].lower():
        return False
    
    return True

# READ MODEL ACCESS (for debug)

def get_read_db():
    # get the entire read database (for debugging/testing)
    return _read_db