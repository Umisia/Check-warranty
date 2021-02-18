import pytest
import json

inv_orders_data_path = r"./data/inv_orders_data.json"
crm_orders_data_path = r"./data/crm_orders_data.json"
inv_filecontent_data_path = r"./data/filecontent_test_data.json"

def load_json_data(path):
    with open(path, encoding='UTF-8') as my_data:
        data = json.load(my_data)
        return data

@pytest.fixture(params=load_json_data(inv_filecontent_data_path))
def inv_filecontent_data(request):
    return request.param

@pytest.fixture(params=load_json_data(inv_orders_data_path))
def inv_orders_data(request):
    return request.param

@pytest.fixture(params=load_json_data(crm_orders_data_path))
def crm_orders_data(request):
    return request.param