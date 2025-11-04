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


def main():
    # Current testing: Does input and list parsing work?
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
    print(f"\nCollected ingredients: {', '.join(user_ing)}")

    recipes = load_recipes()
    
    match_data = calculate_match(['eggs', 'milk', 'flour'], user_ing)
    print(match_data)

if __name__ == "__main__":
    main()