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
    # main function to run the recipe search and display results
    print("\n" + "=" * 70)
    print("SmartFridge - Quick Recipe Search")
    print("=" * 70)

    print("Enter your available ingredients (comma-separated):")
    print("Ex: eggs, bread, cheese, butter\n")

    # get user input
    user_input = input("Your ingredients: ").strip()

    # guard against empty input
    if not user_input:
        print("\n No ingredients entered. Exiting.\n")
        return
    
    # parse ingredients and print
    user_ing = parse_ingredients(user_input)

    # Get filters (optional)
    print("\nAdd filters? (press Enter to skip)")
    
    filters = {}
    
    # Max time filter
    max_time = input("Max cooking time (minutes, or Enter to skip): ").strip()
    if max_time and max_time.isdigit():
        filters['max_time'] = int(max_time)
    
    # skill level filter
    skill_level = input("Skill level (beginner/intermediate/advanced, or Enter to skip): ").strip()
    if skill_level:
        filters['skill_level'] = skill_level
    
    # dietary filter
    dietary = input("Dietary needs (vegetarian/vegan/gluten-free, or Enter to skip): ").strip()
    if dietary:
        filters['dietary_tags'] = [dietary]
    
    # cuisine filter
    cuisine = input("Cuisine type (Italian/American/Asian/etc, or Enter to skip): ").strip()
    if cuisine:
        filters['cuisine'] = cuisine

    recipes = load_recipes()

    results = search_recipes(user_ing, recipes, filters)

    display_results(results, user_input, filters)


if __name__ == "__main__":
    main()