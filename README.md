# Goody
Foods

## Trail

The **Trail** module lets you create, manage, and save custom trail mix recipes with full nutritional tracking.

### Features

- Create named trail mix recipes with descriptions
- Add and remove ingredients with amounts in grams
- Automatic nutritional totals (calories, protein, fat, carbs)
- Duplicate ingredients are merged automatically
- Save/load individual recipes as JSON files
- Manage collections of recipes

### Usage

```python
from trail import Ingredient, Trail, TrailCollection

# Create a trail mix
mix = Trail(name="Energy Boost", description="High-protein trail mix")

# Add ingredients
mix.add_ingredient(Ingredient("Almonds", amount_grams=50, calories_per_100g=579,
                               protein_per_100g=21.15, fat_per_100g=49.93, carbs_per_100g=21.55))
mix.add_ingredient(Ingredient("Raisins", amount_grams=30, calories_per_100g=299,
                               protein_per_100g=3.07, fat_per_100g=0.46, carbs_per_100g=79.18))

# Get nutritional summary
print(mix.nutrition_summary())

# Save to file
mix.save("energy_boost.json")

# Load from file
loaded = Trail.load("energy_boost.json")

# Use a collection to manage multiple mixes
collection = TrailCollection(directory="./recipes")
collection.add(mix)
collection.save_all()
```

### Running Tests

```bash
python -m pytest test_trail.py -v
```
