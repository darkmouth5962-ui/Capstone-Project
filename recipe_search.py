import json

def parse_ingredients(raw_input):
    # accepts comma-separated or newline-separated ingredients
    # returns a clean list of ingredients

    # splitter; on commas or newlines
    ingredients = raw_input.replace('\n', ',').split(',')

    # normalize list: lowercase and strip whitespace
    cleaned = [ing.strip().lower() for ing in ingredients if ing.strip()]

    return cleaned

def load_recipes():
    # Load recipes from a JSON file
    with open('recipes.json', 'r') as file:
        data = json.load(file)
    return data['recipes']

def calculate_match(recipe_ingredients, user_ingredients):
    # calculates how well a recipe matches the user's ingredients
    # returns match percentage, matched ingredients and missing ingredients

    # normalize
    lower_rec_ings = [ing.lower() for ing in recipe_ingredients]

    # ingredient lists
    matched = []
    missing = []

    # check each recipe ingredient
    for recipe_ing in lower_rec_ings:
        if recipe_ing in user_ingredients:
            matched.append(recipe_ing)
        else:
            missing.append(recipe_ing)

    # calculate precentage
    total = len(lower_rec_ings)
    match_count = len(matched)
    percentage = (match_count/total*100) if total > 0 else 0

    return {
        'percentage': round(percentage, 1),
        'matched': matched,
        'missing': missing
    }

def passes_filters(recipe, filters):
    #check if a recipe passes all specified filters
    if not filters:
        return True
    
    # filter by maximum time
    if 'max_time' in filters and filters['max_time']:
        if recipe.get('total_time', 999) > filters['max_time']:
            return False
    
    # filter by skill level
    if 'skill_level' in filters and filters['skill_level']:
        if recipe.get('skill_level', '').lower() != filters['skill_level'].lower():
            return False
    
    # filter by dietary tags (recipe must have ALL specified tags)
    if 'dietary_tags' in filters and filters['dietary_tags']:
        recipe_tags = [tag.lower() for tag in recipe.get('dietary_tags', [])]
        required_tags = [tag.lower() for tag in filters['dietary_tags']]
        
        for required_tag in required_tags:
            if required_tag not in recipe_tags:
                return False
    
    # filter by cuisine
    if 'cuisine' in filters and filters['cuisine']:
        if recipe.get('cuisine', '').lower() != filters['cuisine'].lower():
            return False
    
    return True

def search_recipes(user_ingredients, recipes, filters=None):
    # searches through recipes and ranks them by match percentage
    results = []

    for recipe in recipes:
        # first check if recipe passes filters
        if not passes_filters(recipe, filters):
            continue
        
        # then calculate ingredient match
        match_data = calculate_match(recipe['ingredients'], user_ingredients)
        
        # only include recipes with at least some match
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

    # sort by match percentage descending
    results.sort(key=lambda x: x['match_percentage'], reverse=True)

    return results
"""SUGGESTION ENGINE FUNCTIONS"""
def find_partial_matches(user_ingredients, recipes, filters=None, min_match_threshold=50, exclude_ids=None):
    # finds recipes that partially match user ingredients.
    # "almost there" recipes - close enough to be worth suggesting.
    
    if exclude_ids is None:
        exclude_ids = set()
    
    partial_matches = []
    
    for recipe in recipes:
        # Skip recipes that were already shown
        if recipe['id'] in exclude_ids:
            continue
        
        # Apply filters first
        if not passes_filters(recipe, filters):
            continue
        
        # Calculate match
        match_data = calculate_match(recipe['ingredients'], user_ingredients)
        
        # Only consider recipes above threshold but not perfect matches
        if min_match_threshold <= match_data['percentage'] < 100:
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
    
    # Sort by match percentage (closest matches first)
    partial_matches.sort(key=lambda x: x['match_percentage'], reverse=True)
    
    return partial_matches

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

