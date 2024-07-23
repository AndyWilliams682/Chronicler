import pytest
import cv2

from vision import *


@pytest.fixture()
def complete_test_image():
    image = cv2.imread(r"src\tests\Images\CompleteTemple.png")[..., ::-1]
    return cv2.cvtColor(image, cv2.COLOR_RGB2HSV)


def test_post_ocr_correction():
    output = post_ocr_correction("ASAGEWAYS\n)")
    assert output == "PASSAGEWAYS"


def test_get_room_boxes(complete_test_image):
    output = get_room_boxes(complete_test_image)
    assert output == [(1166, 896, 228, 112), (1454, 874, 217, 99), (883, 868, 228, 112), (1589, 729, 229, 111), (1307, 729, 228, 111), (1024, 729, 229, 111), (741, 729, 229, 111), (1448, 589, 229, 112), (1166, 589, 228, 112), (883, 589, 228, 112), (1307, 450, 228, 111), (1024, 450, 229, 111), (1166, 309, 228, 112)]
    extra_room_image = complete_test_image
    extra_room_image[896:1008, 546:775] = complete_test_image[896:1008, 1166:1395]
    with pytest.raises(ValueError, match="Expected 13 room boxes, got 14"):
        get_room_boxes(extra_room_image)
    empty_image = complete_test_image
    empty_image[:, :] = (0, 0, 0)
    with pytest.raises(ValueError):
        get_room_boxes(empty_image)


def test_get_image_parameters(complete_test_image):
    output = get_image_parameters(complete_test_image)
    assert output == {'room_details': {'room_width': 229, 'room_height': 112, 'horizontal_gap': 54, 'vertical_gap': 29}, 'slots_to_xy': {'0F2': {'x': 1166, 'y': 896}, '0F1': {'x': 1454, 'y': 867}, '0F3': {'x': 883, 'y': 868}, '1F0': {'x': 1589, 'y': 729}, '1F1': {'x': 1307, 'y': 729}, '1F2': {'x': 1024, 'y': 729}, '1F3': {'x': 741, 'y': 729}, '2F0': {'x': 1448, 'y': 589}, '2F1': {'x': 1166, 'y': 589}, '2F2': {'x': 883, 'y': 589}, '3F0': {'x': 1307, 'y': 450}, '3F1': {'x': 1024, 'y': 450}, '4F0': {'x': 1166, 'y': 309}}, 'incursion_menu_rect': {'x': 1563, 'y': 56, 'w': 648, 'h': 506}, 'incursions_remaining_rect': {'x': 1112, 'y': 1014, 'w': 337, 'h': 112}, 'cached': 1}
    empty_image = complete_test_image
    empty_image[:, :] = (0, 0, 0)
    with pytest.raises(ValueError):
        get_room_boxes(empty_image)


def test_read_image_using_saved_params_full_temple(complete_test_image):
    # Need more testing options for missing submenu/remaining
    cache = get_image_parameters(complete_test_image)
    full_temple = read_image_using_saved_params(complete_test_image, cache)
    assert full_temple == {'layout': {'0F2': {'Name': 'ENTRANCE', 'Connections': ['—']}, '0F1': {'Name': 'PITS', 'Connections': ['—', '\\']}, '0F3': {'Name': 'HALL OF HEROES', 'Connections': ['\\']}, '1F0': {'Name': 'SANCTUM OF UNITY', 'Connections': ['—', '\\']}, '1F1': {'Name': "SURVEYOR'S STUDY", 'Connections': []}, '1F2': {'Name': 'HYBRIDISATION CHAMBER', 'Connections': ['/', '—']}, '1F3': {'Name': 'GLITTERING HALLS', 'Connections': []}, '2F0': {'Name': "DORYANI'S INSTITUTE", 'Connections': ['/', '—']}, '2F1': {'Name': 'HALL OF LORDS', 'Connections': ['/', '\\']}, '2F2': {'Name': 'SPARRING ROOM', 'Connections': ['/']}, '3F0': {'Name': 'POOLS OF RESTORATION', 'Connections': ['/', '\\']}, '3F1': {'Name': 'LIGHTNING WORKSHOP', 'Connections': []}, '4F0': {'Name': 'APEX OF ATZOATL', 'Connections': []}}, 'incursion': {'room': 'PITS', 'left_option': 'POISON GARDEN', 'right_option': 'VAULT'}, 'remaining': 1}
    empty_image = complete_test_image
    empty_image[:, :] = (0, 0, 0)
    with pytest.raises(ValueError):
        get_room_boxes(empty_image)


