from importlib import import_module
from pytz import utc

from django.conf import settings
from django.forms import ValidationError
from django.http import HttpRequest
from django.test import TestCase
from django.utils import timezone

from .context import set_common_context
from .generate_test_data import generate
from common.models import User, Section, Tag, TagImplication, Post, Vote, Comment, CommentVote
from common.models import max_comments_in_sec_view, comment_max_depth
from common.comment_sorting import sort_comments
from common.relative_time import relative_time
import datetime


class ContextTests(TestCase):
    @classmethod
    def setUp(cls):
        generate()

    def test_set_common_context_with_right_user_given_in_session(self):
        # tworzy obiekt HttpRequest i dodaje do niego sesję z SessionMiddleware
        request = HttpRequest()
        session_engine = import_module(settings.SESSION_ENGINE)
        request.session = session_engine.SessionStore()

        # ustawia nieistniejącego użytkownika w sesji
        # tudne: this user does not exist
        request.session['logged_in_as'] = 'monika'

        # woła set_common_context z odpowiednimi danymi
        context = {}
        set_common_context(request, context)

        # sprawdza zmienną 'current_user' z sesji
        self.assertNotEquals(context['current_user'], None)

    def test_set_common_context_with_wrong_user_given_in_session(self):
        # tworzy obiekt HttpRequest i dodaje do niego sesję z SessionMiddleware
        request = HttpRequest()
        session_engine = import_module(settings.SESSION_ENGINE)
        request.session = session_engine.SessionStore()

        # ustawia nieistniejącego użytkownika w sesji
        # tudne: this user does not exist
        request.session['logged_in_as'] = 'tudne'

        # woła set_common_context z odpowiednimi danymi
        context = {}
        set_common_context(request, context)

        # sprawdza zmienną 'current_user' z sesji
        self.assertEquals(context['current_user'], None)


post_model_tests_post_title = 'Poszukiwani chętni do pozowania'
post_model_tests_post_upvotes = 1
post_model_tests_post_downvotes = 1


