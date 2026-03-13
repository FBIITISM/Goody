"""Tests for the Trail Mix module."""

import json
import os
import tempfile
import pytest

from trail import Ingredient, Trail, TrailCollection


class TestIngredient:
    def test_create_ingredient(self):
        ing = Ingredient(
            name="Almonds",
            amount_grams=50,
            calories_per_100g=579,
            protein_per_100g=21.15,
            fat_per_100g=49.93,
            carbs_per_100g=21.55,
        )
        assert ing.name == "Almonds"
        assert ing.amount_grams == 50

    def test_calories_calculated_from_amount(self):
        ing = Ingredient(name="Almonds", amount_grams=100, calories_per_100g=579)
        assert ing.calories == 579.0

    def test_calories_scaled_by_amount(self):
        ing = Ingredient(name="Almonds", amount_grams=50, calories_per_100g=579)
        assert ing.calories == 289.5

    def test_macronutrients_scaled(self):
        ing = Ingredient(
            name="Cashews",
            amount_grams=30,
            calories_per_100g=553,
            protein_per_100g=18.22,
            fat_per_100g=43.85,
            carbs_per_100g=30.19,
        )
        assert round(ing.protein, 2) == 5.47
        assert round(ing.fat, 2) == round(43.85 * 30 / 100, 2)
        assert round(ing.carbs, 2) == 9.06


class TestTrail:
    def _make_trail(self) -> Trail:
        trail = Trail(name="Classic Mix", description="A classic trail mix")
        trail.add_ingredient(
            Ingredient("Almonds", 50, 579, protein_per_100g=21.15, fat_per_100g=49.93, carbs_per_100g=21.55)
        )
        trail.add_ingredient(
            Ingredient("Raisins", 30, 299, protein_per_100g=3.07, fat_per_100g=0.46, carbs_per_100g=79.18)
        )
        trail.add_ingredient(
            Ingredient("Dark Chocolate Chips", 20, 546, protein_per_100g=4.90, fat_per_100g=31.28, carbs_per_100g=59.40)
        )
        return trail

    def test_trail_creation(self):
        trail = Trail(name="My Mix")
        assert trail.name == "My Mix"
        assert trail.description == ""
        assert trail.ingredients == []

    def test_add_ingredient(self):
        trail = Trail(name="Test Mix")
        ing = Ingredient("Walnuts", 40, 654)
        trail.add_ingredient(ing)
        assert len(trail.ingredients) == 1
        assert trail.ingredients[0].name == "Walnuts"

    def test_add_duplicate_ingredient_merges(self):
        trail = Trail(name="Test Mix")
        trail.add_ingredient(Ingredient("Walnuts", 40, 654))
        trail.add_ingredient(Ingredient("Walnuts", 60, 654))
        assert len(trail.ingredients) == 1
        assert trail.ingredients[0].amount_grams == 100

    def test_add_ingredient_case_insensitive_merge(self):
        trail = Trail(name="Test Mix")
        trail.add_ingredient(Ingredient("walnuts", 40, 654))
        trail.add_ingredient(Ingredient("Walnuts", 60, 654))
        assert len(trail.ingredients) == 1
        assert trail.ingredients[0].amount_grams == 100

    def test_remove_ingredient(self):
        trail = self._make_trail()
        result = trail.remove_ingredient("Raisins")
        assert result is True
        assert len(trail.ingredients) == 2
        assert trail.get_ingredient("Raisins") is None

    def test_remove_nonexistent_ingredient(self):
        trail = self._make_trail()
        result = trail.remove_ingredient("Nonexistent")
        assert result is False

    def test_remove_case_insensitive(self):
        trail = self._make_trail()
        result = trail.remove_ingredient("almonds")
        assert result is True
        assert trail.get_ingredient("Almonds") is None

    def test_get_ingredient(self):
        trail = self._make_trail()
        ing = trail.get_ingredient("Raisins")
        assert ing is not None
        assert ing.name == "Raisins"

    def test_get_nonexistent_ingredient(self):
        trail = self._make_trail()
        assert trail.get_ingredient("Nonexistent") is None

    def test_total_weight(self):
        trail = self._make_trail()
        assert trail.total_weight_grams == 100  # 50 + 30 + 20

    def test_total_calories(self):
        trail = self._make_trail()
        expected = (579 * 50 / 100) + (299 * 30 / 100) + (546 * 20 / 100)
        assert round(trail.total_calories, 2) == round(expected, 2)

    def test_total_protein(self):
        trail = self._make_trail()
        expected = (21.15 * 50 / 100) + (3.07 * 30 / 100) + (4.90 * 20 / 100)
        assert round(trail.total_protein, 2) == round(expected, 2)

    def test_total_fat(self):
        trail = self._make_trail()
        expected = (49.93 * 50 / 100) + (0.46 * 30 / 100) + (31.28 * 20 / 100)
        assert round(trail.total_fat, 2) == round(expected, 2)

    def test_total_carbs(self):
        trail = self._make_trail()
        expected = (21.55 * 50 / 100) + (79.18 * 30 / 100) + (59.40 * 20 / 100)
        assert round(trail.total_carbs, 2) == round(expected, 2)

    def test_nutrition_summary(self):
        trail = self._make_trail()
        summary = trail.nutrition_summary()
        assert summary["name"] == "Classic Mix"
        assert "total_calories" in summary
        assert "total_weight_grams" in summary
        assert "ingredients" in summary
        assert set(summary["ingredients"]) == {"Almonds", "Raisins", "Dark Chocolate Chips"}

    def test_to_dict(self):
        trail = Trail(name="Simple", description="desc")
        trail.add_ingredient(Ingredient("Nuts", 50, 600))
        d = trail.to_dict()
        assert d["name"] == "Simple"
        assert d["description"] == "desc"
        assert len(d["ingredients"]) == 1
        assert d["ingredients"][0]["name"] == "Nuts"

    def test_from_dict_roundtrip(self):
        trail = self._make_trail()
        data = trail.to_dict()
        restored = Trail.from_dict(data)
        assert restored.name == trail.name
        assert restored.description == trail.description
        assert len(restored.ingredients) == len(trail.ingredients)
        assert restored.total_calories == trail.total_calories

    def test_save_and_load(self):
        trail = self._make_trail()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            path = tmp.name
        try:
            trail.save(path)
            loaded = Trail.load(path)
            assert loaded.name == trail.name
            assert loaded.total_calories == trail.total_calories
            assert len(loaded.ingredients) == len(trail.ingredients)
        finally:
            os.unlink(path)

    def test_empty_trail_zero_totals(self):
        trail = Trail(name="Empty")
        assert trail.total_weight_grams == 0
        assert trail.total_calories == 0
        assert trail.total_protein == 0
        assert trail.total_fat == 0
        assert trail.total_carbs == 0