def display_results(results, ingred_input, filters=None):
    #Displays search results
    print("\n" + "=" * 70)
    print(f"Your ingredients: {ingred_input}")
    print("=" * 70)
    # display active filters
    if filters:
        print("Active filters:")
        for key, value in filters.items():
            print(f"  • {key}: {value}")
    else:
        print("No filters applied")
    print("=" * 70)

    # no recipes found; could be redirected to add more ingredients later
    if not results:
        print("\n No matching recipes found.")
        if filters:
            print("Try loosening your filters or adding more ingredients!\n")
        else:
            print("Try adding more ingredients!\n")
        return


    for i, recipe in enumerate(results, 1):
        #visual indicator
        bars = "[]" * int(recipe['match_percentage'] / 10)

        print(f"\n{i}. {recipe['name']}")
        print(f"   Match: {recipe['match_percentage']}% {bars}")
        # displays new metadata, useful for later filtering
        info_parts = []
        info_parts.append(f"Total Time: {recipe['total_time']} min")
        info_parts.append(f"Serves: {recipe['servings']}")
        info_parts.append(f"Skill Level: {recipe['skill_level']}")
        info_parts.append(f"Cuisine: {recipe['cuisine']}")
        print(f"   {' | '.join(info_parts)}")
        
        # Display dietary tags if any
        if recipe['dietary_tags']:
            tags = ', '.join(recipe['dietary_tags'])
            print(f"   Dietary Tags: {tags}")
        
        # Display equipment needed
        if recipe['equipment']:
            equipment = ', '.join(recipe['equipment'])
            print(f"   Equipment Needed: {equipment}")
        print(f"   You Have: {', '.join(recipe['matched_ingredients'])}")
        
        if recipe['missing_ingredients']:
            print(f"   Missing: {', '.join(recipe['missing_ingredients'])}")


def main():
    """
    # main function with ingredient input, filter application, recipe search and matching, display and now suggestions.
    """
    print("\n" + "=" * 70)
    print("SmartFridge - Quick Recipe Search")
    print("=" * 70)

    print("\nEnter your available ingredients (comma-separated):")
    print("Ex: eggs, bread, cheese, butter\n")

    user_input = input("Your ingredients: ").strip()

    if not user_input:
        print("\nNo ingredients entered. Exiting.\n")
        return
    
    user_ing = parse_ingredients(user_input)

    # get filters
    print("\n" + "-" * 70)
    print("⚙️  Optional Filters (press Enter to skip)")
    print("-" * 70)
    
    filters = {}
    
    max_time = input("Max cooking time (minutes): ").strip()
    if max_time and max_time.isdigit():
        filters['max_time'] = int(max_time)
    
    skill_level = input("Skill level (beginner/intermediate/advanced): ").strip()
    if skill_level:
        filters['skill_level'] = skill_level
    
    dietary = input("Dietary needs (vegetarian/vegan/gluten-free): ").strip()
    if dietary:
        filters['dietary_tags'] = [dietary]
    
    cuisine = input("Cuisine type (Italian/American/Asian/etc): ").strip()
    if cuisine:
        filters['cuisine'] = cuisine

    # load recipes and search
    recipes = load_recipes()
    results = search_recipes(user_ing, recipes, filters)

    # display results
    display_results(results, user_input, filters)

    shown_recipe_ids = set(recipe['id'] for recipe in results)

    # suggestion engine activation
    if not results:
        print("\n" + "=" * 70)
        print("No exact matches found - here's some options: ")
        print("=" * 70)
        
        # pass has_matches=False since we got zero results
        suggestions = generate_shopping_suggestions(user_ing, recipes, filters, top_n=5, has_matches=False, exclude_ids=shown_recipe_ids)
        
        # for display, try to find partial matches at low threshold
        partial_matches = find_partial_matches(user_ing, recipes, filters, min_match_threshold=10, exclude_ids=shown_recipe_ids)
        
        display_suggestions(suggestions, partial_matches)
        
        # interactive ingredient addition
        if suggestions:
            print("\n" + "-" * 70)
            print("Want to add one of these ingredients and search again? (y/n)")
            add_more = input("Your choice: ").strip().lower()
            
            if add_more == 'y':
                print("\nEnter ingredient to add:")
                new_ingredient = input("> ").strip()
                
                if new_ingredient:
                    user_ing.append(new_ingredient.lower())
                    print(f"\nAdded '{new_ingredient}' to your ingredients!")
                    
                    # Re-run search
                    updated_input = ", ".join(user_ing)
                    results = search_recipes(user_ing, recipes, filters)
                    display_results(results, updated_input, filters)
    
    elif results and results[0]['match_percentage'] < 100:
        # user has SOME matches but none are perfect
        # offer suggestions to improve their options
        print("\n" + "=" * 70)
        print("💡 Want to see what else you could make?")
        print("=" * 70)
        
        show_suggestions = input("See shopping suggestions? (y/n): ").strip().lower()
        
        if show_suggestions == 'y':
            # pass has_matches=True since we have results
            suggestions = generate_shopping_suggestions(user_ing, recipes, filters, top_n=5, has_matches=True, exclude_ids=shown_recipe_ids)
            
            partial_matches = find_partial_matches(user_ing, recipes, filters, min_match_threshold=50, exclude_ids=shown_recipe_ids)
            display_suggestions(suggestions, partial_matches)


if __name__ == "__main__":
    main()