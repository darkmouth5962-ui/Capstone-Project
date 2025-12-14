# Query Handlers - Read Side of CQRS with PostgreSQL
from typing import Dict, Any, List, Optional
from database.db_connection import execute_query
import sys
import os

try:
    from queries.dietary_restrictions import check_recipe_compatibility
    DIETARY_FILTERING_AVAILABLE = True
    print(" Dietary restrictions module loaded successfully")
except ImportError as e:
    print(f"  Warning: Dietary restrictions module not available: {e}")
    DIETARY_FILTERING_AVAILABLE = False
    def check_recipe_compatibility(ingredients, restrictions):
        return True, []  # No filtering if module unavailable

def query_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    # QUERY: get user profile from PostgreSQL
    query = """
        SELECT u_id, username, skill, diet
        FROM "user"
        WHERE u_id = %s;
    """
    result = execute_query(query, (user_id,), fetch_one=True)
    
    if result:
        # convert diet string back to list
        diet_list = result['diet'].split(',') if result.get('diet') else []
        return {
            'user_id': result['u_id'],
            'username': result['username'],
            'skill_level': result['skill'],
            'dietary_restrictions': diet_list
        }
    return None

def query_user_pantry(user_id: str) -> List[Dict[str, Any]]:
    # QUERY: get all ingredients in user's pantry from PostgreSQL
    query = """
        SELECT hi.i_id as ingredient_id, i.name, hi.amt as amount, hi.exp_date
        FROM has_ingredient hi
        JOIN ingredients i ON hi.i_id = i.i_id
        WHERE hi.u_id = %s;
    """
    results = execute_query(query, (user_id,), fetch_all=True)
    
    return [
        {
            'ingredient_id': str(r['ingredient_id']),
            'name': r['name'],
            'amount': float(r['amount']) if r['amount'] else 1.0,
            'exp_date': str(r['exp_date']) if r['exp_date'] else None
        }
        for r in (results or [])
    ]

def query_recipe_by_id(recipe_id: str) -> Optional[Dict[str, Any]]:
    # QUERY: get single recipe by ID with full details from PostgreSQL
    # get recipe basic info
    recipe_query = """
        SELECT r_id, name, "desc", time, skill, serving
        FROM recipe
        WHERE r_id = %s;
    """
    recipe = execute_query(recipe_query, (int(recipe_id),), fetch_one=True)
    
    if not recipe:
        return None
    
    # get ingredients
    ing_query = """
        SELECT i.name
        FROM uses_ingredient ui
        JOIN ingredients i ON ui.i_id = i.i_id
        WHERE ui.r_id = %s
        ORDER BY i.name;
    """
    ingredients = execute_query(ing_query, (int(recipe_id),), fetch_all=True)
    
    # get equipment
    equip_query = """
        SELECT a.name
        FROM uses u
        JOIN appliance a ON u.name = a.name
        WHERE u.r_id = %s
        ORDER BY a.name;
    """
    equipment = execute_query(equip_query, (int(recipe_id),), fetch_all=True)
    
    # get steps/instructions
    steps_query = """
        SELECT num as step, "desc" as instruction, time
        FROM step
        WHERE r_id = %s
        ORDER BY num;
    """
    steps = execute_query(steps_query, (int(recipe_id),), fetch_all=True)
    
    # determine dietary tags
    dietary_tags = []
    if recipe.get('desc'):
        desc_lower = recipe['desc'].lower()
        if 'vegetarian' in desc_lower:
            dietary_tags.append('vegetarian')
        if 'vegan' in desc_lower:
            dietary_tags.append('vegan')
    
    return {
        'id': recipe['r_id'],
        'name': recipe['name'],
        'description': recipe.get('desc', ''),
        'prep_time': recipe.get('time', 0) // 2,  # Estimate
        'cook_time': recipe.get('time', 0) // 2,
        'total_time': recipe.get('time', 0),
        'servings': recipe.get('serving', 1),
        'skill_level': recipe.get('skill', 'beginner'),
        'cuisine': recipe.get('desc', ''),  # Using desc as cuisine for now
        'dietary_tags': dietary_tags,
        'ingredients': [i['name'] for i in (ingredients or [])],
        'equipment': [e['name'] for e in (equipment or [])],
        'instructions': [
            {
                'step': s['step'],
                'instruction': s['instruction'],
                'time': s.get('time', 0),
                'ingredients_needed': []  # would need additional query to match ingredients to steps
            }
            for s in (steps or [])
        ]
    }

