-- Run this query in pgAdmin4 to see your PostgreSQL schema
-- Go to: Tools > Query Tool > Paste this query > Run (F5)

-- =====================================================
-- GET ALL TABLES AND THEIR COLUMNS
-- =====================================================

SELECT
    t.table_name,
    c.column_name,
    c.data_type,
    c.is_nullable,
    c.column_default
FROM information_schema.tables t
JOIN information_schema.columns c
    ON t.table_name = c.table_name
WHERE t.table_schema = 'public'
    AND t.table_type = 'BASE TABLE'
ORDER BY t.table_name, c.ordinal_position;

-- =====================================================
-- Or run these separately for each table you expect:
-- =====================================================

-- Products table
SELECT * FROM information_schema.columns
WHERE table_name = 'products' AND table_schema = 'public';

-- Sales table
SELECT * FROM information_schema.columns
WHERE table_name = 'sales' AND table_schema = 'public';

-- Recipes table
SELECT * FROM information_schema.columns
WHERE table_name = 'recipes' AND table_schema = 'public';

-- Recipe ingredients table
SELECT * FROM information_schema.columns
WHERE table_name = 'recipe_ingredients' AND table_schema = 'public';

-- =====================================================
-- VIEW SAMPLE DATA FROM EACH TABLE
-- =====================================================

-- SELECT * FROM products LIMIT 5;
-- SELECT * FROM sales LIMIT 5;
-- SELECT * FROM recipes LIMIT 5;
-- SELECT * FROM recipe_ingredients LIMIT 5;
