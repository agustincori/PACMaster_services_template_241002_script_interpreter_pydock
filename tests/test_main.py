import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app  # Adjust the import as per your project structure

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

@patch('main.get_new_runid')
@patch('main.user_identify')
@patch('main.save_outcome_data')
@patch('main.log_to_api')
def test_sum_and_save_success(mock_log_to_api, mock_save_outcome_data, mock_user_identify, mock_get_new_runid, client):
    # Arrange
    mock_user_identify.return_value = 0
    mock_get_new_runid.return_value = {'id_run': 1}
    mock_save_outcome_data.return_value = True

    # Act
    response = client.get('/sum_and_save?arg1=10&arg2=20&user=test&pswrd=test&use_db=false')

    # Assert
    assert response.status_code == 200
    data = response.get_json()
    assert data['sum'] == 30
    mock_user_identify.assert_called_once_with('test', 'test')
    mock_get_new_runid.assert_not_called()
    mock_save_outcome_data.assert_not_called()

@patch('main.user_identify')
def test_sum_and_save_missing_parameters(mock_user_identify, client):
    # Act
    response = client.get('/sum_and_save?user=test&pswrd=test&use_db=false')

    # Assert
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

@patch('main.user_identify')
def test_sum_and_save_invalid_credentials(mock_user_identify, client):
    # Arrange
    mock_user_identify.return_value = -1

    # Act
    response = client.get('/sum_and_save?arg1=10&arg2=20&user=invalid&pswrd=invalid&use_db=false')

    # Assert
    assert response.status_code == 401
    data = response.get_json()
    assert 'error' in data
    mock_user_identify.assert_called_once_with('invalid', 'invalid')

# Add more tests as needed to cover other edge cases and scenarios
