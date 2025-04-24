from fastapi.testclient import TestClient
from src.main import app
from src.fake_db import db  # Импортируем db для контроля состояния

client = TestClient(app)

# Тестовые данные (должны соответствовать начальному состоянию db)
initial_users = [
    {
        'id': 1,
        'name': 'Ivan Ivanov',
        'email': 'i.i.ivanov@mail.com',
    },
    {
        'id': 2,
        'name': 'Petr Petrov',
        'email': 'p.p.petrov@mail.com',
    }
]

def setup_module():
    """Сброс базы данных перед каждым тестом"""
    global db
    db._users = [user.copy() for user in initial_users]
    db._id = len(db._users)

def test_get_existed_user():
    '''Получение существующего пользователя'''
    setup_module()
    test_user = initial_users[0]
    response = client.get("/api/v1/user", params={'email': test_user['email']})
    assert response.status_code == 200
    assert response.json() == {
        'id': test_user['id'],
        'name': test_user['name'],
        'email': test_user['email']
    }

def test_get_unexisted_user():
    '''Получение несуществующего пользователя'''
    setup_module()
    non_existent_email = "nonexistent@mail.com"
    response = client.get("/api/v1/user", params={'email': non_existent_email})
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}

def test_create_user_with_valid_email():
    '''Создание пользователя с уникальной почтой'''
    setup_module()
    new_user = {
        "name": "New User",
        "email": "new.user@mail.com"
    }
    response = client.post("/api/v1/user", json=new_user)
    assert response.status_code == 201
    assert isinstance(response.json(), int)
    
    # Проверяем, что пользователь действительно добавлен
    created_user = db.get_user_by_email(new_user['email'])
    assert created_user is not None
    assert created_user['name'] == new_user['name']
    assert created_user['activated'] is False  # Проверка дополнительного поля

def test_create_user_with_invalid_email():
    '''Создание пользователя с существующей почтой'''
    setup_module()
    existing_email = initial_users[0]['email']
    duplicate_user = {
        "name": "Duplicate User",
        "email": existing_email
    }
    response = client.post("/api/v1/user", json=duplicate_user)
    assert response.status_code == 409
    assert response.json() == {"detail": "User with this email already exists"}
    
    # Проверяем, что количество пользователей не изменилось
    assert len(db._users) == len(initial_users)

def test_delete_user():
    '''Удаление пользователя'''
    setup_module()
    # Проверяем удаление существующего пользователя
    user_to_delete = initial_users[0]
    delete_response = client.delete("/api/v1/user", params={'email': user_to_delete['email']})
    assert delete_response.status_code == 204
    
    # Проверяем что пользователь удален
    assert db.get_user_by_email(user_to_delete['email']) is None
    assert len(db._users) == len(initial_users) - 1
    
    # Проверяем удаление несуществующего пользователя
    non_existent_email = "nonexistent@mail.com"
    delete_response = client.delete("/api/v1/user", params={'email': non_existent_email})
    assert delete_response.status_code == 204  # Удаление несуществующего тоже успешно
