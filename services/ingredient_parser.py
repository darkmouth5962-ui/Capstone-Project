from fuzzywuzzy import fuzz, process

def build_master_ingredient_list(recipes):
    # extracts all unique ingredients from the recipe database.
    # "dictionary" for fuzzy matching.

    master_ingredients = set()
    
    for recipe in recipes:
        for ingredient in recipe.get('ingredients', []):
            # normalize to lowercase
            master_ingredients.add(ingredient.lower().strip())
    
    return master_ingredients

def fuzzy_match_ingredient(user_input, master_ingredients, threshold=80):
    # attempts to match a user's ingredient input to known ingredients using fuzzy matching.
    # handles typos, variations, and close matches.

    # if it's an exact match, we're golden!
    if user_input.lower() in master_ingredients:
        return {
            'match': user_input.lower(),
            'score': 100,
            'original': user_input,
            'needs_confirmation': False
        }
    
    # try to find close matches using fuzzy matching
    # process.extractOne returns (best_match, score)
    best_match = process.extractOne(
        user_input.lower(),
        master_ingredients,
        scorer=fuzz.ratio  # using basic Levenshtein distance
    )
    
    if best_match and best_match[1] >= threshold:
        # found a good match
        confidence = best_match[1]
        
        return {
            'match': best_match[0],
            'score': confidence,
            'original': user_input,
            'needs_confirmation': confidence < 95  # ask user if not super confident
        }
    
    # no good match found
    return {
        'match': None,
        'score': best_match[1] if best_match else 0,
        'original': user_input,
        'needs_confirmation': False
    }

def parse_ingredients(raw_input, master_ingredients=None, interactive=True):
    # accepts comma-separated or newline-separated ingredients
    # returns a clean list of ingredients

    # split on commas or newlines
    ingredients = raw_input.replace('\n', ',').split(',')
    
    # normalize: lowercase and strip whitespace
    raw_ingredients = [ing.strip().lower() for ing in ingredients if ing.strip()]
    
    # if no master list provided, just return the raw ingredients (no fuzzy matching)
    if master_ingredients is None:
        return raw_ingredients, {}
    
    # fuzzy matching process
    cleaned = []
    fuzzy_report = {
        'exact_matches': [],
        'fuzzy_matches': [],
        'unmatched': [],
        'user_confirmations': []
    }
    
    print("\n" + "-" * 70)
    print("Validating ingredients...")
    print("-" * 70)
    
    for raw_ing in raw_ingredients:
        match_result = fuzzy_match_ingredient(raw_ing, master_ingredients, threshold=80)
        
        if match_result['match']:
            if match_result['score'] == 100:
                # exact match, no questions asked
                cleaned.append(match_result['match'])
                fuzzy_report['exact_matches'].append(raw_ing)
                print(f"{raw_ing}")
            
            elif match_result['needs_confirmation'] and interactive:
                # fuzzy match, ask for confirmation
                print(f"'{raw_ing}' → Did you mean '{match_result['match']}'? (y/n)")
                confirmation = input("   > ").strip().lower()
                
                if confirmation == 'y' or confirmation == 'yes':
                    cleaned.append(match_result['match'])
                    fuzzy_report['fuzzy_matches'].append({
                        'original': raw_ing,
                        'matched': match_result['match'],
                        'score': match_result['score']
                    })
                    fuzzy_report['user_confirmations'].append(raw_ing)
                    print(f"Using '{match_result['match']}'")
                else:
                    # user rejected the suggestion
                    print(f"Skipping '{raw_ing}'")
                    fuzzy_report['unmatched'].append(raw_ing)
            
            else:
                # high confidence match (95+), use without asking
                cleaned.append(match_result['match'])
                fuzzy_report['fuzzy_matches'].append({
                    'original': raw_ing,
                    'matched': match_result['match'],
                    'score': match_result['score']
                })
                print(f"{raw_ing} → {match_result['match']} ({match_result['score']}% match)")
        
        else:
            # no match found
            print(f"'{raw_ing}' - not recognized (no close matches found)")
            fuzzy_report['unmatched'].append(raw_ing)
            
            if interactive:
                print(f"Keep it anyway? (y/n)")
                keep = input("   > ").strip().lower()
                if keep == 'y' or keep == 'yes':
                    cleaned.append(raw_ing)
                    print(f"Added '{raw_ing}' as-is")
    
    print("-" * 70)
    
    return cleaned, fuzzy_report

def display_fuzzy_summary(fuzzy_report, final_ingredients):
    # show fuzzy match summary if any corrections were made
    if fuzzy_report['fuzzy_matches'] or fuzzy_report['unmatched']:
        print("\n" + "=" * 70)
        print("Ingredient Summary")
        print("=" * 70)
        print(f"Exact matches: {len(fuzzy_report['exact_matches'])}")
        print(f"Fuzzy matches: {len(fuzzy_report['fuzzy_matches'])}")
        print(f"Unmatched: {len(fuzzy_report['unmatched'])}")
        print(f"Final ingredient list: {', '.join(final_ingredients)}")