def update_activity(user):
    """Aktualizuje czas ostatniej aktywności użytkownika, jezeli taki użytkownik istnieje."""

    if user:
        user.update_last_activity_time()
