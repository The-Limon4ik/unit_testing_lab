import pytest

from src.inventory import (
    Inventory,
    Item,
    OutOfStockError,
    UnknownItemError,
)


# ---------------------------------------------------------------- фикстуры


@pytest.fixture
def inventory():
    """Склад с одной позицией: apple, 10 шт. по 10.0."""
    inv = Inventory()
    inv.add(Item("apple", 10.0), quantity=10)
    return inv


@pytest.fixture
def empty_inventory():
    return Inventory()


@pytest.fixture
def multi_inventory():
    """apple 10x10.0 = 100.0; pear 3x2.5 = 7.5; plum 5x1.0 = 5.0 -> 112.5."""
    inv = Inventory()
    inv.add(Item("apple", 10.0), quantity=10)
    inv.add(Item("pear", 2.5), quantity=3)
    inv.add(Item("plum", 1.0), quantity=5)
    return inv


# ---------------------------------------------------------------- Item


def test_item_valid_data_creates_item():
    item = Item("apple", 1.5, 3)
    assert (item.name, item.price, item.quantity) == ("apple", 1.5, 3)


def test_item_default_quantity_is_zero():
    assert Item("apple", 1.0).quantity == 0


def test_item_zero_price_and_quantity_allowed():
    item = Item("free", 0.0, 0)
    assert item.price == 0.0 and item.quantity == 0


@pytest.mark.parametrize(
    "name, price, quantity",
    [
        ("", 1.0, 1),        # пустое имя
        ("apple", -0.01, 1),  # отрицательная цена
        ("apple", 1.0, -1),   # отрицательное количество
    ],
)
def test_item_invalid_data_raises_value_error(name, price, quantity):
    with pytest.raises(ValueError):
        Item(name, price, quantity)


# ---------------------------------------------------------------- add


def test_add_new_item_stores_it_with_given_quantity(empty_inventory):
    empty_inventory.add(Item("apple", 10.0), quantity=4)
    assert empty_inventory.find("apple").quantity == 4


def test_add_default_quantity_adds_one(empty_inventory):
    empty_inventory.add(Item("apple", 10.0))
    assert empty_inventory.find("apple").quantity == 1


def test_add_existing_item_increases_quantity(inventory):
    inventory.add(Item("apple", 10.0), quantity=5)
    assert inventory.find("apple").quantity == 15


@pytest.mark.parametrize("quantity", [0, -1, -100])
def test_add_non_positive_quantity_raises_value_error(inventory, quantity):
    with pytest.raises(ValueError):
        inventory.add(Item("pear", 1.0), quantity=quantity)


def test_add_invalid_quantity_does_not_change_inventory(inventory):
    with pytest.raises(ValueError):
        inventory.add(Item("apple", 10.0), quantity=0)
    assert inventory.find("apple").quantity == 10


# ---------------------------------------------------------------- remove


def test_remove_partial_decreases_quantity(inventory):
    inventory.remove("apple", 3)
    assert inventory.find("apple").quantity == 7


def test_remove_default_quantity_removes_one(inventory):
    inventory.remove("apple")
    assert inventory.find("apple").quantity == 9


def test_remove_all_quantity_deletes_item(inventory):
    inventory.remove("apple", 10)
    with pytest.raises(UnknownItemError):
        inventory.find("apple")


def test_remove_exactly_one_left_deletes_item(empty_inventory):
    empty_inventory.add(Item("apple", 1.0), quantity=1)
    empty_inventory.remove("apple", 1)
    assert empty_inventory.total_value() == 0


def test_remove_unknown_item_raises(inventory):
    with pytest.raises(UnknownItemError):
        inventory.remove("banana")


def test_remove_more_than_available_raises_out_of_stock(inventory):
    with pytest.raises(OutOfStockError):
        inventory.remove("apple", 11)


def test_remove_out_of_stock_does_not_change_quantity(inventory):
    with pytest.raises(OutOfStockError):
        inventory.remove("apple", 11)
    assert inventory.find("apple").quantity == 10


