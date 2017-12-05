import os, json

def test_list_eq(file_out, file_ref):
    with open(file_out) as f:
        list_out = json.load(f)
    with open(file_ref) as f:
        list_ref = json.load(f)

    try:
        assert list_out == list_ref
    except(AssertionError):
        with open("report_tests.txt", "a") as ft:
            ft.write("test_list_eq is failing\n")
