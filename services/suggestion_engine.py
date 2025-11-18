from services.recipe_matcher import find_partial_matches, calculate_match, passes_filters

def generate_shopping_suggestions(user_ingredients, recipes, filters=None, top_n=5, has_matches=True, exclude_ids=None):
    # analyzes which ingredients would unlock the most new recipes
    # this is the "shopping mode" feature
    # will return a list of suggested ingredients with unlock counts
    # analyzes which ingredients would unlock the most new recipes.
    # uses different strategies based on whether ANY matches exist.
    
    # track how many recipes each missing ingredient appears in
    if exclude_ids is None:
        exclude_ids = set()
    
    ingredient_impact = {}
    
    if has_matches:
        # Strategy 1: User has SOME matches - look for close recipes (50%+)
        # This helps them unlock recipes they're almost ready for
        partial_matches = find_partial_matches(
            user_ingredients, 
            recipes, 
            filters, 
            min_match_threshold=50,
            exclude_ids=exclude_ids  # ← Exclude already-shown recipes
        )
        
        # If even 50% threshold returns nothing, lower it
        if not partial_matches:
            partial_matches = find_partial_matches(
                user_ingredients, 
                recipes, 
                filters, 
                min_match_threshold=25,
                exclude_ids=exclude_ids  # ← Still exclude them
            )
    
    else:
        # Strategy 2: User has ZERO matches - analyze ALL filtered recipes
        # Find ingredients that appear most frequently across all recipes
        # This helps them build toward SOMETHING cookable
        
        print("\n💡 Analyzing ALL recipes to find the most useful ingredients...")
        
        partial_matches = []
        for recipe in recipes:
            # Skip recipes already shown (though this shouldn't happen with zero matches)
            if recipe['id'] in exclude_ids:
                continue
            
            # Still apply filters (dietary restrictions are important!)
            if not passes_filters(recipe, filters):
                continue
            
            # Don't care about match percentage - just grab the recipe
            match_data = calculate_match(recipe['ingredients'], user_ingredients)
            
            partial_matches.append({
                'id': recipe['id'],
                'name': recipe['name'],
                'match_percentage': match_data['percentage'],
                'matched_ingredients': match_data['matched'],
                'missing_ingredients': match_data['missing'],
                'total_time': recipe.get('total_time', 0),
                'skill_level': recipe.get('skill_level', 'unknown'),
                'cuisine': recipe.get('cuisine', 'unknown')
            })
    
    # Now count missing ingredient frequency across our candidate recipes
    for recipe in partial_matches:
        for missing_ing in recipe['missing_ingredients']:
            if missing_ing not in ingredient_impact:
                ingredient_impact[missing_ing] = {
                    'name': missing_ing,
                    'unlock_count': 0,
                    'recipe_names': []
                }
            
            ingredient_impact[missing_ing]['unlock_count'] += 1
            ingredient_impact[missing_ing]['recipe_names'].append(recipe['name'])
    
    # Convert to list and sort by unlock count
    suggestions = list(ingredient_impact.values())
    suggestions.sort(key=lambda x: x['unlock_count'], reverse=True)
    
    return suggestions[:top_n]

def display_suggestions(suggestions, partial_matches=None):
    # displays shopping suggestions and partial matches

    print("\n" + "=" * 70)
    print(" SMART SHOPPING SUGGESTIONS")
    print("=" * 70)
    
    if not suggestions:
        print("\n   No suggestions available - you might need more ingredients!")
        print("   Try adding some common items like eggs, butter, or garlic.\n")
        return
    
    print("\n Get these ingredients to unlock more recipes:\n")
    
    for i, suggestion in enumerate(suggestions, 1):
        unlock_text = "recipe" if suggestion['unlock_count'] == 1 else "recipes"
        print(f"{i}. {suggestion['name'].upper()}")
        print(f"   Unlocks: {suggestion['unlock_count']} {unlock_text}")
        
        # Show first 3 recipes it unlocks
        recipe_preview = suggestion['recipe_names'][:3]
        if len(suggestion['recipe_names']) > 3:
            recipe_preview.append(f"...and {len(suggestion['recipe_names']) - 3} more")
        
        print(f"   Recipes: {', '.join(recipe_preview)}")
        print()
    
    # optionally show partial matches
    if partial_matches:
        print("\n" + "=" * 70)
        print("🔍 RECIPES YOU'RE CLOSE TO MAKING")
        print("=" * 70)
        print(f"\nFound {len(partial_matches)} recipes you're almost ready for:\n")
        
        for i, recipe in enumerate(partial_matches[:5], 1):  # Show top 5
            bars = "█" * int(recipe['match_percentage'] / 10)
            empty_bars = "░" * (10 - int(recipe['match_percentage'] / 10))
            
            print(f"{i}. {recipe['name']}")
            print(f"   Progress: [{bars}{empty_bars}] {recipe['match_percentage']}%")
            print(f"   You have: {', '.join(recipe['matched_ingredients'])}")
            print(f"   Still need: {', '.join(recipe['missing_ingredients'])}")
            print()