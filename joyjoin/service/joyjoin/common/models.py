import datetime
import re

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.db import models, transaction
from django.utils import timezone
from django.utils.dateparse import parse_date

from common.relative_time import relative_time
from common.sanitizer import is_sanitary


class User(models.Model):
    """ Klasa reprezentująca użytkownika.

    Attributes:
        login (str): login użytkownika, używany do logowania i widoczny w URLach
        password (str): hasło użytkownika, przechowywane jako skrót PBKDF2
        email (str): adres email użytkownika, obecnie jeszcze nieużywany w praktyce
        birth_date (datetime.date): data urodzenia użytkownika
        creation_time (datetime.datetime): czas utworzenia modelu tego użytkownika w bazie danych
        description (str): opis własny użytkownika, użytkownik może go edytować i wyświetla się na jego stronie
        last_activity_time (datetime.datetime): czas ostatniej aktywności użytkownika
        last_update_punctation_time (datetime.datetime): czas ostatniej aktualizacji punktacji w tabeli TagPunctation dla danego użytkownika
        is_punctation_changeable (bool): True, gdy użytkownik zezwala na modyfikację punktacji w tabeli TagPunctation, False wpw.
    """
    login = models.CharField(max_length=31, unique=True)
    password = models.CharField(max_length=511)
    email = models.CharField(max_length=127)
    name = models.CharField(max_length=63)
    birth_date = models.DateField()
    creation_time = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=511, blank=True)
    last_activity_time = models.DateTimeField(auto_now_add=True)
    last_update_punctation_time = models.DateTimeField(auto_now_add=True)
    is_punctation_changeable = models.BooleanField(default=True)
    image = models.ImageField(
        default='default.jpg', width_field="width_field", height_field="height_field")
    image_mini = models.ImageField(default='default_mini.jpg')
    height_field = models.IntegerField(null=True)
    width_field = models.IntegerField(null=True)

    def __str__(self):
        return self.login

    def save(self, *args, **kwargs):
        """
        Sprawdza poprawność modelu użytkownika.
        Jeśli model jest poprawny, zapisuje go w bazie.
        Jeśli tworzony jest nowy model użytkownika to dla każdego istniejącego tagu dodaje rekord w tabeli TagPunctation z punktacjami nowego użytkownika.
        Jeśli model nie jest poprawny zwraca django.core.expections.ValidationError
        """
        data = {
            'login': self.login,
            'password': self.password,
            'email': self.email,
            'name': self.name,
            'birth_date': self.birth_date,
            'creation_time': self.creation_time,
            'description': self.description,
            'last_activity_time': self.last_activity_time,
        }
        result = User.validate(data, source='model')
        if result[0] == 'OK':
            with transaction.atomic():
                super().save(*args, **kwargs)

                # Jezeli tworzony jest nowy użytkownik to dodaje nowe rekordy do tabeli TagPunctation
                if not TagPunctation.objects.filter(user=self).exists():
                    for tag in Tag.objects.all():
                        tp = TagPunctation()
                        tp.user = self
                        tp.tag = tag
                        tp.punctation = 0
                        tp.save()
        else:
            raise ValidationError(
                'Nie można zapisać modelu: {}'.format(result[1]))

    def validate(data, source='register'):
        """
        Sprawdza czy przekazane dane są poprawne.
        Zwraca listę dwuelemntową:
            * jeśli walidacja przebiegła poprawnie pierwszy element listy to 'OK'
            * w przeciwnym wypadku, pierwszy element listy to inny niepusty string
            * drugi element listy to przyjazny dla człowieka opis
        Parametr 'source' określa rodzaj walidacji:
            'model': oznacza, że walidacja sprawdza czy dane modelu są poprawne i mogą być zapisane
            'register': wartość domyślna, oznaczna że walidowane są dane przy rejestracji
            'settings': oznacza że walidadowane są dane z aplikacji settings
        """

        # Sprawdza czy źródło jest jedną z prawidłowych wartości
        if source not in ['model', 'register', 'settings']:
            raise ValueError

        try:
            login = data['login']
            name = data['name']
            email = data['email']
            if source == 'model':
                password = data['password']
            elif source in ['register', 'settings']:
                passwd1 = data['password']
                passwd2 = data['password_2']
            if source == 'model':
                birth_date = data['birth_date']
            elif source in ['register', 'settings']:
                date_string = data['birth_date']
            if source == 'model':
                creation_time = data['creation_time']
            if source in ['model', 'settings']:
                description = data['description']
            if source == 'model':
                last_activity_time = data['last_activity_time']
            if source == 'register':
                acceptance = data['rules']
        except KeyError:
            return ['post_error', 'Błąd POST']

        # Sprawdzanie poprawności i unikalności loginu
        if not 3 <= len(login) <= 20:
            return ['login_wrong_length', 'Login musi mieć od 3 do 20 znaków']

        for letter in login:
            if not (letter.islower() or letter.isnumeric() or letter == '_'):
                return ['login_forbidden_characters', 'Login musi się składać wyłącznie z małych liter, cyfr lub znaku "_"']

        if not login[0].islower():
            return ['login_forbidden_first_character', 'Login musi zaczynać się od litery']

        if source == 'register':
            for user in User.objects.all():
                if user.login == login:
                    return ['login_used', 'Login jest już zajęty']

        # Sprawdzanie imienia i nazwiska (nazwy)
        if not 3 <= len(name) <= 63:
            return ['name_wrong_length', 'Imię i nazwisko muszą mieć od 3 do 63 znaków']

        for letter in name:
            if not (letter.isalpha() or letter == ' '):
                return ['name_forbidden_characters', 'Imię i nazwisko muszą składać się tylko z liter']

        # Sprawdzanie adresu email
        email_validator = EmailValidator()
        try:
            email_validator(email)
        except ValidationError:
            return ['email_wrong_format', 'Błędny adres email']

        # Sprawdzanie hasła
        if source == 'register' or (source == 'settings' and (passwd1 or passwd2)):
            if passwd1 != passwd2:
                return ['password_different_passwords', 'Hasła nie są identyczne']
            try:
                validate_password(passwd1)
            except ValidationError as errors:
                for error in errors:
                    if error.startswith('To hasło jest za krótkie. Musi zawierać co najmniej 8 znaków.'):
                        return ['password_too_short', 'Hasło jest za krótkie. Musi zawierać minimum 8 znaków.']
                    if error.startswith('To hasło jest zbyt powszechne.'):
                        return ['password_too_common', 'Hasło jest zbyt proste.']
                    if error.startswith('Hasło składa się wyłącznie z cyfr.'):
                        return ['password_is_numeric', 'Hasło nie może składać się tylko z cyfr.']
        elif source == 'model':
            regex = re.compile(
                'pbkdf2_sha256\\$[1-9][0-9]*\\$[a-zA-Z0-9+/]+(=){0,2}\\$[a-zA-Z0-9+/]+(=){0,2}$')
            if not regex.fullmatch(password):
                return ['password_improperly_formated', 'Hasło jest źle sformatowane']

        # Sprawdzanie daty
        if source in ['register', 'settings']:
            try:
                date = parse_date(date_string)
            except ValueError:
                return ['age_wrong_format', 'Zły format daty']
            if date is None:
                return ['age_wrong_format', 'Zły format daty']
            age = timezone.now().date() - date
        elif source == 'model':
            if type(birth_date) == str:
                birth_date = parse_date(birth_date)
            age = timezone.now().date() - birth_date
        if not 12 * 365.25 <= age.days <= 120 * 365.25:
            return ['age_wrong_date', 'Musisz być w wieku między 12 a 120 lat aby założyć konto']

        # Sprawdzanie czasu utworzenia
        if source == 'model':
            if creation_time is not None:
                if creation_time > timezone.now():
                    return ['creation_time_in_the_future', 'Czas utworzenia użytkownika jest w przyszłości']
                if creation_time.date() < birth_date:
                    return ['creation_time_before_birth', 'Czas utworzenia użytkownika jest przed jego narodzeniem']

        # Sprawdzanie opisu
        if source in ['model', 'settings'] and description is not None and len(description) > 511:
            return ['description_too_long', 'Opis nie może być dłuższy niż 511 znaków.']

        # Sprawdzanie czasu ostatniej aktywności
        if source == 'model':
            if last_activity_time is not None:
                if last_activity_time > timezone.now():
                    return ['last_activity_time_in_the_future', 'Czas ostatniej aktywności użytkownika jest w przyszłości']
                if last_activity_time < creation_time:
                    return ['creation_time_before_creation', 'Czas ostatniej aktywności użytkownika jest przed utworzeniem użytkownika']
        # Sprawdzanie akceptacji regulaminu
        if source == 'register' and not acceptance == 'on':
            return ['rules_not_accepted', 'Aby założyć konto, wymagana jest akceptacja regulaminu']

        # Walidacja przebiegla pomyslnie
        return ['OK', 'Dziękujemy za założenie konta! Zapraszamy do korzystania z JoyJoin!']

    def update_last_activity_time(self):
        """
        Aktualizuje czas ostatniej aktywności użytkownika do chwili obecnej.
        Ta funkcja powinna być wywołana przez widoki przy każdej aktywności zalogowanego użytkownika.
        """
        self.last_activity_time = timezone.now()
        self.save()

    def update_last_update_punctation_time(self):
        """
        Aktualizuje czas ostatniej zmiany preferencji użytkownika.
        """
        self.last_update_punctation_time = timezone.now()
        self.save()

    def last_activity_rel_time(self):
        """
        Zwraca str opisujący czas ostatniej aktywności użytkownika względnie do chwili obecnej.
        Jeżeli ostatnia aktywność nastąpiła wcześniej niż minutę temu to zostaje zwrócony napis 'teraz'.
        Przykładowa wartość zwracana: '35 minut temu'
        """
        result = relative_time(self.last_activity_time, datetime.datetime.now())
        if result.split(' ')[1].startswith('sekund'):
            result = 'teraz'
        return result


