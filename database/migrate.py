"""
Migration script to load recipes.json data into PostgreSQL database
"""

import json
import sys
from pathlib import Path
from database.db_connection import (
    init_db_pool, 
    execute_update, 
    execute_many,
    execute_query,
    test_connection,
    close_all_connections,
    DatabaseContext
)

def load_recipes_from_json(filepath='recipes.json'):
    """Load recipes from JSON file"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data['recipes']

def extract_unique_ingredients(recipes):
    """Extract all unique ingredients from recipes"""
    ingredients = set()
    for recipe in recipes:
        for ing in recipe.get('ingredients', []):
            ingredients.add(ing.lower())
    return sorted(ingredients)

def extract_unique_appliances(recipes):
    """Extract all unique appliances from recipes"""
    appliances = set()
    for recipe in recipes:
        for equip in recipe.get('equipment', []):
            appliances.add(equip.lower())
    return sorted(appliances)

def extract_dietary_tags(recipes):
    """Extract all dietary tags"""
    tags = set()
    for recipe in recipes:
        for tag in recipe.get('dietary_tags', []):
            tags.add(tag.lower())
    return sorted(tags)

def insert_ingredients(ingredients_list):
    """Insert ingredients into database"""
    print(f"\n📦 Inserting {len(ingredients_list)} ingredients...")
    
    # For demo, we'll set default values for cpu (cost) and unit
    # In production, these would come from a more detailed data source
    query = """
        INSERT INTO ingredients (name, cpu, unit, diet_cat)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (name) DO NOTHING
        RETURNING i_id;
    """
    
    params = []
    for ing in ingredients_list:
        # Set some reasonable defaults
        cpu = 0.00  # cost per unit - would be filled in later
        unit = 'each'  # default unit
        diet_cat = None  # would be categorized later
        params.append((ing, cpu, unit, diet_cat))
    
    count = execute_many(query, params)
    print(f"  ✓ Inserted {count} ingredients")
    return count

def insert_appliances(appliances_list):
    """Insert appliances into database"""
    print(f"\n🔧 Inserting {len(appliances_list)} appliances...")
    
    query = """
        INSERT INTO appliance (name)
        VALUES (%s)
        ON CONFLICT (name) DO NOTHING;
    """
    
    params = [(app,) for app in appliances_list]
    count = execute_many(query, params)
    print(f"  ✓ Inserted {count} appliances")
    return count

def get_ingredient_id(ingredient_name):
    """Get ingredient ID by name"""
    query = "SELECT i_id FROM ingredients WHERE name = %s;"
    result = execute_query(query, (ingredient_name.lower(),), fetch_one=True)
    return result['i_id'] if result else None

def insert_recipes(recipes):
    """Insert recipes and related data"""
    print(f"\n📖 Inserting {len(recipes)} recipes...")
    
    for recipe in recipes:
        recipe_id = recipe['id']
        name = recipe['name']
        desc = recipe.get('cuisine', '')  # Using cuisine as description for now
        time = recipe.get('total_time', 0)
        skill = recipe.get('skill_level', 'beginner')
        serving = recipe.get('servings', 1)
        
        # Insert recipe
        query = """
            INSERT INTO recipe (r_id, name, "desc", time, skill, serving)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (r_id) DO UPDATE 
            SET name = EXCLUDED.name,
                "desc" = EXCLUDED."desc",
                time = EXCLUDED.time,
                skill = EXCLUDED.skill,
                serving = EXCLUDED.serving;
        """
        execute_update(query, (recipe_id, name, desc, time, skill, serving))
        
        # Insert recipe ingredients (uses_ingredient)
        for ingredient_name in recipe.get('ingredients', []):
            i_id = get_ingredient_id(ingredient_name)
            if i_id:
                ing_query = """
                    INSERT INTO uses_ingredient (r_id, i_id, amt)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (r_id, i_id) DO NOTHING;
                """
                execute_update(ing_query, (recipe_id, i_id, '1'))  # Default amount
        
        # Insert recipe steps
        for step_data in recipe.get('instructions', []):
            step_num = step_data['step']
            step_desc = step_data['instruction']
            step_time = step_data.get('time', 0)
            
            step_query = """
                INSERT INTO step (r_id, num, "desc", time)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (r_id, num) DO UPDATE
                SET "desc" = EXCLUDED."desc",
                    time = EXCLUDED.time;
            """
            execute_update(step_query, (recipe_id, step_num, step_desc, step_time))
        
        # Insert recipe equipment (uses)
        for equipment_name in recipe.get('equipment', []):
            equip_query = """
                INSERT INTO uses (name, r_id)
                VALUES (%s, %s)
                ON CONFLICT (name, r_id) DO NOTHING;
            """
            execute_update(equip_query, (equipment_name.lower(), recipe_id))
    
    print(f"  ✓ Inserted {len(recipes)} recipes with ingredients, steps, and equipment")

def insert_cooking_terms():
    """Insert common cooking terms"""
    print("\n📚 Inserting cooking terms...")
    
    cooking_terms = [
        ('dice', 'Cut food into small cubes (about 1/4 inch)'),
        ('mince', 'Cut food into very small pieces'),
        ('chop', 'Cut into irregular pieces'),
        ('slice', 'Cut into thin, flat pieces'),
        ('julienne', 'Cut into thin strips'),
        ('sauté', 'Cook quickly in a small amount of fat over high heat'),
        ('simmer', 'Cook gently just below boiling point'),
        ('boil', 'Cook in liquid at 212°F with rapid bubbling'),
        ('bake', 'Cook with dry heat in an oven'),
        ('roast', 'Cook with dry heat, usually at higher temperature than baking'),
        ('grill', 'Cook over direct heat'),
        ('steam', 'Cook with steam from boiling water'),
        ('blanch', 'Briefly cook in boiling water, then plunge into ice water'),
        ('braise', 'Cook slowly in liquid in a covered pot'),
        ('sear', 'Brown the surface quickly at high heat'),
        ('whisk', 'Beat rapidly with a whisk to incorporate air'),
        ('fold', 'Gently combine ingredients to preserve air'),
        ('knead', 'Work dough by pressing and folding'),
        ('marinate', 'Soak in seasoned liquid to add flavor'),
        ('season', 'Add salt, pepper, or other spices to taste')
    ]
    
    query = """
        INSERT INTO cok_term (name, "desc")
        VALUES (%s, %s)
        ON CONFLICT (name) DO NOTHING;
    """
    
    count = execute_many(query, cooking_terms)
    print(f"  ✓ Inserted {count} cooking terms")

def verify_migration():
    """Verify that migration was successful"""
    print("\n🔍 Verifying migration...")
    
    checks = [
        ("SELECT COUNT(*) as count FROM ingredients", "Ingredients"),
        ("SELECT COUNT(*) as count FROM recipe", "Recipes"),
        ("SELECT COUNT(*) as count FROM appliance", "Appliances"),
        ("SELECT COUNT(*) as count FROM step", "Recipe steps"),
        ("SELECT COUNT(*) as count FROM uses_ingredient", "Recipe ingredients"),
        ("SELECT COUNT(*) as count FROM uses", "Recipe equipment"),
        ("SELECT COUNT(*) as count FROM cok_term", "Cooking terms"),
    ]
    
    for query, name in checks:
        result = execute_query(query, fetch_one=True)
        count = result['count'] if result else 0
        print(f"  ✓ {name}: {count}")

def main():
    """Main migration function"""
    print("=" * 70)
    print("SmartFridge Database Migration")
    print("=" * 70)
    
    # Initialize database connection
    if not init_db_pool():
        print("✗ Failed to connect to database")
        sys.exit(1)
    
    # Test connection
    if not test_connection():
        print("✗ Database connection test failed")
        sys.exit(1)
    
    try:
        # Load recipes from JSON
        print("\n📂 Loading recipes.json...")
        recipes = load_recipes_from_json()
        print(f"  ✓ Loaded {len(recipes)} recipes")
        
        # Extract unique data
        ingredients = extract_unique_ingredients(recipes)
        appliances = extract_unique_appliances(recipes)
        
        # Insert data
        insert_ingredients(ingredients)
        insert_appliances(appliances)
        insert_cooking_terms()
        insert_recipes(recipes)
        
        # Verify
        verify_migration()
        
        print("\n" + "=" * 70)
        print("✅ Migration completed successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        close_all_connections()

if __name__ == '__main__':
    main()