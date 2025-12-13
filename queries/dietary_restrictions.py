"""
Dietary Restriction Filtering System
Maps dietary restrictions to ingredient exclusions
"""

# comprehensive mapping of dietary restrictions to forbidden ingredients
DIETARY_RESTRICTIONS = {
    'vegetarian': {
        'forbidden_ingredients': [
            'chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna', 
            'shrimp', 'bacon', 'ham', 'turkey', 'lamb', 'meat'
        ],
        'description': 'No meat, fish, or poultry'
    },
    'vegan': {
        'forbidden_ingredients': [
            # all meat
            'chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna',
            'shrimp', 'bacon', 'ham', 'turkey', 'lamb', 'meat',
            # dairy
            'milk', 'cheese', 'butter', 'cream', 'yogurt', 'sour cream',
            'mozzarella', 'parmesan', 'cheddar', 'feta', 'ricotta',
            # eggs
            'egg', 'eggs',
            # honey
            'honey'
        ],
        'description': 'No animal products'
    },
    'dairy-free': {
        'forbidden_ingredients': [
            'milk', 'cheese', 'butter', 'cream', 'yogurt', 'sour cream',
            'mozzarella', 'parmesan', 'cheddar', 'feta', 'ricotta',
            'cream cheese', 'heavy cream', 'half and half', 'whey'
        ],
        'description': 'No dairy products'
    },
    'gluten-free': {
        'forbidden_ingredients': [
            'bread', 'flour', 'wheat', 'pasta', 'spaghetti', 'noodles',
            'breadcrumbs', 'wheat flour', 'all-purpose flour', 'barley',
            'rye', 'couscous', 'soy sauce'  # most soy sauce contains wheat
        ],
        'description': 'No gluten-containing grains'
    },
    'nut-free': {
        'forbidden_ingredients': [
            'peanut', 'peanuts', 'peanut butter', 'almond', 'almonds',
            'cashew', 'cashews', 'walnut', 'walnuts', 'pecan', 'pecans',
            'pistachio', 'pistachios', 'hazelnut', 'hazelnuts',
            'macadamia', 'pine nuts', 'brazil nuts'
        ],
        'description': 'No tree nuts or peanuts'
    }
}


def check_recipe_compatibility(recipe_ingredients, user_dietary_restrictions):
    """
    Check if a recipe is compatible with user's dietary restrictions
    
    Args:
        recipe_ingredients: List of ingredient names (strings)
        user_dietary_restrictions: List of dietary restriction names (e.g., ['vegan', 'gluten-free'])
    
    Returns:
        tuple: (is_compatible: bool, violations: list of dicts)
    """
    violations = []
    
    # normalize ingredient names for comparison
    recipe_ingredients_lower = [ing.lower().strip() for ing in recipe_ingredients]
    
    for restriction in user_dietary_restrictions:
        restriction_lower = restriction.lower().strip()
        
        if restriction_lower not in DIETARY_RESTRICTIONS:
            continue
        
        forbidden = DIETARY_RESTRICTIONS[restriction_lower]['forbidden_ingredients']
        
        # check if any recipe ingredient is forbidden
        for recipe_ing in recipe_ingredients_lower:
            for forbidden_ing in forbidden:
                # check for exact match or if forbidden ingredient is part of recipe ingredient; e.g., "cheese" matches "cheddar cheese"
                if forbidden_ing in recipe_ing or recipe_ing in forbidden_ing:
                    violations.append({
                        'restriction': restriction,
                        'ingredient': recipe_ing,
                        'reason': f"Contains {forbidden_ing}"
                    })
                    break
    
    is_compatible = len(violations) == 0
    return is_compatible, violations


def get_restriction_info(restriction_name):
    # get information about a dietary restriction
    restriction_lower = restriction_name.lower().strip()
    if restriction_lower in DIETARY_RESTRICTIONS:
        return DIETARY_RESTRICTIONS[restriction_lower]
    return None


def get_all_restrictions():
    # get list of all supported dietary restrictions
    return list(DIETARY_RESTRICTIONS.keys())


def format_violation_message(violations):
    # format violation messages for user display
    if not violations:
        return None
    
    messages = []
    for v in violations:
        messages.append(f"{v['restriction']}: {v['reason']}")
    
    return " | ".join(messages)