def query_recipes_by_ingredients(ingredient_names: List[str], filters: Dict[str, Any] = None, user_id: str = None) -> List[Dict[str, Any]]:
    """
    QUERY: search recipes by ingredients with automatic dietary restriction filtering
    
    Args:
        ingredient_names: List of ingredient names to search
        filters: Optional dict with max_time, skill_level, cuisine
        user_id: User ID to automatically apply their dietary restrictions
    
    Returns:
        Dict with 'compatible' recipes and 'filtered' recipes (with violation info)
    """
    filters = filters or {}
    compatible_results = []
    filtered_results = []
    
    # get user's dietary restrictions if user_id provided
    user_dietary_restrictions = []
    if user_id and DIETARY_FILTERING_AVAILABLE:
        user_query = "SELECT diet FROM \"user\" WHERE u_id = %s;"
        user_result = execute_query(user_query, (user_id,), fetch_one=True)
        if user_result and user_result.get('diet'):
            # diet is stored as comma-separated string
            user_dietary_restrictions = [d.strip() for d in user_result['diet'].split(',') if d.strip()]
            print(f"🍽️ Applying dietary restrictions for user {user_id}: {', '.join(user_dietary_restrictions)}")
    
    # normalize ingredient names
    user_ingredients = [ing.lower().strip() for ing in ingredient_names]
    
    # base query to get all recipes
    base_query = """
        SELECT DISTINCT r.r_id as id, r.name, r."desc", r.time as total_time, 
               r.skill as skill_level, r.serving as servings
        FROM recipe r
        WHERE 1=1
    """
    
    params = []
    
    # apply filters
    if 'max_time' in filters and filters['max_time']:
        base_query += " AND r.time <= %s"
        params.append(filters['max_time'])
    
    if 'skill_level' in filters and filters['skill_level']:
        base_query += " AND LOWER(r.skill) = LOWER(%s)"
        params.append(filters['skill_level'])
    
    if 'cuisine' in filters and filters['cuisine']:
        base_query += " AND LOWER(r.\"desc\") LIKE LOWER(%s)"
        params.append(f"%{filters['cuisine']}%")
    
    base_query += " ORDER BY r.name;"
    
    recipes = execute_query(base_query, tuple(params), fetch_all=True)
    
    # for each recipe, calculate match and check dietary restrictions
    filtered_count = 0
    for recipe in (recipes or []):
        r_id = recipe['id']
        
        # get recipe ingredients
        ing_query = """
            SELECT i.name
            FROM uses_ingredient ui
            JOIN ingredients i ON ui.i_id = i.i_id
            WHERE ui.r_id = %s;
        """
        recipe_ings = execute_query(ing_query, (r_id,), fetch_all=True)
        recipe_ing_names = [i['name'].lower() for i in (recipe_ings or [])]
        
        # apply dietary restriction filtering
        is_compatible = True
        violations = []
        
        if user_dietary_restrictions and recipe_ing_names and DIETARY_FILTERING_AVAILABLE:
            is_compatible, violations = check_recipe_compatibility(
                recipe_ing_names,
                user_dietary_restrictions
            )
            
            if not is_compatible:
                filtered_count += 1
                print(f"   ❌ Filtering out '{recipe['name']}': {[v['reason'] for v in violations]}")
        
        # get equipment
        equip_query = """
            SELECT a.name
            FROM uses u
            JOIN appliance a ON u.name = a.name
            WHERE u.r_id = %s;
        """
        equipment = execute_query(equip_query, (r_id,), fetch_all=True)
        
        # calculate match
        matched = [ing for ing in recipe_ing_names if ing in user_ingredients]
        missing = [ing for ing in recipe_ing_names if ing not in user_ingredients]
        
        total = len(recipe_ing_names)
        percentage = (len(matched) / total * 100) if total > 0 else 0
        
        if percentage > 0:
            recipe_data = {
                'id': r_id,
                'name': recipe['name'],
                'match_percentage': round(percentage, 1),
                'matched_ingredients': matched,
                'missing_ingredients': missing,
                'prep_time': recipe.get('total_time', 0) // 2,
                'cook_time': recipe.get('total_time', 0) // 2,
                'total_time': recipe.get('total_time', 0),
                'servings': recipe.get('servings', 1),
                'skill_level': recipe.get('skill_level', 'beginner'),
                'cuisine': recipe.get('desc', ''),
                'dietary_tags': [],
                'equipment': [e['name'] for e in (equipment or [])]
            }
            
            if is_compatible:
                compatible_results.append(recipe_data)
            else:
                # Add violation info for filtered recipes
                recipe_data['violations'] = [
                    {
                        'ingredient': v['ingredient'],
                        'restriction': v['restriction']
                    }
                    for v in violations
                ]
                filtered_results.append(recipe_data)
    
    # sort compatible results by match percentage
    compatible_results.sort(key=lambda x: x['match_percentage'], reverse=True)
    
    # sort filtered results by match percentage too
    filtered_results.sort(key=lambda x: x['match_percentage'], reverse=True)
    
    if filtered_count > 0:
        print(f" Filtered out {filtered_count} recipes due to dietary restrictions")
    
    return {
        'compatible': compatible_results,
        'filtered': filtered_results,
        'dietary_restrictions': user_dietary_restrictions
    }

