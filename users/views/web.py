from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core import signing
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django import forms

from users.models import User
from orders.models import Order

CONFIRM_SALT = 'email-confirmation'
CONFIRM_MAX_AGE = 60 * 60 * 24  # 24 hours


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput, label='Пароль')
    password2 = forms.CharField(widget=forms.PasswordInput, label='Підтвердіть пароль')

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Паролі не збігаються')
        if p1:
            try:
                validate_password(p1)
            except ValidationError as e:
                raise forms.ValidationError(e.messages)
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.is_active = False
        if commit:
            user.save()
        return user


class EditProfileForm(forms.ModelForm):
    new_password = forms.CharField(
        widget=forms.PasswordInput, label='Новий пароль', required=False
    )

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean_new_password(self):
        pw = self.cleaned_data.get('new_password')
        if pw:
            try:
                validate_password(pw)
            except ValidationError as e:
                raise forms.ValidationError(e.messages)
        return pw

    def save(self, commit=True):
        user = super().save(commit=False)
        pw = self.cleaned_data.get('new_password')
        if pw:
            user.set_password(pw)
        if commit:
            user.save()
        return user


def _send_confirmation_email(request, user):
    token = signing.dumps(user.pk, salt=CONFIRM_SALT)
    confirm_url = request.build_absolute_uri(f'/confirm-email/{token}/')
    body = render_to_string('users/email_confirm.html', {
        'user': user,
        'confirm_url': confirm_url,
    })
    send_mail(
        subject='Підтвердіть email — BookShop',
        message=body,
        from_email=None,
        recipient_list=[user.email],
        fail_silently=False,
    )


def register(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            _send_confirmation_email(request, user)
            return render(request, 'users/register.html', {
                'form': RegisterForm(),
                'email_sent': True,
                'email': user.email,
            })
    else:
        form = RegisterForm()
    return render(request, 'users/register.html', {'form': form})


def confirm_email(request, token):
    try:
        user_pk = signing.loads(token, salt=CONFIRM_SALT, max_age=CONFIRM_MAX_AGE)
        user = User.objects.get(pk=user_pk)
        user.is_active = True
        user.save()
        messages.success(request, 'Email підтверджено! Тепер ви можете увійти.')
        return redirect('/login/')
    except signing.SignatureExpired:
        messages.error(request, 'Посилання для підтвердження застаріло. Зареєструйтесь знову.')
        return redirect('/register/')
    except (signing.BadSignature, User.DoesNotExist):
        messages.error(request, 'Невалідне посилання для підтвердження.')
        return redirect('/register/')


def _orders(user):
    return Order.objects.filter(user=user).prefetch_related('items__book').order_by('-created_at')


@login_required
def profile(request):
    return render(request, 'users/profile.html', {'orders': _orders(request.user)})


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            login(request, request.user)
            return redirect('/profile/')
    else:
        form = EditProfileForm(instance=request.user)
    return render(request, 'users/edit_profile.html', {'form': form})