def test_read_image_using_saved_params_not_continuous(complete_test_image):
    cache = get_image_parameters(complete_test_image)
    previous = {"remaining": 3, "slot": "0F1"}
    not_continuous = read_image_using_saved_params(complete_test_image, cache, previous)
    assert not_continuous == {'layout': {'0F2': {'Name': 'ENTRANCE', 'Connections': ['—']}, '0F1': {'Name': 'PITS', 'Connections': ['—', '\\']}, '0F3': {'Name': 'HALL OF HEROES', 'Connections': ['\\']}, '1F0': {'Name': 'SANCTUM OF UNITY', 'Connections': ['—', '\\']}, '1F1': {'Name': "SURVEYOR'S STUDY", 'Connections': []}, '1F2': {'Name': 'HYBRIDISATION CHAMBER', 'Connections': ['/', '—']}, '1F3': {'Name': 'GLITTERING HALLS', 'Connections': []}, '2F0': {'Name': "DORYANI'S INSTITUTE", 'Connections': ['/', '—']}, '2F1': {'Name': 'HALL OF LORDS', 'Connections': ['/', '\\']}, '2F2': {'Name': 'SPARRING ROOM', 'Connections': ['/']}, '3F0': {'Name': 'POOLS OF RESTORATION', 'Connections': ['/', '\\']}, '3F1': {'Name': 'LIGHTNING WORKSHOP', 'Connections': []}, '4F0': {'Name': 'APEX OF ATZOATL', 'Connections': []}}, 'incursion': {'room': 'PITS', 'left_option': 'POISON GARDEN', 'right_option': 'VAULT'}, 'remaining': 1}


def test_read_image_using_saved_params_continuous(complete_test_image):
    cache = get_image_parameters(complete_test_image)
    previous = {"remaining": 2, "slot": "0F1"}
    not_continuous = read_image_using_saved_params(complete_test_image, cache, previous)
    assert not_continuous == {'incursion': {'left_option': 'POISON GARDEN', 'right_option': 'VAULT', 'room': 'PITS'}, 'layout': {'0F1': {'Connections': ['—', '\\', 'r—'], 'Name': 'PITS'}}, 'remaining': 1}


# def test_get_text_mask()
# TODO: CHECK FOR WHEN THE TEXT MASK FINDS NOTHING


def test_read_incursion_submenu():
    menu_image = cv2.imread(r"src\tests\Images\Submenu.png")[..., ::-1]
    menu_image = cv2.cvtColor(menu_image, cv2.COLOR_RGB2HSV)
    output = read_incursion_submenu(menu_image)
    assert output == {'left_option': 'POISON GARDEN', 'right_option': 'VAULT', 'room': 'PITS'}


def test_read_incursions_remaining():
    rem_image = cv2.imread(r"src\tests\Images\Remaining.png")[..., ::-1]
    rem_image = cv2.cvtColor(rem_image, cv2.COLOR_RGB2HSV)
    output = read_incursions_remaining(rem_image)
    assert output == 1


def test_read_room_text():
    room_image = cv2.imread(r"src\tests\Images\Room.png")[..., ::-1]
    room_image = cv2.cvtColor(room_image, cv2.COLOR_RGB2HSV)
    output = read_room_text(room_image)
    assert output == "HALL OF HEROES"


def test_connection_present():
    connection_image = cv2.imread(r"src\tests\Images\Connection.png")[..., ::-1]
    connection_image = cv2.cvtColor(connection_image, cv2.COLOR_RGB2HSV)
    present_image = connection_image[1:29]
    not_present_image = connection_image[29:140]
    assert connection_present(present_image) == True
    assert connection_present(not_present_image) == False