def query_user_favorites(user_id: str) -> List[Dict[str, Any]]:
    # QUERY: get user's favorite recipes from PostgreSQL
    query = """
        SELECT r.r_id as id, r.name
        FROM favorite f
        JOIN recipe r ON f.r_id = r.r_id
        WHERE f.u_id = %s;
    """
    favorites = execute_query(query, (user_id,), fetch_all=True)
    
    # get current pantry for match calculation
    user_pantry = query_user_pantry(user_id)
    user_ingredients = [ing['name'] for ing in user_pantry]
    
    results = []
    for fav in (favorites or []):
        # get recipe ingredients for match calculation
        recipe = query_recipe_by_id(str(fav['id']))
        if recipe:
            matched = [ing for ing in recipe['ingredients'] if ing in user_ingredients]
            missing = [ing for ing in recipe['ingredients'] if ing not in user_ingredients]
            total = len(recipe['ingredients'])
            percentage = (len(matched) / total * 100) if total > 0 else 0
            
            results.append({
                'id': fav['id'],
                'name': fav['name'],
                'match_percentage': round(percentage, 1),
                'matched_ingredients': matched,
                'missing_ingredients': missing
            })
    
    return results

def query_shopping_suggestions(user_id: str, filters: Dict[str, Any] = None, top_n: int = 5) -> List[Dict[str, Any]]:
    # QUERY: get shopping suggestions based on current pantry from PostgreSQL
    filters = filters or {}
    
    user_pantry = query_user_pantry(user_id)
    user_ingredients = [ing['name'] for ing in user_pantry]
    
    # get all recipes
    all_recipes = query_recipes_by_ingredients(user_ingredients, filters)
    
    # track ingredient impact
    ingredient_impact = {}
    
    for recipe in all_recipes:
        # consider recipes 50%+ matched
        if 50 <= recipe['match_percentage'] < 100:
            for missing_ing in recipe['missing_ingredients']:
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