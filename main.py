from services.ingredient_parser import (
    parse_ingredients, 
    build_master_ingredient_list,
    display_fuzzy_summary
)
from services.recipe_matcher import (
    load_recipes,
    find_partial_matches,
    display_results
)
from services.suggestion_engine import (
    display_suggestions
)

# CQRS+EDA Architecture Integration
from commands.command_handlers import (
    handle_create_user,
    handle_add_ingredient,
    handle_log_recipe_search
)
from queries.query_handlers import (
    query_recipes_by_ingredients,
    query_shopping_suggestions
)
from consumers.event_consumers import setup_event_consumers
import time

# session user ID (created at startup)
_session_user_id = None

def get_user_filters():
    # get filters
    print("\n" + "-" * 70)
    print("Optional Filters (press Enter to skip)")
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
    
    return filters

def handle_no_matches(user_ing, recipes, filters, master_ingredients):
    print("\n" + "=" * 70)
    print("No exact matches found - let's find some options!")
    print("=" * 70)
    
    # Generate suggestions - NOW USING QUERY
    suggestions = query_shopping_suggestions(_session_user_id, filters, top_n=5)
    
    # Find any partial matches at low threshold
    partial_matches = find_partial_matches(user_ing, recipes, filters, min_match_threshold=10, exclude_ids=set())
    
    display_suggestions(suggestions, partial_matches)
    
    # Offer to add ingredients and search again
    if suggestions:
        print("\n" + "-" * 70)
        print("Want to add one of these ingredients and search again? (y/n)")
        add_more = input("Your choice: ").strip().lower()
        
        if add_more == 'y':
            print("\nEnter ingredient to add:")
            new_ingredient = input("> ").strip()
            
            if new_ingredient:
                # Fuzzy match the new ingredient
                new_ing_parsed, _ = parse_ingredients(new_ingredient, master_ingredients, interactive=True)
                
                if new_ing_parsed:
                    # ADD INGREDIENT USING COMMAND
                    for ing in new_ing_parsed:
                        handle_add_ingredient(_session_user_id, ing, 1.0)
                    
                    user_ing.extend(new_ing_parsed)
                    print(f"\nAdded '{', '.join(new_ing_parsed)}' to your ingredients!")
                    
                    # Wait for event processing
                    time.sleep(0.1)
                    
                    # Re-run search - NOW USING QUERY
                    updated_input = ", ".join(user_ing)
                    results = query_recipes_by_ingredients(_session_user_id, user_ing, filters)
                    display_results(results, updated_input, filters)

def handle_partial_matches(user_ing, recipes, filters, shown_recipe_ids):
    # user has SOME matches but none are perfect
        # offer suggestions to improve their options
        print("\n" + "=" * 70)
        print("Want to see what else you could make?")
        print("=" * 70)
        
        show_suggestions = input("See shopping suggestions? (y/n): ").strip().lower()
        
        if show_suggestions == 'y':
            # Generate suggestions - NOW USING QUERY
            suggestions = query_shopping_suggestions(_session_user_id, filters, top_n=5)
            
            partial_matches = find_partial_matches(user_ing, recipes, filters, min_match_threshold=50, exclude_ids=shown_recipe_ids)
            display_suggestions(suggestions, partial_matches)

def main():
    global _session_user_id
    
    # CQRS+EDA SETUP: initialize event consumers
    setup_event_consumers()
    
    # CQRS+EDA SETUP: create session user (COMMAND)
    user_result = handle_create_user(
        username=f"session_{int(time.time())}",
        password="temp",
        dietary_restrictions=[]
    )
    _session_user_id = user_result['user_id']
    
    # time for event processing
    time.sleep(0.05)
    
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

    # CQRS+EDA: add ingredients to pantry using COMMANDS
    for ingredient in user_ing:
        handle_add_ingredient(_session_user_id, ingredient, 1.0) #sample amount
    
    # wait for event processing
    time.sleep(0.1)

    filters = get_user_filters()

    # search - QUERY instead of search_recipes
    results = query_recipes_by_ingredients(user_ing, filters)
    
    # CQRS+EDA: log search for analytics
    handle_log_recipe_search(_session_user_id, user_ing, filters, len(results))

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