@pytest.mark.parametrize("quantity", [0, -1])
def test_remove_non_positive_quantity_raises_value_error(inventory, quantity):
    with pytest.raises(ValueError):
        inventory.remove("apple", quantity)


# ---------------------------------------------------------------- find


def test_find_existing_item_returns_item(inventory):
    item = inventory.find("apple")
    assert item.name == "apple" and item.price == pytest.approx(10.0)


def test_find_unknown_item_raises(inventory):
    with pytest.raises(UnknownItemError):
        inventory.find("banana")


# ---------------------------------------------------------------- total_value


def test_total_value_empty_inventory_returns_zero(empty_inventory):
    assert empty_inventory.total_value() == pytest.approx(0.0)


def test_total_value_single_item(inventory):
    assert inventory.total_value() == pytest.approx(100.0)


def test_total_value_multiple_items_sums_all(multi_inventory):
    assert multi_inventory.total_value() == pytest.approx(112.5)


def test_total_value_rounds_to_two_decimals(empty_inventory):
    empty_inventory.add(Item("x", 0.333), quantity=1)
    assert empty_inventory.total_value() == pytest.approx(0.33)


def test_total_value_after_remove_decreases(inventory):
    inventory.remove("apple", 4)
    assert inventory.total_value() == pytest.approx(60.0)


# ---------------------------------------------------------------- low_stock


def test_low_stock_default_threshold_is_five(multi_inventory):
    # pear=3, plum=5 (граница включается), apple=10 не входит
    assert multi_inventory.low_stock() == ["pear", "plum"]


def test_low_stock_explicit_threshold(multi_inventory):
    assert multi_inventory.low_stock(threshold=3) == ["pear"]


def test_low_stock_result_is_sorted(empty_inventory):
    for name in ["zebra", "apple", "mango"]:
        empty_inventory.add(Item(name, 1.0), quantity=1)
    assert empty_inventory.low_stock() == ["apple", "mango", "zebra"]


def test_low_stock_threshold_zero_returns_empty(multi_inventory):
    assert multi_inventory.low_stock(threshold=0) == []


def test_low_stock_empty_inventory_returns_empty_list(empty_inventory):
    assert empty_inventory.low_stock() == []


def test_low_stock_negative_threshold_raises(inventory):
    with pytest.raises(ValueError):
        inventory.low_stock(threshold=-1)


# ---------------------------------------------------------------- apply_discount


@pytest.mark.parametrize(
    "percent, expected",
    [
        (0, 100.0),
        (10, 90.0),
        (50, 50.0),
        (100, 0.0),
    ],
)
def test_apply_discount_valid_percent(inventory, percent, expected):
    assert inventory.apply_discount(percent) == pytest.approx(expected)


@pytest.mark.parametrize("percent", [-0.01, -1, 100.01, 101])
def test_apply_discount_percent_out_of_range_raises(inventory, percent):
    with pytest.raises(ValueError):
        inventory.apply_discount(percent)


def test_apply_discount_empty_inventory_returns_zero(empty_inventory):
    assert empty_inventory.apply_discount(25) == pytest.approx(0.0)


def test_apply_discount_does_not_change_inventory(inventory):
    inventory.apply_discount(50)
    assert inventory.total_value() == pytest.approx(100.0)


# probably defects (xfail)


@pytest.mark.xfail(
    reason="Дефект: add() молча затирает Item.quantity, заданное в конструкторе "
    "(Item('a', 1.0, 5) + add(quantity=1) даёт 1, а не 5 или 6).",
    strict=True,
)
def test_add_new_item_with_initial_quantity_keeps_it(empty_inventory):
    empty_inventory.add(Item("apple", 1.0, 5), quantity=1)
    assert empty_inventory.find("apple").quantity in (5, 6)


@pytest.mark.xfail(
    reason="Дефект: total_value() на пустом складе возвращает int 0 вместо float "
    "(нарушает аннотацию -> float).",
    strict=True,
)
def test_total_value_empty_inventory_returns_float(empty_inventory):
    assert isinstance(empty_inventory.total_value(), float)