class PostModelTests(TestCase):
    @classmethod
    def setUp(cls):
        generate()

    def test_count_votes(self):
        post = Post.objects.get(title=post_model_tests_post_title)
        self.assertEqual(
            post.count_votes(),
            post_model_tests_post_upvotes + post_model_tests_post_downvotes
        )
        self.assertEqual(post.count_votes(1), post_model_tests_post_upvotes)
        self.assertEqual(post.count_votes(-1), post_model_tests_post_downvotes)

    def test_attempting_to_save_with_creation_time_in_the_future(self):
        post = Post.objects.first()
        post.creation_time = timezone.now() + timezone.timedelta(1)
        with self.assertRaises(ValidationError):
            post.save()

    def test_attempting_to_save_with_creation_time_too_far_in_the_past(self):
        post = Post()
        post.creation_time = timezone.now() - timezone.timedelta(2)
        with self.assertRaises(ValidationError):
            post.save()

    def test_update_a_post_already_saved(self):
        post = Post.objects.first()
        post.creation_time = timezone.now() - timezone.timedelta(2)
        post.title = post.title[:-1]
        post.save()

    def test_attempting_to_save_with_too_long_user_tags_field(self):
        post = Post.objects.first()
        post.user_tags = 'a ' * 127
        post.save()
        post.user_tags = 'a ' * 128
        with self.assertRaises(ValidationError):
            post.save()

    def test_attempting_to_save_with_one_of_user_tags_too_long(self):
        post = Post.objects.first()
        post.user_tags = 'jakiś-tag ' + 'a' * 32
        with self.assertRaises(ValidationError):
            post.save()

    def test_count_all_comments_with_no_comments(self):
        post = Post.objects.get(title="comment_test")
        self.assertIs(post.count_all_comments(), 0)

    def test_count_all_comments_with_top_level_comments(self):
        post = Post.objects.get(title="comment_test")
        comment1 = Comment(parent_post=post)
        comment1.save()
        comment2 = Comment(parent_post=post)
        comment2.save()

        self.assertIs(post.count_all_comments(), 2)

    def test_count_all_comments_with_top_lvl_and_indirect_comments(self):
        post = Post.objects.get(title="comment_test")
        comment1 = Comment(parent_post=post)
        comment1.save()
        comment2 = Comment(parent_post=post, parent_comment=comment1)
        comment2.save()

        self.assertIs(post.count_all_comments(), 2)

    def test_get_top_level_comments_with_no_comments(self):
        post = Post.objects.get(title="comment_test")
        comments = []
        self.assertEquals(list(post.get_top_level_comments()), comments)

    def test_get_top_level_comments_with_top_lvl_comments(self):
        post = Post.objects.get(title="comment_test")
        comment1 = Comment(parent_post=post)
        comment1.save()
        comment2 = Comment(parent_post=post)
        comment2.save()

        comments = [comment1, comment2]
        self.assertEquals(list(post.get_top_level_comments()), comments)

    def test_get_top_level_comments_with_top_lvl_and_indirect_comments(self):
        post = Post.objects.get(title="comment_test")
        comment1 = Comment(parent_post=post)
        comment1.save()
        comment2 = Comment(parent_post=post, parent_comment=comment1)
        comment2.save()

        comments = [comment1]
        self.assertEquals(list(post.get_top_level_comments()), comments)

    def test_get_top_level_comments_with_argument_smaller_than_top_lvl_comments_num(self):
        post = Post.objects.get(title="comment_test")
        comment1 = Comment(parent_post=post)
        comment1.save()
        comment2 = Comment(parent_post=post)
        comment2.save()
        comment3 = Comment(parent_post=post, parent_comment=comment1)
        comment3.save()

        arg = 1
        comments = [comment1]
        self.assertEquals(list(post.get_top_level_comments(arg)), comments)

    def test_get_top_level_comments_with_argument_bigger_than_top_lvl_comments_num(self):
        post = Post.objects.get(title="comment_test")
        comment1 = Comment(parent_post=post)
        comment1.save()
        comment2 = Comment(parent_post=post)
        comment2.save()
        comment3 = Comment(parent_post=post, parent_comment=comment1)
        comment3.save()

        arg = 3
        comments = [comment1, comment2]
        self.assertEquals(list(post.get_top_level_comments(arg)), comments)

    def test_count_remaining_comments_with_no_comments(self):
        post = Post.objects.get(title="comment_test")
        self.assertEquals(post.count_remaining_comments(), 0)

    def test_count_remaining_comments_with_all_comments_showed(self):
        post = Post.objects.get(title="comment_test")
        for num in range(0, max_comments_in_sec_view):
            comment = Comment(parent_post=post)
            comment.save()
            self.assertEquals(post.count_remaining_comments(), 0)

    def test_count_remaining_comments_with_some_top_lvl_comments_remaining(self):
        post = Post.objects.get(title="comment_test")
        for num_of_direct_comments in range(0, max_comments_in_sec_view + 5):
            comment = Comment(parent_post=post)
            comment.save()
            self.assertEquals(post.count_remaining_comments(), max(
                num_of_direct_comments+1-max_comments_in_sec_view, 0))

    def test_count_remaining_comments_with_one_top_lvl_and_some_indirect_comments(self):
        post = Post.objects.get(title="comment_test")
        direct_comment = Comment(parent_post=post)
        direct_comment.save()

        for num_of_indirect_comments in range(0, max_comments_in_sec_view + 5):
            indirect_comment = Comment(
                parent_post=post, parent_comment=direct_comment)
            indirect_comment.save()
            self.assertEquals(post.count_remaining_comments(),
                              num_of_indirect_comments+1)

    def test_count_remaining_comments_with_top_lvl_and_indirect_comments(self):
        post = Post.objects.get(title="comment_test")

        top_lvl_remaining = 0
        for num in range(0, max_comments_in_sec_view + 5):
            comment = Comment(parent_post=post)
            comment.save()

        parent_comment = Comment(parent_post=post)
        parent_comment.save()

        top_lvl_remaining = 5 + 1
        for num_of_indirect_comments in range(0, max_comments_in_sec_view + 5):
            comment = Comment(parent_post=post, parent_comment=parent_comment)
            comment.save()
            self.assertEquals(post.count_remaining_comments(),
                              top_lvl_remaining + num_of_indirect_comments+1)


class SectionModelTests(TestCase):
    @classmethod
    def setUp(cls):
        generate()

    def test_attempting_to_save_with_wrong_icon(self):
        section = Section.objects.first()
        section.icon = 'wrrrong'
        with self.assertRaises(ValidationError):
            section.save()


class TagImplicationTests(TestCase):
    @classmethod
    def setUp(cls):
        generate()

    def test_attempting_to_save_with_mismatching_sections(self):
        child = Tag.objects.filter(section__name='programming').first()
        parent = Tag.objects.filter(section__name='painting').first()
        ti = TagImplication()
        ti.child = child
        ti.parent = parent
        with self.assertRaises(ValidationError):
            ti.save()

    def test_attempting_to_save_implication_that_closes_a_loop(self):
        child = Tag.objects.filter(
            section__name='programming', name='c++11').first()
        parent = Tag.objects.filter(
            section__name='programming', name='standardy').first()
        ti = TagImplication()
        ti.child = child
        ti.parent = parent
        with self.assertRaises(ValidationError):
            ti.save()


