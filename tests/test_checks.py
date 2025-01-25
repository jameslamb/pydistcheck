import pydistcheck._checks


def test_all_checks_constant_contains_names_of_all_checks():
    check_classes = []
    for obj_name in dir(pydistcheck._checks):
        obj = getattr(pydistcheck._checks, obj_name)
        if hasattr(obj, "check_name") and obj is not pydistcheck._checks._CheckProtocol:
            check_classes.append(obj.check_name)

    # every check should be in ALL_CHECKS
    assert set(check_classes) == pydistcheck._checks.ALL_CHECKS

    # check class names should be unique
    assert len(pydistcheck._checks.ALL_CHECKS) == len(check_classes)
