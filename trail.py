"""Trail Mix module for Goody - Foods app.

Allows users to create, manage, and save custom trail mix recipes.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class Ingredient:
    """Represents a single ingredient in a trail mix."""

    name: str
    amount_grams: float
    calories_per_100g: float
    protein_per_100g: float = 0.0
    fat_per_100g: float = 0.0
    carbs_per_100g: float = 0.0

    @property
    def calories(self) -> float:
        return (self.calories_per_100g * self.amount_grams) / 100

    @property
    def protein(self) -> float:
        return (self.protein_per_100g * self.amount_grams) / 100

    @property
    def fat(self) -> float:
        return (self.fat_per_100g * self.amount_grams) / 100

    @property
    def carbs(self) -> float:
        return (self.carbs_per_100g * self.amount_grams) / 100


@dataclass
class Trail:
    """Represents a trail mix recipe with a collection of ingredients."""

    name: str
    description: str = ""
    ingredients: List[Ingredient] = field(default_factory=list)

    def add_ingredient(self, ingredient: Ingredient) -> None:
        """Add an ingredient to the trail mix."""
        for existing in self.ingredients:
            if existing.name.lower() == ingredient.name.lower():
                existing.amount_grams += ingredient.amount_grams
                return
        self.ingredients.append(ingredient)

    def remove_ingredient(self, name: str) -> bool:
        """Remove an ingredient by name. Returns True if removed, False if not found."""
        for i, ingredient in enumerate(self.ingredients):
            if ingredient.name.lower() == name.lower():
                self.ingredients.pop(i)
                return True
        return False

    def get_ingredient(self, name: str) -> Optional[Ingredient]:
        """Get an ingredient by name."""
        for ingredient in self.ingredients:
            if ingredient.name.lower() == name.lower():
                return ingredient
        return None

    @property
    def total_weight_grams(self) -> float:
        """Total weight of the trail mix in grams."""
        return sum(i.amount_grams for i in self.ingredients)

    @property
    def total_calories(self) -> float:
        """Total calories in the trail mix."""
        return sum(i.calories for i in self.ingredients)

    @property
    def total_protein(self) -> float:
        """Total protein in grams."""
        return sum(i.protein for i in self.ingredients)

    @property
    def total_fat(self) -> float:
        """Total fat in grams."""
        return sum(i.fat for i in self.ingredients)

    @property
    def total_carbs(self) -> float:
        """Total carbohydrates in grams."""
        return sum(i.carbs for i in self.ingredients)

    def nutrition_summary(self) -> dict:
        """Return a summary of nutritional information."""
        return {
            "name": self.name,
            "total_weight_grams": round(self.total_weight_grams, 2),
            "total_calories": round(self.total_calories, 2),
            "total_protein_grams": round(self.total_protein, 2),
            "total_fat_grams": round(self.total_fat, 2),
            "total_carbs_grams": round(self.total_carbs, 2),
            "ingredients": [i.name for i in self.ingredients],
        }

    def to_dict(self) -> dict:
        """Serialize the trail mix to a dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "ingredients": [asdict(i) for i in self.ingredients],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Trail":
        """Deserialize a trail mix from a dictionary."""
        ingredients = [Ingredient(**i) for i in data.get("ingredients", [])]
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            ingredients=ingredients,
        )

    def save(self, filepath: str) -> None:
        """Save the trail mix to a JSON file."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> "Trail":
        """Load a trail mix from a JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)


class TrailCollection:
    """Manages a collection of saved trail mix recipes."""

    def __init__(self, directory: str = ".") -> None:
        self.directory = directory
        self._trails: dict[str, Trail] = {}

    def add(self, trail: Trail) -> None:
        """Add a trail mix to the collection."""
        self._trails[trail.name] = trail

    def remove(self, name: str) -> bool:
        """Remove a trail mix by name. Returns True if removed."""
        if name in self._trails:
            del self._trails[name]
            return True
        return False

    def get(self, name: str) -> Optional[Trail]:
        """Get a trail mix by name."""
        return self._trails.get(name)

    def list_trails(self) -> List[str]:
        """Return a list of trail mix names."""
        return list(self._trails.keys())

    def save_all(self) -> None:
        """Save all trail mixes to JSON files in the collection directory."""
        os.makedirs(self.directory, exist_ok=True)
        for trail in self._trails.values():
            safe_name = "".join(
                c if c.isalnum() or c in "-_" else "_"
                for c in trail.name
            ).lower()
            filepath = os.path.join(self.directory, f"{safe_name}.json")
            trail.save(filepath)

    def load_all(self) -> None:
        """Load all trail mixes from JSON files in the collection directory."""
        if not os.path.isdir(self.directory):
            return
        for filename in os.listdir(self.directory):
            if filename.endswith(".json"):
                filepath = os.path.join(self.directory, filename)
                trail = Trail.load(filepath)
                self._trails[trail.name] = trail