class UserModelTests(TestCase):
    @classmethod
    def setUp(cls):
        generate()

    def test_update_last_activity_time_right(self):
        # sprawdza czy update rzeczywiście aktualizuję czas aktywności
        user = User.objects.get(login="monika")
        time_old = user.last_activity_time
        user.update_last_activity_time()
        time_new = user.last_activity_time

        self.assertIs(time_new >= time_old, True)

    def test_save_with_wrong_email(self):
        user = User.objects.first()
        user.email = 'thisisnotavalid@email'
        with self.assertRaises(ValidationError):
            user.save()

    def test_with_email_with_a_dot(self):
        user = User.objects.first()
        user.email = 'this.is.a.valid.email@joyjoin.space'
        user.save()

    def test_with_email_with_double_dot(self):
        user = User.objects.first()
        user.email = 'this..is.a.valid.email@joyjoin.space'
        with self.assertRaises(ValidationError):
            user.save()

    def test_save_with_wrong_password(self):
        user = User.objects.first()
        user.password = 'bad_password'
        with self.assertRaises(ValidationError):
            user.save()

    def test_validate_with_creation_time_in_the_future(self):
        user = User.objects.first()
        user.creation_time = timezone.now() + timezone.timedelta(1)
        with self.assertRaises(ValidationError):
            user.save()

    def test_validate_with_creation_time_before_birth(self):
        user = User.objects.first()
        user.creation_time = datetime.datetime(1980, 1, 1, 0, 0, 0, 0, utc)
        with self.assertRaises(ValidationError):
            user.save()

    def test_validate_with_last_activity_in_the_future(self):
        user = User.objects.first()
        user.last_activity_time = timezone.now() + timezone.timedelta(1)
        with self.assertRaises(ValidationError):
            user.save()

    def test_validate_with_last_activity_before_creation(self):
        user = User.objects.first()
        user.last_activity_time = user.creation_time - timezone.timedelta(1)
        with self.assertRaises(ValidationError):
            user.save()

    def test_validate_with_wrong_source(self):
        with self.assertRaises(ValueError):
            User.validate(None, source='imwrong')


