import datetime


def calendar(time):
    """Usuwa z daty informajce niedotyczące kalendarza"""
    return time.replace(hour=0, minute=0, second=0, microsecond=0)


def relative_time(creation_time, now):
    """Oblicza czas jaki upłynął od podanej w argumencie daty, do teraz. Zwraca sformatowany napis."""

    # ogólna różnica czasu
    time = now - datetime.datetime(creation_time.year, creation_time.month,
                                   creation_time.day, creation_time.hour, creation_time.minute, creation_time.second)
    creation_time_ = datetime.datetime(creation_time.year, creation_time.month, creation_time.day, creation_time.hour, creation_time.minute, creation_time.second)

    if (time.days < 0):
        return "0 sekund temu"

    # różnica (na podstawie kalendarza)
    years = (now.year - creation_time.year) - (now.month < creation_time.month or (
        now.month == creation_time.month and now.day < creation_time.day))
    if (now.year - creation_time.year > 0) and (now.month == creation_time.month):
        months = 12*years + 11*(now.day < creation_time.day)
    else:
        months = 12*years + (now.month - creation_time.month) % 12 - \
            (now.day < creation_time.day and now.month != creation_time.month)

    days = time.days
    weeks = int(days/7)

    # różnica (na podstawie zegara)
    seconds = time.seconds
    minutes = int(seconds/60)
    hours = int(seconds/3600)

    # względne miesiace w roku i dni w tygodniu
    rel_months = months % 12
    rel_days = days % 7

    # względne tygodnie (typu "x miesięcy i y tygodni temu')
    first = now.replace(day=1) 								# pierwszy dzien aktualnego miesiaca
    # ostatni dzien poprzedniego miesiaca
    last = first - datetime.timedelta(days=1)
    month_ago = last.replace(day=min(last.day, now.day))		# miesiać temu
    if (months == 1):
        rel_weeks = int(
            ((calendar(month_ago) - calendar(creation_time_)).days)/7)
    else:
        rel_weeks = 0

    # względne sekundy, minuty i godziny
    rel_seconds = seconds % 60
    rel_minutes = minutes % 60
    rel_hours = hours % 24

    # dni, minuty itd. które są odmieniane inaczej
    format_set = [2, 3, 4, 22, 23, 24, 32, 33, 34, 42, 43, 44, 52, 53, 54]

    if years:
        out = str(years)
        if years == 1:
            out += ' rok'
        elif years in format_set:
            out += ' lata'
        else:
            out += ' lat'
        if rel_months and years == 1:
            out += ' i ' + str(rel_months)
            if rel_months == 1:
                out += ' miesiąc'
            elif rel_months in format_set:
                out += ' miesiące'
            else:
                out += ' miesięcy'
    elif months:
        out = str(months)
        if months == 1:
            out += ' miesiąc'
        elif months in format_set:
            out += ' miesiące'
        else:
            out += ' miesięcy'
        if rel_weeks and months == 1:
            out += ' i ' + str(rel_weeks)
            if rel_weeks == 1:
                out += ' tydzień'
            else:
                out += ' tygodnie'
    elif weeks:
        out = str(weeks)
        if weeks == 1:
            out += ' tydzień'
        else:
            out += ' tygodnie'
        if rel_days and weeks == 1:
            out += ' i ' + str(rel_days)
            if rel_days == 1:
                out += ' dzień'
            else:
                out += ' dni'
    elif days:
        out = str(days)
        if days == 1:
            out += ' dzień'
        else:
            out += ' dni'
        if rel_hours and days == 1:
            out += ' i ' + str(rel_hours)
            if rel_hours == 1:
                out += ' godzinę'
            elif rel_hours in format_set:
                out += ' godziny'
            else:
                out += ' godzin'
    elif hours:
        out = str(hours)
        if hours == 1:
            out += ' godzinę'
        elif hours in format_set:
            out += ' godziny'
        else:
            out += ' godzin'
        if rel_minutes and hours == 1:
            out += ' i ' + str(rel_minutes)
            if rel_minutes == 1:
                out += ' minutę'
            elif rel_minutes in format_set:
                out += ' minuty'
            else:
                out += ' minut'
    elif minutes:
        out = str(minutes)
        if minutes == 1:
            out += ' minutę'
        elif minutes in format_set:
            out += ' minuty'
        else:
            out += ' minut'

        if rel_seconds and minutes == 1:
            out += ' i ' + str(rel_seconds)
            if rel_seconds == 1:
                out += ' sekundę'
            elif rel_seconds in format_set:
                out += ' sekundy'
            else:
                out += ' sekund'
    else:
        out = str(int(seconds))
        if rel_seconds == 1:
            out += ' sekundę'
        elif rel_seconds in format_set:
            out += ' sekundy'
        else:
            out += ' sekund'

    return out + ' temu'
