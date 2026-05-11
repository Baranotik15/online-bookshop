import pytest
from unittest.mock import patch
from django.core import signing
from django.core.management import call_command
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from .models import User
from .tasks import send_confirmation_email


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def active_user():
    return User.objects.create_user(
        email='active@example.com', username='activeuser', password='pass1234', is_active=True
    )


# --- Registration ---

@pytest.mark.django_db
def test_register_creates_inactive_user(client):
    r = client.post('/register/', {
        'email': 'new@example.com',
        'username': 'newuser',
        'password1': 'StrongPass123!',
        'password2': 'StrongPass123!',
    })
    assert r.status_code in (200, 302)
    user = User.objects.get(email='new@example.com')
    assert not user.is_active


@pytest.mark.django_db
@pytest.mark.parametrize('email', [
    'user1@example.com',
    'user2@gmail.com',
    'user3@test.org',
])
def test_register_various_emails(client, email):
    r = client.post('/register/', {
        'email': email,
        'username': email.split('@')[0],
        'password1': 'StrongPass123!',
        'password2': 'StrongPass123!',
    })
    assert r.status_code in (200, 302)
    assert User.objects.filter(email=email).exists()


@pytest.mark.django_db
def test_register_duplicate_email_rejected(client, active_user):
    r = client.post('/register/', {
        'email': active_user.email,
        'username': 'newusername',
        'password1': 'StrongPass123!',
        'password2': 'StrongPass123!',
    })
    assert User.objects.filter(email=active_user.email).count() == 1


@pytest.mark.django_db
def test_register_password_mismatch_rejected(client):
    r = client.post('/register/', {
        'email': 'mismatch@example.com',
        'username': 'mismatchuser',
        'password1': 'StrongPass123!',
        'password2': 'WrongPass456!',
    })
    assert not User.objects.filter(email='mismatch@example.com').exists()


# --- Email confirmation ---

@pytest.mark.django_db
def test_confirm_email_activates_user(client):
    user = User.objects.create_user(
        email='confirm@example.com', username='confirmuser', password='pass1234', is_active=False
    )
    token = signing.dumps(user.pk, salt='email-confirmation')
    r = client.get(f'/confirm-email/{token}/')
    assert r.status_code in (200, 302)
    user.refresh_from_db()
    assert user.is_active


@pytest.mark.django_db
def test_invalid_token_does_not_activate(client):
    user = User.objects.create_user(
        email='noactivate@example.com', username='noactivate', password='pass1234', is_active=False
    )
    r = client.get('/confirm-email/invalid-token-xyz/')
    user.refresh_from_db()
    assert not user.is_active


# --- Login ---

@pytest.mark.django_db
def test_login_inactive_user_rejected(client):
    User.objects.create_user(
        email='inactive@example.com', username='inactiveuser', password='pass1234', is_active=False
    )
    r = client.post('/login/', {'username': 'inactive@example.com', 'password': 'pass1234'})
    assert r.status_code in (200, 302)
    assert not r.wsgi_request.user.is_authenticated


@pytest.mark.django_db
def test_login_active_user_succeeds(client, active_user):
    r = client.post('/login/', {'username': active_user.email, 'password': 'pass1234'})
    assert r.wsgi_request.user.is_authenticated


# --- Profile ---

@pytest.mark.django_db
def test_profile_requires_login(client):
    r = client.get('/profile/')
    assert r.status_code in (302, 403)


@pytest.mark.django_db
def test_profile_accessible_when_authenticated(client, active_user):
    client.force_login(active_user)
    r = client.get('/profile/')
    assert r.status_code == 200


# --- Register redirect for authenticated ---

@pytest.mark.django_db
def test_register_redirects_if_authenticated(client, active_user):
    client.force_login(active_user)
    r = client.get('/register/')
    assert r.status_code == 302


# --- Confirm email error cases ---

@pytest.mark.django_db
def test_confirm_email_expired_token(client):
    with patch('users.views.web.signing.loads') as mock_loads:
        mock_loads.side_effect = signing.SignatureExpired('expired')
        r = client.get('/confirm-email/any-token/')
    assert r.status_code == 302


@pytest.mark.django_db
def test_confirm_email_bad_signature(client):
    r = client.get('/confirm-email/completely-invalid-token/')
    assert r.status_code == 302


# --- Edit profile ---

@pytest.mark.django_db
def test_edit_profile_get(client, active_user):
    client.force_login(active_user)
    r = client.get('/profile/edit/')
    assert r.status_code == 200


@pytest.mark.django_db
def test_edit_profile_post_updates_username(client, active_user):
    client.force_login(active_user)
    r = client.post('/profile/edit/', {'username': 'newname', 'email': active_user.email})
    assert r.status_code == 302
    active_user.refresh_from_db()
    assert active_user.username == 'newname'


# --- Celery task ---

@pytest.mark.django_db
def test_send_confirmation_email_task(active_user):
    with patch('users.tasks.send_mail') as mock_send:
        send_confirmation_email(active_user.pk, 'http://example.com/confirm/token/')
        mock_send.assert_called_once()
        _, kwargs = mock_send.call_args
        assert active_user.email in kwargs.get('recipient_list', [])


@pytest.mark.django_db
def test_register_triggers_email_task(client):
    with patch('users.views.web.send_confirmation_email.delay') as mock_delay:
        client.post('/register/', {
            'email': 'celery@example.com',
            'username': 'celeryuser',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        mock_delay.assert_called_once()


# --- Management command ---

@pytest.mark.django_db
def test_create_groups_creates_three_groups():
    call_command('create_groups', verbosity=0)
    assert Group.objects.filter(name='Edit Books').exists()
    assert Group.objects.filter(name='Edit Orders').exists()
    assert Group.objects.filter(name='Edit Users').exists()


@pytest.mark.django_db
def test_create_groups_replaces_existing():
    Group.objects.create(name='Old Group')
    call_command('create_groups', verbosity=0)
    assert not Group.objects.filter(name='Old Group').exists()
    assert Group.objects.count() == 3