class RelativeTimeTest(TestCase):
    """
    Testy funkcji relative_time
    """

    # przyszłość

    def test_relative_time_future(self):
        now_time = datetime.datetime(2020, 3, 9, 1, 13, 0)
        then_time = now_time + datetime.timedelta(seconds=1)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "0 sekund temu")

    # sekundy

    def test_relative_time_seconds1(self):
        now_time = datetime.datetime(2020, 3, 9, 1, 13, 0)
        then_time = now_time - datetime.timedelta(seconds=1)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "1 sekundę temu")

    def test_relative_time_seconds2(self):
        now_time = datetime.datetime(2020, 3, 9, 1, 13, 0)
        then_time = now_time - datetime.timedelta(seconds=3)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "3 sekundy temu")

    def test_relative_time_seconds3(self):
        now_time = datetime.datetime(2020, 3, 9, 1, 13, 0)
        then_time = now_time - datetime.timedelta(seconds=5)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "5 sekund temu")

    # minuty

    def test_relative_time_minutes1(self):
        now_time = datetime.datetime(2020, 3, 9, 1, 13, 0)
        then_time = now_time - datetime.timedelta(minutes=1, seconds=0)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "1 minutę temu")

    def test_relative_time_minutes2(self):
        now_time = datetime.datetime(2020, 3, 9, 1, 13, 0)
        then_time = now_time - datetime.timedelta(minutes=2, seconds=4)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "2 minuty temu")

    def test_relative_time_minutes3(self):
        now_time = datetime.datetime(2020, 3, 9, 1, 13, 0)
        then_time = now_time - datetime.timedelta(minutes=5, seconds=4)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "5 minut temu")

    def test_relative_time_minutes4(self):
        now_time = datetime.datetime(2020, 3, 9, 1, 13, 0)
        then_time = now_time - datetime.timedelta(minutes=1, seconds=1)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "1 minutę i 1 sekundę temu")

    def test_relative_time_minutes5(self):
        now_time = datetime.datetime(2020, 3, 9, 1, 13, 0)
        then_time = now_time - datetime.timedelta(minutes=1, seconds=2)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "1 minutę i 2 sekundy temu")

    def test_relative_time_minutes6(self):
        now_time = datetime.datetime(2020, 3, 9, 1, 13, 0)
        then_time = now_time - datetime.timedelta(minutes=1, seconds=5)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "1 minutę i 5 sekund temu")

    # godziny

    def test_relative_time_hours1(self):
        now_time = datetime.datetime(2020, 3, 9, 1, 0, 0)
        then_time = now_time - \
            datetime.timedelta(hours=1, minutes=0, seconds=4)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "1 godzinę temu")

    def test_relative_time_hours2(self):
        now_time = datetime.datetime(2020, 3, 9, 1, 0, 0)
        then_time = now_time - \
            datetime.timedelta(hours=2, minutes=0, seconds=4)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "2 godziny temu")

    def test_relative_time_hours3(self):
        now_time = datetime.datetime(2020, 3, 9, 1, 0, 0)
        then_time = now_time - \
            datetime.timedelta(hours=5, minutes=0, seconds=4)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "5 godzin temu")

    def test_relative_time_hours4(self):
        now_time = datetime.datetime(2020, 3, 9, 1, 0, 0)
        then_time = now_time - \
            datetime.timedelta(hours=1, minutes=1, seconds=4)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "1 godzinę i 1 minutę temu")

    def test_relative_time_hours5(self):
        now_time = datetime.datetime(2020, 3, 9, 1, 0, 0)
        then_time = now_time - \
            datetime.timedelta(hours=1, minutes=2, seconds=4)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "1 godzinę i 2 minuty temu")

    def test_relative_time_hours6(self):
        now_time = datetime.datetime(2020, 3, 9, 1, 0, 0)
        then_time = now_time - \
            datetime.timedelta(hours=1, minutes=5, seconds=4)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "1 godzinę i 5 minut temu")

    # dni

    def test_relative_time_days1(self):
        # 08.03 i 09.03
        now_time = datetime.datetime(2020, 3, 9, 12, 0, 0)
        then_time = now_time - \
            datetime.timedelta(hours=24, minutes=10, seconds=0)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "1 dzień temu")

    def test_relative_time_days2(self):
        # 03.03 i 09.03
        now_time = datetime.datetime(2020, 3, 9, 12, 0, 0)
        then_time = now_time - \
            datetime.timedelta(days=6, hours=23, minutes=0, seconds=4)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "6 dni temu")

    def test_relative_time_days3(self):
        # 08.03 i 09.03
        now_time = datetime.datetime(2020, 3, 9, 12, 0, 0)
        then_time = now_time - \
            datetime.timedelta(days=1, hours=1, minutes=0, seconds=4)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "1 dzień i 1 godzinę temu")

    def test_relative_time_days4(self):
        # 08.03 i 09.03
        now_time = datetime.datetime(2020, 3, 9, 12, 0, 0)
        then_time = now_time - \
            datetime.timedelta(days=1, hours=23, minutes=0, seconds=4)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "1 dzień i 23 godziny temu")

    def test_relative_time_days5(self):
        # 08.03 i 09.03
        now_time = datetime.datetime(2020, 3, 9, 12, 0, 0)
        then_time = now_time - \
            datetime.timedelta(days=1, hours=5, minutes=0, seconds=4)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "1 dzień i 5 godzin temu")

    # tygodnie

    def test_relative_time_weeks1(self):
        # 02.03 i 09.03
        now_time = datetime.datetime(2020, 3, 9, 12, 0, 0)
        then_time = now_time - \
            datetime.timedelta(days=7, hours=1, minutes=0, seconds=4)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "1 tydzień temu")

    def test_relative_time_weeks2(self):
        # 10.02 i 09.03
        now_time = datetime.datetime(2020, 3, 9, 12, 0, 0)
        then_time = now_time - \
            datetime.timedelta(days=28, hours=1, minutes=0, seconds=4)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "4 tygodnie temu")

    def test_relative_time_week3(self):
        # 01.03 i 09.03
        now_time = datetime.datetime(2020, 3, 9, 12, 0, 0)
        then_time = now_time - \
            datetime.timedelta(days=8, hours=1, minutes=0, seconds=4)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "1 tydzień i 1 dzień temu")

    def test_relative_time_week4(self):
        # 25.02 i 09.03
        now_time = datetime.datetime(2020, 3, 9, 12, 0, 0)
        then_time = now_time - \
            datetime.timedelta(days=13, hours=1, minutes=0, seconds=4)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "1 tydzień i 6 dni temu")

    # miesiące

    def test_relative_time_months1(self):
        # 09.02.2020 i 09.03.2020
        now_time = datetime.datetime(2020, 3, 9, 12, 0, 0)
        then_time = datetime.datetime(2020, 2, 3, 23, 59, 59)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "1 miesiąc temu")

    def test_relative_time_months2(self):
        # 10.10.2019 i 09.03.2020
        now_time = datetime.datetime(2020, 3, 9, 12, 0, 0)
        then_time = datetime.datetime(2019, 10, 10, 13, 0, 0)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "4 miesiące temu")

    def test_relative_time_months3(self):
        # 08.10.2019 i 09.03.2020
        now_time = datetime.datetime(2020, 3, 9, 12, 0, 0)
        then_time = datetime.datetime(2019, 10, 8, 13, 0, 0)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "5 miesięcy temu")

    def test_relative_time_month4(self):
        # 02.02.2020 i 09.03.2020
        now_time = datetime.datetime(2020, 3, 9, 12, 0, 0)
        then_time = datetime.datetime(2020, 2, 2, 23, 59, 59)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "1 miesiąc i 1 tydzień temu")

    def test_relative_time_month5(self):
        # 26.01.2020 i 09.03.2020
        now_time = datetime.datetime(2020, 3, 9, 12, 0, 0)
        then_time = datetime.datetime(2020, 1, 26, 23, 59, 0)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "1 miesiąc i 2 tygodnie temu")

    def test_relative_time_not_year(self):
        # 10.03.2019 i 09.03.2020
        now_time = datetime.datetime(2020, 3, 9, 12, 0, 0)
        then_time = datetime.datetime(2019, 3, 10, 13, 0, 0)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "11 miesięcy temu")

    # lata

    def test_relative_time_year1(self):
        # 09.03.2019 i 09.03.2020
        now_time = datetime.datetime(2020, 3, 9, 12, 0, 0)
        then_time = datetime.datetime(2019, 3, 9, 13, 0, 0)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "1 rok temu")

    def test_relative_time_years2(self):
        # 09.02.2018 i 09.03.2020
        now_time = datetime.datetime(2020, 3, 9, 12, 0, 0)
        then_time = datetime.datetime(2018, 2, 9, 13, 0, 0)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "2 lata temu")

    def test_relative_time_years3(self):
        # 09.03.2015 i 09.03.2020
        now_time = datetime.datetime(2020, 3, 9, 12, 0, 0)
        then_time = datetime.datetime(2015, 2, 9, 13, 0, 0)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "5 lat temu")

    def test_relative_time_years4(self):
        # 09.03.2015 i 09.03.2020
        now_time = datetime.datetime(2020, 3, 9, 12, 0, 0)
        then_time = datetime.datetime(2019, 2, 9, 13, 0, 0)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "1 rok i 1 miesiąc temu")

    def test_relative_time_years5(self):
        # 08.12.2018 i 09.03.2020
        now_time = datetime.datetime(2020, 3, 9, 12, 0, 0)
        then_time = datetime.datetime(2018, 12, 8, 13, 0, 0)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "1 rok i 3 miesiące temu")

    def test_relative_time_years6(self):
        # 09.09.2018 i 09.03.2020
        now_time = datetime.datetime(2020, 3, 9, 12, 0, 0)
        then_time = datetime.datetime(2018, 9, 9, 13, 0, 0)
        result = relative_time(then_time, now_time)
        self.assertEqual(result, "1 rok i 6 miesięcy temu")