class Section(models.Model):
    """ Klasa reprezentująca sekcję portalu.

    Attributes:
        name (str): nazwa sekcji
        description (str): opis sekcji
        users: iterowalny obiekt zawierający użytkowików należących do tej
            sekcji jako obiekty common.models.User
        icon: nazwa ikony tej sekcji (str)
    """
    name = models.CharField(max_length=63)
    description = models.CharField(max_length=255)
    users = models.ManyToManyField(User)
    icon = models.CharField(max_length=63, default='laptop')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        Sprawdza czy ten model sekcji jest poprawny.
        Jeśli jest, zapisuje go w bazie danych.
        Jeśli nie jest, podnosi django.core.exceptions.ValidationError
        """
        result = self.validate()
        if result == 'OK':
            super().save(*args, **kwargs)
        else:
            raise ValidationError(
                'Nie można zapisać common.models.Section: {}'.format(result))

    def validate(self):
        """
        Sprawdza czy ten obiekt jest poprawny i może być zapisany w bazie.
        Zwraca 'OK' jeśli tak i str z wyjaśnieniem problemu jeśli nie.
        """
        allowed_icons = ['laptop', 'brush', 'soccer-ball', 'art-gallery', 'music', 'gamepad', 'videocam', 'user-pair']
        if self.icon not in allowed_icons:
            return 'błędna ikona sekcji'

        return 'OK'


class Tag(models.Model):
    """ Ta klasa reprezentuje tag.

    Attributes:
        name: nazwa tagu
        section: sekcja do której należy tag
        slug: nazwa tagu w wersji, która wygląda dobrze w URL lub NULL jeśli nazwa wystarczy
        tooltip: krótki opis tagu, który wyświetla się np. po najechaniu myszą
        _level: poziom tagu w hierarchi implikacji, tylko funkcja TagImplication.save() ma prawo go zmieniać
    """
    name = models.CharField(max_length=31)
    section = models.ForeignKey(Section, on_delete=models.SET_NULL, blank=True, null=True)
    slug = models.CharField(max_length=31, blank=True, null=True)
    tooltip = models.CharField(max_length=63)
    _level = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return '[{}] ({}) {}'.format(self._level, self.section.name, self.name)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)

            # Jezeli tworzony jest nowy tag to tworzy nowe rekordy w tabeli TagPunctation
            if not TagPunctation.objects.filter(tag=self).exists():
                for user in User.objects.all():
                    tp = TagPunctation()
                    tp.user = user
                    tp.tag = self
                    tp.punctation = 0
                    tp.save()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'section'], name='tag_unique_name_section'),
            models.UniqueConstraint(
                fields=['slug', 'section'], name='tag_unique_slug_section'),
        ]

    def slug_or_name(self):
        """
        Zwraca slug lub nazwę, jeśli slug nie istnieje
        """
        if self.slug:
            return self.slug
        return self.name


class TagImplication(models.Model):
    """ Klasa reprezentująca relację implikacji między tagami.

    Note:
        Tag implikujący i implikowany muszą należeć do tej samej sekcji.

    Attributes:
        parent: tag implikujący
        child: tag implikowany
    """
    parent = models.ForeignKey(
        Tag, related_name='parent', on_delete=models.CASCADE, blank=False, null=False)
    child = models.ForeignKey(
        Tag, related_name='child', on_delete=models.CASCADE, blank=False, null=False)

    @property
    def section(self):
        """common.models.Section: Sekcja do której należy implikacja."""
        return self.parent.section

    def save(self, *args, **kwargs):
        """
        Zapisuje nową implikację upewniając się że nie powstaje cykl.
        """
        if self.child.section != self.parent.section:
            raise ValidationError(
                'Implikacja nie może zostać zapisana: tagi należą do różnych sekcji')

        call_stack = []
        call_stack.append((self.child._level + 1, self.parent))
        visited = {self.child}
        with transaction.atomic():
            while call_stack:
                call = call_stack.pop()
                target_level = call[0]
                vertex = call[1]
                if vertex._level < target_level:
                    if vertex in visited:
                        raise ValidationError(
                            'Implikacja {} nie może zostać zapisana, ponieważ tworzy pętlę'.format(self))
                    visited.add(vertex)
                    vertex._level = target_level
                    vertex.save()
                    parents = set()
                    for each in TagImplication.objects.filter(parent__section=self.section, child=vertex):
                        parents.add(each.parent)
                    for each in parents:
                        call_stack.append((target_level + 1, each))
            super().save(args, kwargs)

    def __str__(self):
        return '({}) {} --> {}'.format(self.section.name, self.parent.name, self.child.name)


max_comments_in_sec_view = 2


class Post(models.Model):
    """ Klasa reprezentująca post na stronie.

    Attributes:
        text (str): treść posta
        title (str): tytuł posta (str)
        author (common.models.User): autor posta
            lub None jeśli autor został usunięty
        section (common.models.Section): sekcja do której należy post
            lub None jeśli sekcja została usunięta
        creation_time (datetime.datetime): czas utworzenia posta
        tags: iterowalny obiekt zawierający tagi źródłowe posta
        implied_tags: iterowalny obiekt zawierający tagi implikowane posta
        user_tags: str zawierający tagi użytkownicze posta, oddzielone spacjami
        punctation (float): początkowa punktacja posta
    """
    text = models.TextField()
    title = models.CharField(max_length=63)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    section = models.ForeignKey(Section, on_delete=models.SET_NULL, blank=True, null=True)
    creation_time = models.DateTimeField(auto_now_add=True)
    # tagi implikowane przez tagi dodane przez użytkownika
    implied_tags = models.ManyToManyField(Tag, related_name='implied_tags', blank=True)
    # tagi dodane przez użytkownika, ale nienależące do implied_tags
    tags = models.ManyToManyField(Tag, related_name='tags', blank=True)
    user_tags = models.CharField(max_length=255, blank=True)
    punctation = models.FloatField(default=0)

    def save(self, *args, **kwargs):
        """
        Zapisuje model posta upewniając się że jest poprawny.
        """
        # Post nie zawiera złego HTML
        if not is_sanitary(self.text):
            raise ValidationError('Post nie może zostać zapisany: treść zawiera zły HTML.')
        # Czasy mają sens
        if self.creation_time is not None:
            if self.creation_time > timezone.now():
                raise ValidationError(
                    'Post nie może zostać zapisany: data utworzenia w przyszłości.')
            delta = timezone.now() - self.creation_time
            if delta.days > 0 and not Post.objects.filter(id=self.id).exists():
                raise ValidationError(
                    'Post nie może zostać zapisany: data utworzenia co najmniej dzień w przeszłości.')
        # User tags ma dobrą formę
        if self.user_tags is not None:
            if not len(self.user_tags) < 256:
                raise ValidationError(
                    'Bład przy tworzeniu posta: tagi użytkownika mają za dużą łączną długość ({}/{})'.format(
                        len(self.user_tags),
                        256)
                )
            for user_tag in self.user_tags.split(' '):
                if len(user_tag) > 31:
                    raise ValidationError(
                        'Błąd przy tworzeniu posta: jeden z tagów użytkownika ("{}") jest za długi ({}/{})'.format(
                            user_tag,
                            len(user_tag),
                            31)
                    )
        super().save(args, kwargs)

    def __str__(self):
        return 'post {} użytkownika {} w sekcji {}'.format(
            self.pk,
            self.author.login,
            self.section.name
        )

    def count_votes(self, reaction=None):
        """
        Liczy głosy danego typu (lub wszystkie gdy nie dano argumentu 'reaction')
        """
        if reaction:
            return Vote.objects.filter(post=self, reaction=reaction).count()
        return Vote.objects.filter(post=self).count()

    def user_tags_as_list(self):
        """
        Zwraca tagi użytkownika jako listę elementów typu str
        """
        if self.user_tags:
            return self.user_tags.split(" ")
        return []

    def creation_rel_time(self):
        """
        Zwraca str opisujący czas utworzenia posta względnie do chwili obecnej.
        Przykładowa wartość zwracana: '35 minut temu'
        """
        return relative_time(self.creation_time, datetime.datetime.now())

    def count_all_comments(self):
        """
        Zwraca liczbę wszystkich komentarzy pod postem (bezpośrednio i pośrednio pod postem)
        """
        return Comment.objects.filter(parent_post=self).count()

    def get_top_level_comments(self, num_of_comments='all'):
        """
        Zwraca komentarze bezpośrednio pod postem
        """
        if num_of_comments == 'all':
            return Comment.objects.filter(parent_post=self, parent_comment=None)
        else:
            return Comment.objects.filter(parent_post=self, parent_comment=None)[:num_of_comments]

    def count_remaining_comments(self):
        """
        Liczy ile komentarzy nie zostało jeszcze wyświetlonych (widok sekcji)
        Przykładowo: w widoku sekcji pod postem wyswietlono x komentarzy, a wszystkich komentarzy jest y
        więc zostało y - x komentarzy do wyświetlenia.
        """
        return self.count_all_comments() - self.get_top_level_comments(max_comments_in_sec_view).count()


comment_max_depth = 10


class Comment(models.Model):
    """ Klasa reprezentująca komentarz na stronie.

    Attributes:
        text: treść komentarza (str)
        author: autor komentarza (common.models.User)
            lub None jeśli autor został usunięty
        creation_time: czas utworzenia komentarza (datetime.datetime)
        parent_post: nadrzędny post pod którym (pośrednio lub bezpośrednio)
            znajduje się ten komentarz (common.models.Post)
        parent_comment: nadrzędny komentarz pod którym (bezpośrednio)
            znajduje się ten komentarz (common.models.Comment)
        depth: głębokość komentarza, gdzie komentarz bezpośrednio
            pod postem ma głębokość równą 1 (int)
    """
    text = models.TextField()
    author = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    creation_time = models.DateTimeField(auto_now_add=True)
    parent_post = models.ForeignKey(Post, on_delete=models.CASCADE)
    parent_comment = models.ForeignKey(
        'Comment', on_delete=models.CASCADE, blank=True, null=True)
    depth = models.SmallIntegerField(blank=True, null=True)

    def __str__(self):
        if self.parent_comment:
            return 'komentarz {} użytkownika {} pod postem {} pod komentarzem {} (głębokość: {})'.format(
                self.pk,
                self.author.login,
                self.parent_post.pk,
                self.parent_comment.pk,
                self.get_depth()
            )
        else:
            return 'komentarz {} użytkownika {} pod postem {} (głębokość: {})'.format(
                self.pk,
                self.author.login,
                self.parent_post.pk,
                self.get_depth()
            )

    def creation_rel_time(self):
        """
        Zwraca względny czas od utworzenia komentarza
        """
        return relative_time(self.creation_time, datetime.datetime.now())

    def get_direct_replies(self):
        """
        Zwraca odpowiedzi (komentarze) bezpośrednio pod komentarzem
        """
        return Comment.objects.filter(parent_comment=self)

    def count_direct_replies(self):
        """
        Zwraca liczbe odpowiedzi (komentarzy) bezpośrednio pod komentarzem
        """
        return Comment.objects.filter(parent_comment=self).count()

    def count_votes(self, reaction=None):
        """
        Liczy głosy danego typu (lub wszystkie gdy nie dano argumentu 'reaction')
        """
        if reaction:
            return CommentVote.objects.filter(comment=self, reaction=reaction).count()
        return CommentVote.objects.filter(comment=self).count()

    def count_all_replies(self):
        """
        Zwraca liczbę wszystkich odpowiedzi (bezpośrednio i pośrednio) pod komentarzem
        """
        suma = 0
        for comment in self.get_direct_replies():
            suma += comment.count_all_replies()
        return suma + self.count_direct_replies()

    def get_depth(self):
        """
        Zwraca głębokość komentarza
        Jeżeli pole depth nie jest ustalone, to liczy je i zapisuje w bazie
        """
        if not self.depth:
            depth = 1
            tmp_comment = self
            while tmp_comment.parent_comment:
                tmp_comment = tmp_comment.parent_comment
                depth += 1
            self.depth = depth
            self.save()

        return self.depth

    def is_max_depth(self):
        """
        Zwraca informację czy komentarz osiągnął maksymalną głębokość
        Zwraca True lub False
        """
        return self.get_depth() == comment_max_depth


class CommentVote(models.Model):
    """ Klasa reprezentująca głos użytkownika na komentarz.

    Attributes:
        user (common.models.User): użytkownik bedący autorem komentarza
        comment (common.models.Comment): komentarz na który użytkownik głosował
        reaction (int): rodzaj głosu obecnie dozwolone wartości to:
            +1: głos pozytywny
            -1: głos negatywny
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    reaction = models.SmallIntegerField()

    def __str__(self):
        dictionary = {
            -1: 'downvote',
            +1: 'upvote',
        }
        return '{} użytkownika {} na komentarz {}'.format(
            dictionary[self.reaction],
            self.user.login,
            self.comment.pk
        )

    def get_reaction(self):
        """
        Zwraca wartość reakcji (int)
        """
        return self.reaction


