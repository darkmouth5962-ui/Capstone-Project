from services.ingredient_parser import (
    parse_ingredients, 
    build_master_ingredient_list,
    display_fuzzy_summary
)
from services.recipe_matcher import (
    load_recipes,
    search_recipes,
    find_partial_matches,
    display_results
)
from services.suggestion_engine import (
    generate_shopping_suggestions,
    display_suggestions
)

def get_user_filters():
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

def handle_no_matches(user_ing, recipes, filters, master_ingredients):
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

def handle_partial_matches(user_ing, recipes, filters, shown_recipe_ids):
    # user has SOME matches but none are perfect
        # offer suggestions to improve their options
        print("\n" + "=" * 70)
        print("Want to see what else you could make?")
        print("=" * 70)
        
        show_suggestions = input("See shopping suggestions? (y/n): ").strip().lower()
        
        if show_suggestions == 'y':
            # pass has_matches=True since we have results
            suggestions = generate_shopping_suggestions(user_ing, recipes, filters, top_n=5, has_matches=True, exclude_ids=shown_recipe_ids)
            
            partial_matches = find_partial_matches(user_ing, recipes, filters, min_match_threshold=50, exclude_ids=shown_recipe_ids)
            display_suggestions(suggestions, partial_matches)

def main():
    # main function with ingredient input, filter application, recipe search and matching, display and now suggestions.
    
    # load recipes
    recipes = load_recipes()

    print("\n" + "=" * 70)
    print("SmartFridge - Quick Recipe Search")
    print("=" * 70)

    print("\nEnter your available ingredients (comma-separated):")
    print("Ex: eggs, bread, cheese, butter\n")

    user_input = input("Your ingredients: ").strip()

    if not user_input:
        print("\nNo ingredients entered. Exiting.\n")
        return
    
    print("\nBuilding ingredient database...")
    master_ingredients = build_master_ingredient_list(recipes)
    print(f"Loaded {len(master_ingredients)} known ingredients")

    # parse ingredients with fuzzy matching
    user_ing, fuzzy_report = parse_ingredients(user_input, master_ingredients, interactive=True)

    # show fuzzy match summary if any corrections were made
    display_fuzzy_summary(fuzzy_report, user_ing)

    filters = get_user_filters()

    # search
    results = search_recipes(user_ing, recipes, filters)

    # display results
    display_results(results, user_input, filters)

    shown_recipe_ids = set(recipe['id'] for recipe in results)

    # suggestion engine activation
    if not results:
        # no matches found, activate full suggestion engine
        handle_no_matches(user_ing, recipes, filters, master_ingredients)
    elif results and results[0]['match_percentage'] < 100:
        # some matches but not perfect, offer additional suggestions
        handle_partial_matches(user_ing, recipes, filters, shown_recipe_ids)
        


if __name__ == "__main__":
    main()