class VoteModelTests(TestCase):
    def __init__(self, methodName):
        self.upvote = Vote()
        self.upvote.reaction = 1
        self.downvote = Vote()
        self.downvote.reaction = -1
        self.undefined_votes = []
        undefined_reactions = [0, 2, -2, 42, 0xbeef]
        for ur in undefined_reactions:
            undefined_vote = Vote()
            undefined_vote.reaction = ur
            self.undefined_votes.append(undefined_vote)
        TestCase.__init__(self, methodName)

    def test_is_upvote(self):
        self.assertTrue(self.upvote.is_upvote())
        self.assertFalse(self.downvote.is_upvote())
        for uv in self.undefined_votes:
            self.assertFalse(uv.is_upvote())

    def test_is_downvote(self):
        self.assertFalse(self.upvote.is_downvote())
        self.assertTrue(self.downvote.is_downvote())
        for uv in self.undefined_votes:
            self.assertFalse(uv.is_downvote())

    def test_is_undefined(self):
        self.assertFalse(self.upvote.is_undefined())
        self.assertFalse(self.downvote.is_undefined())
        for uv in self.undefined_votes:
            self.assertTrue(uv.is_undefined())


class ModelStrMethodTests(TestCase):
    @classmethod
    def setUp(cls):
        generate()

    def test_str_methods(self):
        # Takie testowanie wystarczy, jako że nic od tego nie zależy
        models = User, Section, Tag, TagImplication, Post, Vote, CommentVote
        for model in models:
            obj = model.objects.first()
            self.assertTrue(str(obj))

    def test_comment_str_method(self):
        comment = Comment.objects.filter(parent_comment__isnull=True).first()
        self.assertTrue(str(comment))
        comment = Comment.objects.filter(parent_comment__isnull=False).first()
        self.assertTrue(str(comment))