class TestTrailCollection:
    def _make_collection(self) -> TrailCollection:
        col = TrailCollection()
        t1 = Trail(name="Classic Mix")
        t1.add_ingredient(Ingredient("Almonds", 50, 579))
        t2 = Trail(name="Tropical Mix")
        t2.add_ingredient(Ingredient("Mango", 40, 60))
        col.add(t1)
        col.add(t2)
        return col

    def test_add_trail(self):
        col = TrailCollection()
        trail = Trail(name="Test")
        col.add(trail)
        assert "Test" in col.list_trails()

    def test_remove_trail(self):
        col = self._make_collection()
        result = col.remove("Classic Mix")
        assert result is True
        assert "Classic Mix" not in col.list_trails()

    def test_remove_nonexistent(self):
        col = TrailCollection()
        assert col.remove("Nothing") is False

    def test_get_trail(self):
        col = self._make_collection()
        trail = col.get("Tropical Mix")
        assert trail is not None
        assert trail.name == "Tropical Mix"

    def test_get_missing_trail(self):
        col = TrailCollection()
        assert col.get("Missing") is None

    def test_list_trails(self):
        col = self._make_collection()
        trails = col.list_trails()
        assert "Classic Mix" in trails
        assert "Tropical Mix" in trails

    def test_save_and_load_all(self):
        col = self._make_collection()
        with tempfile.TemporaryDirectory() as tmpdir:
            col_dir = TrailCollection(directory=tmpdir)
            for name in col.list_trails():
                col_dir.add(col.get(name))
            col_dir.save_all()

            # Verify JSON files were created
            files = [f for f in os.listdir(tmpdir) if f.endswith(".json")]
            assert len(files) == 2

            # Load into a new collection
            loaded_col = TrailCollection(directory=tmpdir)
            loaded_col.load_all()
            assert set(loaded_col.list_trails()) == {"Classic Mix", "Tropical Mix"}

    def test_load_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            col = TrailCollection(directory=tmpdir)
            col.load_all()
            assert col.list_trails() == []

    def test_load_nonexistent_directory(self):
        col = TrailCollection(directory="/nonexistent/path")
        col.load_all()  # Should not raise
        assert col.list_trails() == []
