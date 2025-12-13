-- SmartFridge PostgreSQL Database Schema
-- Based on the ER diagram design

-- Drop tables if they exist (in reverse dependency order)
DROP TABLE IF EXISTS uses_term CASCADE;
DROP TABLE IF EXISTS uses CASCADE;
DROP TABLE IF EXISTS has_app CASCADE;
DROP TABLE IF EXISTS step CASCADE;
DROP TABLE IF EXISTS uses_ingredient CASCADE;
DROP TABLE IF EXISTS favorite CASCADE;
DROP TABLE IF EXISTS has_ingredient CASCADE;
DROP TABLE IF EXISTS cok_term CASCADE;
DROP TABLE IF EXISTS appliance CASCADE;
DROP TABLE IF EXISTS ingredients CASCADE;
DROP TABLE IF EXISTS recipe CASCADE;
DROP TABLE IF EXISTS "user" CASCADE;

-- User table
CREATE TABLE "user" (
    u_id VARCHAR(50) PRIMARY KEY,
    skill VARCHAR(20) CHECK (skill IN ('beginner', 'intermediate', 'advanced')),
    diet VARCHAR(100),  -- Can store multiple dietary restrictions as comma-separated
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

-- Ingredients table
CREATE TABLE ingredients (
    i_id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    cpu DECIMAL(10, 2),  -- cost per unit
    unit VARCHAR(20),    -- e.g., 'lb', 'oz', 'each'
    diet_cat VARCHAR(100) -- dietary category (vegetarian, vegan, etc.)
);

-- Recipe table
CREATE TABLE recipe (
    r_id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    "desc" TEXT,  -- description
    time INTEGER,  -- total time in minutes
    skill VARCHAR(20) CHECK (skill IN ('beginner', 'intermediate', 'advanced')),
    serving INTEGER
);

-- Appliance table
CREATE TABLE appliance (
    name VARCHAR(50) PRIMARY KEY
);

-- Cooking terms table
CREATE TABLE cok_term (
    name VARCHAR(50) PRIMARY KEY,
    "desc" TEXT
);

-- has_ingredient: User's pantry (which ingredients a user has)
CREATE TABLE has_ingredient (
    u_id VARCHAR(50) REFERENCES "user"(u_id) ON DELETE CASCADE,
    i_id INTEGER REFERENCES ingredients(i_id) ON DELETE CASCADE,
    amt DECIMAL(10, 2),
    exp_date DATE,
    PRIMARY KEY (u_id, i_id)
);

-- favorite: User's favorite recipes
CREATE TABLE favorite (
    u_id VARCHAR(50) REFERENCES "user"(u_id) ON DELETE CASCADE,
    r_id INTEGER REFERENCES recipe(r_id) ON DELETE CASCADE,
    PRIMARY KEY (u_id, r_id)
);

-- uses_ingredient: Which ingredients a recipe uses
CREATE TABLE uses_ingredient (
    r_id INTEGER REFERENCES recipe(r_id) ON DELETE CASCADE,
    i_id INTEGER REFERENCES ingredients(i_id) ON DELETE CASCADE,
    amt VARCHAR(50),  -- e.g., "2 cups", "3 slices"
    PRIMARY KEY (r_id, i_id)
);

-- Step: Recipe instructions
CREATE TABLE step (
    r_id INTEGER REFERENCES recipe(r_id) ON DELETE CASCADE,
    num INTEGER,  -- step number
    "desc" TEXT NOT NULL,
    time INTEGER,  -- time for this step in seconds
    PRIMARY KEY (r_id, num)
);

-- has_app: Which appliances a user has
CREATE TABLE has_app (
    name VARCHAR(50) REFERENCES appliance(name) ON DELETE CASCADE,
    u_id VARCHAR(50) REFERENCES "user"(u_id) ON DELETE CASCADE,
    PRIMARY KEY (name, u_id)
);

-- Uses: Which appliances a recipe requires
CREATE TABLE uses (
    name VARCHAR(50) REFERENCES appliance(name) ON DELETE CASCADE,
    r_id INTEGER REFERENCES recipe(r_id) ON DELETE CASCADE,
    PRIMARY KEY (name, r_id)
);

-- uses_term: Which cooking terms are used in which recipe steps
CREATE TABLE uses_term (
    r_id INTEGER,
    num INTEGER,
    name VARCHAR(50) REFERENCES cok_term(name) ON DELETE CASCADE,
    FOREIGN KEY (r_id, num) REFERENCES step(r_id, num) ON DELETE CASCADE,
    PRIMARY KEY (r_id, num, name)
);

-- Create indexes for better query performance
CREATE INDEX idx_has_ingredient_user ON has_ingredient(u_id);
CREATE INDEX idx_has_ingredient_ingredient ON has_ingredient(i_id);
CREATE INDEX idx_favorite_user ON favorite(u_id);
CREATE INDEX idx_favorite_recipe ON favorite(r_id);
CREATE INDEX idx_uses_ingredient_recipe ON uses_ingredient(r_id);
CREATE INDEX idx_uses_ingredient_ingredient ON uses_ingredient(i_id);
CREATE INDEX idx_step_recipe ON step(r_id);
CREATE INDEX idx_uses_recipe ON uses(r_id);
CREATE INDEX idx_has_app_user ON has_app(u_id);
CREATE INDEX idx_ingredients_name ON ingredients(name);
CREATE INDEX idx_recipe_skill ON recipe(skill);
CREATE INDEX idx_recipe_time ON recipe(time);

-- Create a view for easy recipe searching with ingredient matching
CREATE OR REPLACE VIEW recipe_full_info AS
SELECT 
    r.r_id,
    r.name,
    r."desc",
    r.time,
    r.skill,
    r.serving,
    COUNT(DISTINCT ui.i_id) as ingredient_count,
    STRING_AGG(DISTINCT i.name, ', ' ORDER BY i.name) as ingredients_list,
    STRING_AGG(DISTINCT a.name, ', ' ORDER BY a.name) as equipment_list
FROM recipe r
LEFT JOIN uses_ingredient ui ON r.r_id = ui.r_id
LEFT JOIN ingredients i ON ui.i_id = i.i_id
LEFT JOIN uses u ON r.r_id = u.r_id
LEFT JOIN appliance a ON u.name = a.name
GROUP BY r.r_id, r.name, r."desc", r.time, r.skill, r.serving;

COMMENT ON TABLE "user" IS 'User accounts with dietary preferences and skill level';
COMMENT ON TABLE ingredients IS 'Master ingredient list with pricing and dietary info';
COMMENT ON TABLE recipe IS 'Recipe master data';
COMMENT ON TABLE has_ingredient IS 'User pantry - what ingredients each user has';
COMMENT ON TABLE favorite IS 'User favorite recipes';
COMMENT ON TABLE uses_ingredient IS 'Recipe ingredients - what each recipe requires';
COMMENT ON TABLE step IS 'Recipe cooking instructions';
COMMENT ON TABLE cok_term IS 'Cooking terminology definitions';
COMMENT ON TABLE uses_term IS 'Cooking terms used in recipe steps';
COMMENT ON TABLE appliance IS 'Kitchen appliances';
COMMENT ON TABLE has_app IS 'User appliances - what equipment each user has';
COMMENT ON TABLE uses IS 'Recipe equipment - what appliances each recipe requires';