class CommentModelTests(TestCase):
    @classmethod
    def setUp(cls):
        generate()

    def test_creation_rel_time_method_exists(self):
        comment = Comment.objects.first()
        comment.creation_rel_time()

    def test_get_direct_replies(self):
        post = Post.objects.get(title="comment_test")
        parent_comment = Comment(parent_post=post)
        parent_comment.save()

        child_comment1 = Comment(
            parent_post=post, parent_comment=parent_comment)
        child_comment1.save()
        child_comment2 = Comment(
            parent_post=post, parent_comment=parent_comment)
        child_comment2.save()
        child_comment3 = Comment(
            parent_post=post, parent_comment=child_comment1)
        child_comment3.save()
        another_comment = Comment(parent_post=post)
        another_comment.save()
        child_comment4 = Comment(
            parent_post=post, parent_comment=another_comment)
        child_comment4.save()

        direct_replies = [child_comment1, child_comment2]
        self.assertEquals(
            list(parent_comment.get_direct_replies()), direct_replies)

    def test_count_direct_replies(self):
        post = Post.objects.get(title="comment_test")
        parent_comment = Comment(parent_post=post)
        parent_comment.save()

        child_comment1 = Comment(
            parent_post=post, parent_comment=parent_comment)
        child_comment1.save()
        child_comment2 = Comment(
            parent_post=post, parent_comment=parent_comment)
        child_comment2.save()
        child_comment3 = Comment(
            parent_post=post, parent_comment=child_comment1)
        child_comment3.save()
        another_comment = Comment(parent_post=post)
        another_comment.save()
        child_comment4 = Comment(
            parent_post=post, parent_comment=another_comment)
        child_comment4.save()
        self.assertEquals(parent_comment.get_direct_replies().count(), 2)

    def test_count_votes_with_reaction_1(self):
        post = Post.objects.get(title="comment_test")
        user1 = User.objects.get(login="monika")
        user2 = User.objects.get(login="piwosz")
        user3 = User.objects.get(login="norbert")

        comment = Comment(parent_post=post)
        comment.save()
        self.assertEquals(comment.count_votes(1), 0)

        cv1 = CommentVote(user=user1, comment=comment, reaction=1)
        cv1.save()
        self.assertEquals(comment.count_votes(1), 1)

        cv2 = CommentVote(user=user2, comment=comment, reaction=1)
        cv2.save()
        self.assertEquals(comment.count_votes(1), 2)

        cv3 = CommentVote(user=user3, comment=comment, reaction=1)
        cv3.save()
        self.assertEquals(comment.count_votes(1), 3)

    def test_count_votes_with_reaction_minus1(self):
        post = Post.objects.get(title="comment_test")
        user1 = User.objects.get(login="monika")
        user2 = User.objects.get(login="piwosz")
        user3 = User.objects.get(login="norbert")

        comment = Comment(parent_post=post)
        comment.save()
        self.assertEquals(comment.count_votes(-1), 0)

        cv1 = CommentVote(user=user1, comment=comment, reaction=-1)
        cv1.save()
        self.assertEquals(comment.count_votes(-1), 1)

        cv2 = CommentVote(user=user2, comment=comment, reaction=-1)
        cv2.save()
        self.assertEquals(comment.count_votes(-1), 2)

        cv3 = CommentVote(user=user3, comment=comment, reaction=-1)
        cv3.save()
        self.assertEquals(comment.count_votes(-1), 3)

    def test_count_votes_with_reaction_mixed(self):
        post = Post.objects.get(title="comment_test")
        user1 = User.objects.get(login="monika")
        user2 = User.objects.get(login="piwosz")
        user3 = User.objects.get(login="norbert")

        comment = Comment(parent_post=post)
        comment.save()
        self.assertEquals(comment.count_votes(1), 0)
        self.assertEquals(comment.count_votes(-1), 0)

        cv1 = CommentVote(user=user1, comment=comment, reaction=1)
        cv1.save()
        self.assertEquals(comment.count_votes(1), 1)
        self.assertEquals(comment.count_votes(-1), 0)

        cv2 = CommentVote(user=user2, comment=comment, reaction=-1)
        cv2.save()
        self.assertEquals(comment.count_votes(1), 1)
        self.assertEquals(comment.count_votes(-1), 1)

        cv3 = CommentVote(user=user3, comment=comment, reaction=1)
        cv3.save()
        self.assertEquals(comment.count_votes(1), 2)
        self.assertEquals(comment.count_votes(-1), 1)

    def test_count_votes_with_no_argument(self):
        post = Post.objects.get(title="comment_test")
        user1 = User.objects.get(login="monika")
        user2 = User.objects.get(login="piwosz")
        user3 = User.objects.get(login="norbert")

        comment = Comment(parent_post=post)
        comment.save()
        self.assertEquals(comment.count_votes(), 0)

        cv1 = CommentVote(user=user1, comment=comment, reaction=1)
        cv1.save()
        self.assertEquals(comment.count_votes(), 1)

        cv2 = CommentVote(user=user2, comment=comment, reaction=-1)
        cv2.save()
        self.assertEquals(comment.count_votes(), 2)

        cv3 = CommentVote(user=user3, comment=comment, reaction=1)
        cv3.save()
        self.assertEquals(comment.count_votes(), 3)

    def test_count_all_replies_with_no_replies(self):
        post = Post.objects.get(title="comment_test")
        self.assertEquals(post.count_all_comments(), 0)

    def test_count_all_replies_with_some_replies(self):
        post = Post.objects.get(title="comment_test")
        parent_comment = Comment(parent_post=post)
        parent_comment.save()

        child_comment1 = Comment(
            parent_post=post, parent_comment=parent_comment)
        child_comment1.save()
        child_comment2 = Comment(
            parent_post=post, parent_comment=parent_comment)
        child_comment2.save()
        child_comment3 = Comment(
            parent_post=post, parent_comment=child_comment1)
        child_comment3.save()
        another_comment = Comment(parent_post=post)
        another_comment.save()
        child_comment4 = Comment(
            parent_post=post, parent_comment=another_comment)
        child_comment4.save()

        self.assertEquals(parent_comment.count_all_replies(), 3)
        self.assertEquals(child_comment1.count_all_replies(), 1)
        self.assertEquals(child_comment2.count_all_replies(), 0)
        self.assertEquals(child_comment3.count_all_replies(), 0)
        self.assertEquals(another_comment.count_all_replies(), 1)
        self.assertEquals(child_comment4.count_all_replies(), 0)

    def test_get_depth_with_some_replies(self):
        post = Post.objects.get(title="comment_test")
        parent_comment = Comment(parent_post=post)
        parent_comment.save()

        child_comment1 = Comment(
            parent_post=post, parent_comment=parent_comment)
        child_comment1.save()
        child_comment2 = Comment(
            parent_post=post, parent_comment=parent_comment)
        child_comment2.save()
        child_comment3 = Comment(
            parent_post=post, parent_comment=child_comment1)
        child_comment3.save()
        another_comment = Comment(parent_post=post)
        another_comment.save()
        child_comment4 = Comment(
            parent_post=post, parent_comment=another_comment)
        child_comment4.save()

        self.assertEquals(parent_comment.get_depth(), 1)
        self.assertEquals(child_comment1.get_depth(), 2)
        self.assertEquals(child_comment2.get_depth(), 2)
        self.assertEquals(child_comment3.get_depth(), 3)
        self.assertEquals(another_comment.get_depth(), 1)
        self.assertEquals(child_comment4.get_depth(), 2)

    def test_is_max_depth(self):
        post = Post.objects.get(title="comment_test")
        parent_comment = Comment(parent_post=post)
        parent_comment.save()
        self.assertEquals(parent_comment.is_max_depth(), False)

        for comm_depth in range(0, comment_max_depth-2):
            parent_comment = Comment(
                parent_post=post, parent_comment=parent_comment)
            parent_comment.save()
            self.assertEquals(parent_comment.is_max_depth(), False)

        parent_comment = Comment(
            parent_post=post, parent_comment=parent_comment)
        parent_comment.save()
        self.assertEquals(parent_comment.is_max_depth(), True)