class Vote(models.Model):
    """ Klasa reprezentująca głos użytkownika na post.

    Attributes:
        user (common.models.User): użytkownik bedący autorem posta
        post (common.models.Post): post na który użytkownik głosował
        reaction (int): rodzaj głosu obecnie dozwolone wartości to:
            +1: głos pozytywny
            -1: głos negatywny
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    reaction = models.SmallIntegerField()

    def __str__(self):
        dictionary = {
            -1: 'downvote',
            +1: 'upvote',
        }
        return '{} użytkownika {} na post {}'.format(
            dictionary[self.reaction],
            self.user.login,
            self.post.pk
        )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'post'], name='vote_unique_post_user'),
        ]

    def is_upvote(self):
        """
        Zwraca:
            True jeśli głos to upvote
            False w przeciwnym wypadku
        """
        return self.reaction == 1

    def is_downvote(self):
        """
        Zwraca:
            True jeśli głos to downvote
            False w przeciwnym wypadku
        """
        return self.reaction == -1

    def is_undefined(self):
        """
        Zwraca:
            True jeśli głos to ma dozwolony typ
            False w przeciwnym wypadku
        """
        return self.reaction not in [1, -1]


class PostVisit(models.Model):
    """ Klasa przechowująca ilość wyświetleń danego posta przez danego użytkownika

    Attributes:
        user (common.models.User): użytkownik, który wyświetlił pewien post
        post (common.models.Post): post, który został wyświetlony przez użytkownika
        visit_counter (int): ilość wyświetleń
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    visit_counter = models.SmallIntegerField()

    def __str__(self):
        return '{} wyswietleń posta {} przez użytkownika {}'.format(
            self.visit_counter,
            self.post.pk,
            self.user.login
        )

    def get_visit_counter(self):
        """
        Zwraca licznik wyświetleń (int)
        """
        return self.visit_counter


class TagPunctation(models.Model):
    """ Klasa przechowująca osobistą punktację każdego użytkownika do każdego tagu

    Attributes:
        user (common.models.User): użytkownik, którego tyczy się punktacja
        tag (common.models.Post): tag, którego tyczy się punktacja
        punctation (float): punktacja
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    punctation = models.FloatField()

    def __str__(self):
        return '{} punktacja tagu {} przez użytkownika {}'.format(
            self.punctation,
            self.tag.pk,
            self.user.login
        )

    def get_punctation(self):
        """
        Zwraca punktację (float)
        """
        return self.visit_counter
