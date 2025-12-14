"""
Ingredient Substitution System
Maps problematic ingredients to dietary-appropriate substitutes
"""

# Comprehensive substitution database
SUBSTITUTIONS = {
    # DAIRY SUBSTITUTIONS
    'milk': {
        'substitutes': [
            {
                'name': 'almond milk',
                'ratio': '1:1',
                'best_for': ['vegan', 'dairy-free'],
                'flavor_impact': 'Slightly nutty flavor, thinner consistency',
                'texture_impact': 'Works well in most recipes, may be thinner in sauces',
                'cooking_notes': 'Use unsweetened for savory dishes'
            },
            {
                'name': 'oat milk',
                'ratio': '1:1',
                'best_for': ['vegan', 'dairy-free', 'nut-free'],
                'flavor_impact': 'Mild, slightly sweet',
                'texture_impact': 'Creamy, similar to dairy milk',
                'cooking_notes': 'Great for baking and cooking'
            },
            {
                'name': 'soy milk',
                'ratio': '1:1',
                'best_for': ['vegan', 'dairy-free'],
                'flavor_impact': 'Neutral flavor',
                'texture_impact': 'Similar to dairy milk',
                'cooking_notes': 'High protein content, works well in all recipes'
            }
        ]
    },
    
    'butter': {
        'substitutes': [
            {
                'name': 'vegan butter',
                'ratio': '1:1',
                'best_for': ['vegan', 'dairy-free'],
                'flavor_impact': 'Very similar to butter',
                'texture_impact': 'Nearly identical in baking and cooking',
                'cooking_notes': 'Use same amount, melts similarly'
            },
            {
                'name': 'olive oil',
                'ratio': '3/4 cup oil = 1 cup butter',
                'best_for': ['vegan', 'dairy-free'],
                'flavor_impact': 'Adds olive flavor (good for savory dishes)',
                'texture_impact': 'Works in cooking, different in baking',
                'cooking_notes': 'Best for sautéing and roasting'
            },
            {
                'name': 'coconut oil',
                'ratio': '1:1',
                'best_for': ['vegan', 'dairy-free'],
                'flavor_impact': 'Slight coconut flavor',
                'texture_impact': 'Solid at room temp, similar to butter',
                'cooking_notes': 'Great for baking, use refined for no coconut taste'
            }
        ]
    },
    
    'cheese': {
        'substitutes': [
            {
                'name': 'vegan cheese',
                'ratio': '1:1',
                'best_for': ['vegan', 'dairy-free'],
                'flavor_impact': 'Similar but not identical',
                'texture_impact': 'Melts differently, improving brands available',
                'cooking_notes': 'Some brands melt better than others'
            },
            {
                'name': 'nutritional yeast',
                'ratio': '2-3 tbsp per 1/4 cup cheese',
                'best_for': ['vegan', 'dairy-free'],
                'flavor_impact': 'Cheesy, nutty flavor',
                'texture_impact': 'No melting, adds flavor only',
                'cooking_notes': 'Great for "cheesy" flavor without dairy'
            },
            {
                'name': 'cashew cream',
                'ratio': 'varies by recipe',
                'best_for': ['vegan', 'dairy-free'],
                'flavor_impact': 'Mild, creamy',
                'texture_impact': 'Creamy but doesn\'t melt like cheese',
                'cooking_notes': 'Soak cashews first, blend smooth'
            }
        ]
    },
    
    'cream': {
        'substitutes': [
            {
                'name': 'coconut cream',
                'ratio': '1:1',
                'best_for': ['vegan', 'dairy-free'],
                'flavor_impact': 'Slight coconut flavor',
                'texture_impact': 'Very rich and creamy',
                'cooking_notes': 'Chill can and use thick top layer'
            },
            {
                'name': 'cashew cream',
                'ratio': '1:1',
                'best_for': ['vegan', 'dairy-free'],
                'flavor_impact': 'Neutral, mild',
                'texture_impact': 'Thick and creamy',
                'cooking_notes': 'Blend soaked cashews with water'
            },
            {
                'name': 'oat cream',
                'ratio': '1:1',
                'best_for': ['vegan', 'dairy-free', 'nut-free'],
                'flavor_impact': 'Mild, slightly sweet',
                'texture_impact': 'Creamy and thick',
                'cooking_notes': 'Commercial versions available'
            }
        ]
    },
    
    'yogurt': {
        'substitutes': [
            {
                'name': 'coconut yogurt',
                'ratio': '1:1',
                'best_for': ['vegan', 'dairy-free'],
                'flavor_impact': 'Slight coconut flavor',
                'texture_impact': 'Similar to dairy yogurt',
                'cooking_notes': 'Works in all recipes'
            },
            {
                'name': 'soy yogurt',
                'ratio': '1:1',
                'best_for': ['vegan', 'dairy-free'],
                'flavor_impact': 'Neutral',
                'texture_impact': 'Very similar to dairy yogurt',
                'cooking_notes': 'High protein, works well'
            }
        ]
    },
    
    # EGGS SUBSTITUTIONS
    'egg': {
        'substitutes': [
            {
                'name': 'flax egg',
                'ratio': '1 tbsp ground flax + 3 tbsp water = 1 egg',
                'best_for': ['vegan'],
                'flavor_impact': 'Slightly nutty',
                'texture_impact': 'Works for binding, not for fluffiness',
                'cooking_notes': 'Let sit 5 min to gel, best for baking'
            },
            {
                'name': 'chia egg',
                'ratio': '1 tbsp chia seeds + 3 tbsp water = 1 egg',
                'best_for': ['vegan'],
                'flavor_impact': 'Very mild',
                'texture_impact': 'Works for binding',
                'cooking_notes': 'Let sit 5 min to gel'
            },
            {
                'name': 'applesauce',
                'ratio': '1/4 cup = 1 egg',
                'best_for': ['vegan'],
                'flavor_impact': 'Slight sweetness',
                'texture_impact': 'Adds moisture, works in baking',
                'cooking_notes': 'Use unsweetened, best for cakes/muffins'
            },
            {
                'name': 'aquafaba',
                'ratio': '3 tbsp = 1 egg',
                'best_for': ['vegan'],
                'flavor_impact': 'Neutral',
                'texture_impact': 'Can be whipped, great for meringues',
                'cooking_notes': 'Liquid from canned chickpeas, whips like egg whites'
            }
        ]
    },
    
    'eggs': {
        'substitutes': [
            {
                'name': 'flax eggs',
                'ratio': '1 tbsp ground flax + 3 tbsp water per egg',
                'best_for': ['vegan'],
                'flavor_impact': 'Slightly nutty',
                'texture_impact': 'Works for binding',
                'cooking_notes': 'Multiply ratio by number of eggs needed'
            },
            {
                'name': 'aquafaba',
                'ratio': '3 tbsp per egg',
                'best_for': ['vegan'],
                'flavor_impact': 'Neutral',
                'texture_impact': 'Can be whipped',
                'cooking_notes': 'From canned chickpeas'
            }
        ]
    },
    
    # MEAT SUBSTITUTIONS
    'chicken': {
        'substitutes': [
            {
                'name': 'tofu',
                'ratio': '1:1 by weight',
                'best_for': ['vegetarian', 'vegan'],
                'flavor_impact': 'Neutral, absorbs flavors well',
                'texture_impact': 'Firm tofu has similar texture when pressed',
                'cooking_notes': 'Press water out first, marinate for best flavor'
            },
            {
                'name': 'chickpeas',
                'ratio': '1 cup = 4 oz chicken',
                'best_for': ['vegetarian', 'vegan'],
                'flavor_impact': 'Mild, nutty',
                'texture_impact': 'Different texture, hearty',
                'cooking_notes': 'Works well in curries and stews'
            },
            {
                'name': 'seitan',
                'ratio': '1:1 by weight',
                'best_for': ['vegetarian', 'vegan'],
                'flavor_impact': 'Neutral',
                'texture_impact': 'Chewy, meat-like',
                'cooking_notes': 'High in protein, wheat-based (not gluten-free)'
            }
        ]
    },
    
    'beef': {
        'substitutes': [
            {
                'name': 'portobello mushrooms',
                'ratio': '1:1 by volume',
                'best_for': ['vegetarian', 'vegan'],
                'flavor_impact': 'Umami, meaty flavor',
                'texture_impact': 'Hearty, substantial',
                'cooking_notes': 'Slice or chop, great for grilling'
            },
            {
                'name': 'lentils',
                'ratio': '1 cup cooked = 4 oz beef',
                'best_for': ['vegetarian', 'vegan'],
                'flavor_impact': 'Earthy',
                'texture_impact': 'Hearty, holds together',
                'cooking_notes': 'Great for tacos, bolognese, etc.'
            },
            {
                'name': 'black beans',
                'ratio': '1 cup = 4 oz beef',
                'best_for': ['vegetarian', 'vegan'],
                'flavor_impact': 'Rich, earthy',
                'texture_impact': 'Hearty and filling',
                'cooking_notes': 'Can mash partially for texture'
            }
        ]
    },
    
    # GLUTEN SUBSTITUTIONS
    'bread': {
        'substitutes': [
            {
                'name': 'gluten-free bread',
                'ratio': '1:1',
                'best_for': ['gluten-free'],
                'flavor_impact': 'Similar with right brand',
                'texture_impact': 'Can be denser or crumblier',
                'cooking_notes': 'Many good brands available now'
            },
            {
                'name': 'lettuce wraps',
                'ratio': '2 leaves = 1 slice',
                'best_for': ['gluten-free'],
                'flavor_impact': 'Fresh, crunchy',
                'texture_impact': 'Completely different, light',
                'cooking_notes': 'Use sturdy lettuce like romaine'
            },
            {
                'name': 'rice cakes',
                'ratio': '1:1',
                'best_for': ['gluten-free'],
                'flavor_impact': 'Mild, neutral',
                'texture_impact': 'Crispy, lighter',
                'cooking_notes': 'Works for open-faced sandwiches'
            }
        ]
    },
    
    'pasta': {
        'substitutes': [
            {
                'name': 'gluten-free pasta',
                'ratio': '1:1',
                'best_for': ['gluten-free'],
                'flavor_impact': 'Nearly identical',
                'texture_impact': 'Very close to wheat pasta',
                'cooking_notes': 'Cook al dente, don\'t overcook'
            },
            {
                'name': 'zucchini noodles',
                'ratio': '1:1 by volume',
                'best_for': ['gluten-free'],
                'flavor_impact': 'Fresh, vegetal',
                'texture_impact': 'Much softer, releases water',
                'cooking_notes': 'Spiralize, cook briefly or eat raw'
            },
            {
                'name': 'rice noodles',
                'ratio': '1:1',
                'best_for': ['gluten-free'],
                'flavor_impact': 'Neutral',
                'texture_impact': 'Softer, different chew',
                'cooking_notes': 'Naturally gluten-free'
            }
        ]
    },
    
    'flour': {
        'substitutes': [
            {
                'name': 'gluten-free flour blend',
                'ratio': '1:1',
                'best_for': ['gluten-free'],
                'flavor_impact': 'Similar to wheat flour',
                'texture_impact': 'Works well in most recipes',
                'cooking_notes': 'Use blends with xanthan gum for best results'
            },
            {
                'name': 'almond flour',
                'ratio': '1:1 (but denser)',
                'best_for': ['gluten-free'],
                'flavor_impact': 'Nutty, sweet',
                'texture_impact': 'Denser, moister',
                'cooking_notes': 'Best for cakes, cookies, not bread'
            },
            {
                'name': 'coconut flour',
                'ratio': '1/4 cup coconut = 1 cup wheat',
                'best_for': ['gluten-free'],
                'flavor_impact': 'Slight coconut flavor',
                'texture_impact': 'Very absorbent',
                'cooking_notes': 'Needs more liquid, use less'
            }
        ]
    }
}

def get_substitutions_for_ingredient(ingredient_name, dietary_restrictions):
    """
    Get appropriate substitutions for an ingredient based on dietary restrictions
    
    Args:
        ingredient_name: Name of the ingredient to substitute
        dietary_restrictions: List of dietary restrictions (e.g., ['vegan', 'gluten-free'])
    
    Returns:
        List of appropriate substitutes
    """
    ingredient_lower = ingredient_name.lower().strip()
    
    if ingredient_lower not in SUBSTITUTIONS:
        return []
    
    all_substitutes = SUBSTITUTIONS[ingredient_lower]['substitutes']
    
    # filter substitutes that work for the dietary restrictions
    appropriate_subs = []
    for sub in all_substitutes:
        # check if this substitute helps with any of the user's dietary restrictions
        if any(restriction in sub['best_for'] for restriction in dietary_restrictions):
            appropriate_subs.append(sub)
    
    return appropriate_subs

def format_substitution_display(substitute):
    # format a substitution for display
    return {
        'name': substitute['name'],
        'ratio': substitute['ratio'],
        'impact': f"{substitute['flavor_impact']} | {substitute['texture_impact']}",
        'notes': substitute['cooking_notes']
    }