class CommentVoteModelTests(TestCase):
    @classmethod
    def setUp(cls):
        generate()

    def test_get_reaction_with_reaction_1(self):
        post = Post.objects.get(title="comment_test")
        comment = Comment(parent_post=post)
        comment.save()
        user = User.objects.get(login="monika")

        cv = CommentVote(user=user, comment=comment, reaction=1)
        self.assertEquals(cv.get_reaction(), 1)

    def test_get_reaction_with_reaction_minus1(self):
        post = Post.objects.get(title="comment_test")
        comment = Comment(parent_post=post)
        comment.save()
        user = User.objects.get(login="monika")

        cv = CommentVote(user=user, comment=comment, reaction=-1)
        self.assertEquals(cv.get_reaction(), -1)


class CommentSortingTests(TestCase):
    @classmethod
    def setUp(cls):
        generate()

    def test_sort_comments_with_no_comments(self):
        comments = []
        self.assertEquals(sort_comments(comments, 'najnowsze'), [])

    def test_sort_comments_with_sort_type_najnowsze(self):
        post = Post.objects.get(title="comment_test")
        user = User.objects.get(login='monika')

        comment1 = Comment(parent_post=post, author=user)
        comment1.save()
        comment2 = Comment(parent_post=post, author=user)
        comment2.save()
        comment3 = Comment(parent_post=post, author=user)
        comment3.save()
        comment4 = Comment(parent_post=post, author=user)
        comment4.save()

        comments = [comment2, comment4, comment1, comment3]
        sorted_comments = [comment4, comment3, comment2, comment1]
        self.assertEquals(sort_comments(
            comments, 'najnowsze'), sorted_comments)

    def test_sort_comments_with_sort_type_najstarsze(self):
        post = Post.objects.get(title="comment_test")
        user = User.objects.get(login='monika')

        comment1 = Comment(parent_post=post, author=user)
        comment1.save()
        comment2 = Comment(parent_post=post, author=user)
        comment2.save()
        comment3 = Comment(parent_post=post, author=user)
        comment3.save()
        comment4 = Comment(parent_post=post, author=user)
        comment4.save()

        comments = [comment2, comment4, comment1, comment3]
        sorted_comments = [comment1, comment2, comment3, comment4]
        self.assertEquals(sort_comments(
            comments, 'najstarsze'), sorted_comments)

    def test_sort_comments_with_sort_type_najpopularniejsze(self):
        post = Post.objects.get(title="comment_test")
        user = User.objects.get(login='monika')
        user2 = User.objects.get(login='piwosz')
        user3 = User.objects.get(login='piwosz')

        comment1 = Comment(parent_post=post, author=user)
        comment1.save()
        comment2 = Comment(parent_post=post, author=user)
        comment2.save()
        comment3 = Comment(parent_post=post, author=user)
        comment3.save()

        cv1 = CommentVote(user=user, comment=comment1, reaction=1)
        cv2 = CommentVote(user=user2, comment=comment1, reaction=-1)
        cv3 = CommentVote(user=user3, comment=comment1, reaction=-1)
        cv4 = CommentVote(user=user, comment=comment2, reaction=1)
        cv5 = CommentVote(user=user2, comment=comment2, reaction=-1)
        cv6 = CommentVote(user=user, comment=comment3, reaction=1)
        cv1.save()
        cv2.save()
        cv3.save()
        cv4.save()
        cv5.save()
        cv6.save()

        comments = [comment2, comment1, comment3]
        sorted_comments = [comment1, comment2, comment3]
        self.assertEquals(sort_comments(
            comments, 'najbardziej popularne'), sorted_comments)

    def test_sort_comments_with_sort_type_najlepiej_oceniane(self):
        post = Post.objects.get(title="comment_test")
        user = User.objects.get(login='monika')
        user2 = User.objects.get(login='piwosz')
        user3 = User.objects.get(login='piwosz')

        comment1 = Comment(parent_post=post, author=user)
        comment1.save()
        comment2 = Comment(parent_post=post, author=user)
        comment2.save()
        comment3 = Comment(parent_post=post, author=user)
        comment3.save()

        cv1 = CommentVote(user=user, comment=comment1, reaction=1)
        cv2 = CommentVote(user=user2, comment=comment1, reaction=-1)
        cv3 = CommentVote(user=user3, comment=comment1, reaction=-1)
        cv4 = CommentVote(user=user, comment=comment2, reaction=1)
        cv5 = CommentVote(user=user2, comment=comment2, reaction=-1)
        cv6 = CommentVote(user=user, comment=comment3, reaction=1)
        cv1.save()
        cv2.save()
        cv3.save()
        cv4.save()
        cv5.save()
        cv6.save()

        comments = [comment2, comment1, comment3]
        sorted_comments = [comment3, comment2, comment1]
        self.assertEquals(sort_comments(
            comments, 'najlepiej oceniane'), sorted_comments)

    def test_sort_comments_with_sort_type_najgorzej_oceniane(self):
        post = Post.objects.get(title="comment_test")
        user = User.objects.get(login='monika')
        user2 = User.objects.get(login='piwosz')
        user3 = User.objects.get(login='piwosz')

        comment1 = Comment(parent_post=post, author=user)
        comment1.save()
        comment2 = Comment(parent_post=post, author=user)
        comment2.save()
        comment3 = Comment(parent_post=post, author=user)
        comment3.save()

        cv1 = CommentVote(user=user, comment=comment1, reaction=1)
        cv2 = CommentVote(user=user2, comment=comment1, reaction=-1)
        cv3 = CommentVote(user=user3, comment=comment1, reaction=-1)
        cv4 = CommentVote(user=user, comment=comment2, reaction=1)
        cv5 = CommentVote(user=user2, comment=comment2, reaction=-1)
        cv6 = CommentVote(user=user, comment=comment3, reaction=1)
        cv1.save()
        cv2.save()
        cv3.save()
        cv4.save()
        cv5.save()
        cv6.save()

        comments = [comment2, comment1, comment3]
        sorted_comments = [comment1, comment2, comment3]
        self.assertEquals(sort_comments(
            comments, 'najgorzej oceniane'), sorted_comments)

    def test_sort_comments_with_undefined_sort_type(self):
        # domyślnie sortowanie od najnowszych
        post = Post.objects.get(title="comment_test")
        user = User.objects.get(login='monika')
        user2 = User.objects.get(login='piwosz')
        user3 = User.objects.get(login='piwosz')

        comment1 = Comment(parent_post=post, author=user)
        comment1.save()
        comment3 = Comment(parent_post=post, author=user)
        comment3.save()
        comment2 = Comment(parent_post=post, author=user)
        comment2.save()

        cv1 = CommentVote(user=user, comment=comment1, reaction=1)
        cv2 = CommentVote(user=user2, comment=comment1, reaction=-1)
        cv3 = CommentVote(user=user3, comment=comment1, reaction=-1)
        cv4 = CommentVote(user=user, comment=comment2, reaction=1)
        cv5 = CommentVote(user=user2, comment=comment2, reaction=-1)
        cv6 = CommentVote(user=user, comment=comment3, reaction=1)
        cv1.save()
        cv2.save()
        cv3.save()
        cv4.save()
        cv5.save()
        cv6.save()

        comments = [comment2, comment1, comment3]
        sorted_comments = [comment2, comment3, comment1]
        self.assertEquals(sort_comments(
            comments, 'najNIEWIEMJAK oceniane'), sorted_comments)
