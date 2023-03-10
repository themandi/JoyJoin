import re
from django.test import Client, TestCase
from django.http import Http404

from common.generate_test_data import generate
from common.models import User, Vote, Post, Comment, CommentVote, Section, Tag, PostVisit, TagPunctation
from common.queries import get_comments_list, get_simple_comments_list, get_posts, get_posts_for_section, get_posts_with_tag, get_posts_for_user
from common.updates import update_tag_punctations
from login.tests import login_client_for_tests


voteless_post_title = 'Różnice między standardami C++'
commentless_post_title = 'comment_test'
one_comment_post_title = 'Różnice między standardami C++'

post_titles = ['Moje prace',
               'Poszukiwani chętni do pozowania',
               'Meczyk',
               'Jakie farby olejne są najlepsze',
               'Różnice między standardami C++',
               'Move-constructor w C++11',
               'comment_test',
               'Spotkanie dotyczące Pythona',
               'Grupa na Euro 2020',
               'Długi post o malowaniu']

post_titles_for_monika = ['Moje prace',
                          'Poszukiwani chętni do pozowania',
                          'Jakie farby olejne są najlepsze',
                          'Różnice między standardami C++',
                          'Move-constructor w C++11',
                          'comment_test',
                          'Spotkanie dotyczące Pythona',
                          'Długi post o malowaniu',
                          'Meczyk',
                          'Grupa na Euro 2020']


class GetCommentsListTests(TestCase):
    @classmethod
    def setUp(cls):
        generate()

    def test_get_comments_list_with_leaf_comment(self):
        sort_type = 'najnowsze'
        user = User.objects.first()
        comment = Comment.objects.get(
            parent_post__title=one_comment_post_title)
        result = [(comment, 0, 0, False, False), (')', '', '', '', '')]
        self.assertEquals(get_comments_list(comment, sort_type, user), result)

    def test_get_comments_list_with_no_sort_type(self):
        sort_type = 'najjjj'
        user = User.objects.first()
        comment = Comment.objects.get(
            parent_post__title=one_comment_post_title)
        result = [(comment, 0, 0, False, False), (')', '', '', '', '')]
        self.assertEquals(get_comments_list(comment, sort_type, user), result)

    def test_get_comments_list_with_advanced_structure(self):
        sort_type = 'najstarsze'
        user = User.objects.get(id=1)
        another_user = User.objects.get(id=2)
        post = Post.objects.get(title=one_comment_post_title)

        comment1 = Comment.objects.get(parent_post=post)
        comment2 = Comment(
            parent_post=post, parent_comment=comment1, author=user)
        comment2.save()
        comment3 = Comment(
            parent_post=post, parent_comment=comment1, author=user)
        comment3.save()

        comment_vote1 = CommentVote(user=user, comment=comment1, reaction=1)
        comment_vote2 = CommentVote(user=user, comment=comment3, reaction=-1)
        comment_vote3 = CommentVote(
            user=another_user, comment=comment1, reaction=1)
        comment_vote4 = CommentVote(
            user=another_user, comment=comment2, reaction=1)
        comment_vote5 = CommentVote(
            user=another_user, comment=comment3, reaction=1)
        comment_vote1.save()
        comment_vote2.save()
        comment_vote3.save()
        comment_vote4.save()
        comment_vote5.save()

        result = [
            (comment1, 2, 0, True, False),
            (comment2, 1, 0, False, False),
            (')', '', '', '', ''),
            (comment3, 1, 1, False, True),
            (')', '', '', '', ''),
            (')', '', '', '', '')
        ]
        self.assertEquals(get_comments_list(comment1, sort_type, user), result)

    def test_get_comments_list_with_advanced_structure_and_no_user(self):
        sort_type = 'najstarsze'
        user = User.objects.get(id=1)
        another_user = User.objects.get(id=2)
        post = Post.objects.get(title=one_comment_post_title)

        comment1 = Comment.objects.get(parent_post=post)
        comment2 = Comment(
            parent_post=post, parent_comment=comment1, author=user)
        comment2.save()
        comment3 = Comment(
            parent_post=post, parent_comment=comment1, author=user)
        comment3.save()

        comment_vote1 = CommentVote(user=user, comment=comment1, reaction=1)
        comment_vote2 = CommentVote(user=user, comment=comment3, reaction=-1)
        comment_vote3 = CommentVote(
            user=another_user, comment=comment1, reaction=1)
        comment_vote4 = CommentVote(
            user=another_user, comment=comment2, reaction=1)
        comment_vote5 = CommentVote(
            user=another_user, comment=comment3, reaction=1)
        comment_vote1.save()
        comment_vote2.save()
        comment_vote3.save()
        comment_vote4.save()
        comment_vote5.save()

        result = [
            (comment1, 2, 0, False, False),
            (comment2, 1, 0, False, False),
            (')', '', '', '', ''),
            (comment3, 1, 1, False, False),
            (')', '', '', '', ''),
            (')', '', '', '', '')
        ]
        self.assertEquals(get_comments_list(comment1, sort_type, None), result)


class ReplyTests(TestCase):
    @classmethod
    def setUp(cls):
        generate()

    def test_reply_if_not_logged_in(self):
        post = Post.objects.filter(title=one_comment_post_title).first()
        post_id = post.id
        client = Client()
        response = client.post(
            '/post/reply/', {'post_id': post_id, 'comment': 'Tekst', 'comm_id': 'None'})
        self.assertEqual(response.status_code, 200)

    def test_reply_if_post_not_exist(self):
        post_id = 0
        client = Client()
        login_client_for_tests(client)
        response = client.post(
            '/post/reply/', {'post_id': post_id, 'comment': 'Tekst', 'comm_id': 'None'})
        self.assertEqual(response.status_code, 404)

    def test_reply_if_no_text(self):
        post = Post.objects.filter(title=one_comment_post_title).first()
        post_id = post.id
        client = Client()
        login_client_for_tests(client)
        response = client.post(
            '/post/reply/', {'post_id': post_id, 'comment': '', 'comm_id': 'None'})
        self.assertEqual(response.status_code, 404)

    def test_reply_if_no_comm_id(self):
        post = Post.objects.filter(title=one_comment_post_title).first()
        post_id = post.id
        client = Client()
        login_client_for_tests(client)
        response = client.post(
            '/post/reply/', {'post_id': post_id, 'comment': 'Tekst', 'comm_id': ''})
        self.assertEqual(response.status_code, 404)

    def test_reply_to_post(self):
        post = Post.objects.filter(title=commentless_post_title).first()
        post_id = post.id
        client = Client()
        login_client_for_tests(client)
        with self.assertRaises(Comment.DoesNotExist):
            comment = Comment.objects.get(
                author__login=client.session.get('logged_in_as'), parent_post=post)
        response = client.post(
            '/post/reply/', {'post_id': post_id, 'comment': 'Tekst', 'comm_id': 'None'})
        self.assertEqual(response.status_code, 302)
        comment = Comment.objects.get(
            author__login=client.session.get('logged_in_as'), parent_post=post)
        self.assertEquals(comment.text, 'Tekst')

    def test_reply_to_comment(self):
        post = Post.objects.get(title=one_comment_post_title)
        post_id = post.id
        parent_comment = Comment.objects.first()
        parent_comment_id = parent_comment.id
        client = Client()
        login_client_for_tests(client)
        with self.assertRaises(Comment.DoesNotExist):
            comment = Comment.objects.get(author__login=client.session.get(
                'logged_in_as'), parent_post=post, parent_comment=parent_comment)
        response = client.post(
            '/post/reply/', {'post_id': post_id, 'comment': 'Tekst', 'comm_id': parent_comment_id})
        self.assertEqual(response.status_code, 302)
        comment = Comment.objects.get(author__login=client.session.get(
            'logged_in_as'), parent_post=post, parent_comment=parent_comment)
        self.assertEquals(comment.text, 'Tekst')


class ChangeSortingTests(TestCase):
    @classmethod
    def setUp(cls):
        generate()

    def test_change_sorting_with_no_post_id(self):
        client = Client()
        response = client.post('/post/change_sorting/',
                               {'sort_type': 'najnowsze'})
        self.assertEqual(response.status_code, 404)

    def test_change_sorting_with_bad_post_id(self):
        post_id = 0
        client = Client()
        response = client.post('/post/change_sorting/',
                               {'post_id': post_id, 'sort_type': 'najnowsze'})
        self.assertEqual(response.status_code, 302)

    def test_change_sorting_with_good_post_id(self):
        post_id = 1
        client = Client()
        response = client.post('/post/change_sorting/',
                               {'post_id': post_id, 'sort_type': 'najnowsze'})
        self.assertEqual(response.status_code, 302)

    def test_change_sorting_with_no_sort_type(self):
        post_id = 1
        client = Client()
        response = client.post('/post/change_sorting/', {'post_id': post_id})
        self.assertEqual(response.status_code, 302)

    def test_change_sorting_with_bad_sort_type(self):
        post_id = 1
        client = Client()
        response = client.post('/post/change_sorting/',
                               {'post_id': post_id, 'sort_type': 'najjjj'})
        self.assertEqual(response.status_code, 302)


class CommentVoteTests(TestCase):
    @classmethod
    def setUp(cls):
        generate()

    # testy oceniania komentarzy z widoku pojedynczego posta

    def test_comment_vote_up_if_comment_not_exist(self):
        comm_id = 0
        client = Client()
        response = client.post('/post/vote_comment/1//all//',
                               {'sec_view': 'false', 'comm_id': comm_id})
        self.assertEqual(response.status_code, 404)

    def test_comment_vote_down_if_comment_not_exist(self):
        comm_id = 0
        client = Client()
        response = client.post('/post/vote_comment/2//all//',
                               {'sec_view': 'false', 'comm_id': comm_id})
        self.assertEqual(response.status_code, 404)

    def test_comment_vote_up_if_not_logged_in(self):
        comment = Comment.objects.filter(
            parent_post__title=one_comment_post_title).first()
        comment_id = comment.id
        client = Client()
        response = client.post('/post/vote_comment/1/',
                               {'sec_view': 'false', 'comm_id': comment_id})
        self.assertEqual(response.status_code, 200)

    def test_comment_vote_down_if_not_logged_in(self):
        comment = Comment.objects.filter(
            parent_post__title=one_comment_post_title).first()
        comment_id = comment.id
        client = Client()
        response = client.post('/post/vote_comment/2/',
                               {'sec_view': 'false', 'comm_id': comment_id})
        self.assertEqual(response.status_code, 200)

    def test_comment_vote_if_reaction_undefined_and_not_logged_in(self):
        comment = Comment.objects.filter(
            parent_post__title=one_comment_post_title).first()
        comment_id = comment.id
        client = Client()
        response = client.post('/post/vote_comment/4/',
                               {'sec_view': 'false', 'comm_id': comment_id})
        self.assertEqual(response.status_code, 200)

    def test_comment_vote_if_reaction_undefined_and_logged_in(self):
        comment = Comment.objects.filter(
            parent_post__title=one_comment_post_title).first()
        comment_id = comment.id
        client = Client()
        login_client_for_tests(client)
        response = client.post('/post/vote_comment/4/',
                               {'sec_view': 'false', 'comm_id': comment_id})
        self.assertEqual(response.status_code, 200)

    def test_comment_vote_up_if_logged_in(self):
        comment = Comment.objects.filter(
            parent_post__title=one_comment_post_title).first()
        comment_id = comment.id
        client = Client()
        login_client_for_tests(client)
        with self.assertRaises(CommentVote.DoesNotExist):
            comm_vote = CommentVote.objects.get(
                user__login=client.session.get('logged_in_as'), comment=comment)
        response = client.post('/post/vote_comment/1/',
                               {'sec_view': 'false', 'comm_id': comment_id})
        self.assertEqual(response.status_code, 200)
        comm_vote = CommentVote.objects.get(
            user__login=client.session.get('logged_in_as'), comment=comment)
        self.assertEqual(comm_vote.reaction, 1)
        response = client.post('/post/vote_comment/1/',
                               {'sec_view': 'false', 'comm_id': comment_id})
        self.assertEqual(response.status_code, 200)
        with self.assertRaises(CommentVote.DoesNotExist):
            comm_vote = CommentVote.objects.get(
                user__login=client.session.get('logged_in_as'), comment=comment)

    def test_comment_vote_down_if_logged_in(self):
        comment = Comment.objects.filter(
            parent_post__title=one_comment_post_title).first()
        comment_id = comment.id
        client = Client()
        login_client_for_tests(client)
        with self.assertRaises(CommentVote.DoesNotExist):
            comm_vote = CommentVote.objects.get(
                user__login=client.session.get('logged_in_as'), comment=comment)
        response = client.post('/post/vote_comment/2/',
                               {'sec_view': 'false', 'comm_id': comment_id})
        self.assertEqual(response.status_code, 200)
        comm_vote = CommentVote.objects.get(
            user__login=client.session.get('logged_in_as'), comment=comment)
        self.assertEqual(comm_vote.reaction, -1)
        response = client.post('/post/vote_comment/2/',
                               {'sec_view': 'false', 'comm_id': comment_id})
        self.assertEqual(response.status_code, 200)
        with self.assertRaises(CommentVote.DoesNotExist):
            comm_vote = CommentVote.objects.get(
                user__login=client.session.get('logged_in_as'), comment=comment)

    def test_comment_vote_down_to_up_if_logged_in(self):
        comment = Comment.objects.filter(
            parent_post__title=one_comment_post_title).first()
        comment_id = comment.id
        client = Client()
        login_client_for_tests(client)
        with self.assertRaises(CommentVote.DoesNotExist):
            comm_vote = CommentVote.objects.get(
                user__login=client.session.get('logged_in_as'), comment=comment)
        response = client.post('/post/vote_comment/2/',
                               {'sec_view': 'false', 'comm_id': comment_id})
        self.assertEqual(response.status_code, 200)
        comm_vote = CommentVote.objects.get(
            user__login=client.session.get('logged_in_as'), comment=comment)
        self.assertEqual(comm_vote.reaction, -1)
        response = client.post('/post/vote_comment/1/',
                               {'sec_view': 'false', 'comm_id': comment_id})
        self.assertEqual(response.status_code, 200)
        comm_vote = CommentVote.objects.get(
            user__login=client.session.get('logged_in_as'), comment=comment)
        self.assertEqual(comm_vote.reaction, 1)

    def test_comment_vote_up_to_down_if_logged_in(self):
        comment = Comment.objects.filter(
            parent_post__title=one_comment_post_title).first()
        comment_id = comment.id
        client = Client()
        login_client_for_tests(client)
        with self.assertRaises(CommentVote.DoesNotExist):
            comm_vote = CommentVote.objects.get(
                user__login=client.session.get('logged_in_as'), comment=comment)
        response = client.post('/post/vote_comment/1/',
                               {'sec_view': 'false', 'comm_id': comment_id})
        self.assertEqual(response.status_code, 200)
        comm_vote = CommentVote.objects.get(
            user__login=client.session.get('logged_in_as'), comment=comment)
        self.assertEqual(comm_vote.reaction, 1)
        response = client.post('/post/vote_comment/2/',
                               {'sec_view': 'false', 'comm_id': comment_id})
        self.assertEqual(response.status_code, 200)
        comm_vote = CommentVote.objects.get(
            user__login=client.session.get('logged_in_as'), comment=comment)
        self.assertEqual(comm_vote.reaction, -1)

    # testy oceniania komentarzy z widoku sekcji

    def test_comment_view_more_vote_up_if_comment_not_exist(self):
        comm_id = 0
        client = Client()
        response = client.post('/post/vote_comment/1//all//',
                               {'sec_view': 'true', 'comm_id': comm_id})
        self.assertEqual(response.status_code, 404)

    def test_comment_view_more_vote_down_if_comment_not_exist(self):
        comm_id = 0
        client = Client()
        response = client.post('/post/vote_comment/2//all//',
                               {'sec_view': 'true', 'comm_id': comm_id})
        self.assertEqual(response.status_code, 404)

    def test_comment_view_more_vote_up_if_not_logged_in(self):
        comment = Comment.objects.filter(
            parent_post__title=one_comment_post_title).first()
        comment_id = comment.id
        client = Client()
        response = client.post('/post/vote_comment/1/',
                               {'sec_view': 'true', 'comm_id': comment_id})
        self.assertEqual(response.status_code, 200)

    def test_comment_view_more_vote_down_if_not_logged_in(self):
        comment = Comment.objects.filter(
            parent_post__title=one_comment_post_title).first()
        comment_id = comment.id
        client = Client()
        response = client.post('/post/vote_comment/2/',
                               {'sec_view': 'true', 'comm_id': comment_id})
        self.assertEqual(response.status_code, 200)

    def test_comment_view_more_vote_if_reaction_undefined_and_not_logged_in(self):
        comment = Comment.objects.filter(
            parent_post__title=one_comment_post_title).first()
        comment_id = comment.id
        client = Client()
        response = client.post('/post/vote_comment/4/',
                               {'sec_view': 'true', 'comm_id': comment_id})
        self.assertEqual(response.status_code, 200)

    def test_comment_view_more_vote_if_reaction_undefined_and_logged_in(self):
        comment = Comment.objects.filter(
            parent_post__title=one_comment_post_title).first()
        comment_id = comment.id
        client = Client()
        login_client_for_tests(client)
        response = client.post('/post/vote_comment/4/',
                               {'sec_view': 'true', 'comm_id': comment_id})
        self.assertEqual(response.status_code, 200)

    def test_comment_view_more_vote_up_if_logged_in(self):
        comment = Comment.objects.filter(
            parent_post__title=one_comment_post_title).first()
        comment_id = comment.id
        client = Client()
        login_client_for_tests(client)
        with self.assertRaises(CommentVote.DoesNotExist):
            comm_vote = CommentVote.objects.get(
                user__login=client.session.get('logged_in_as'), comment=comment)
        response = client.post('/post/vote_comment/1/',
                               {'sec_view': 'true', 'comm_id': comment_id})
        self.assertEqual(response.status_code, 200)
        comm_vote = CommentVote.objects.get(
            user__login=client.session.get('logged_in_as'), comment=comment)
        self.assertEqual(comm_vote.reaction, 1)
        response = client.post('/post/vote_comment/1/',
                               {'sec_view': 'true', 'comm_id': comment_id})
        self.assertEqual(response.status_code, 200)
        with self.assertRaises(CommentVote.DoesNotExist):
            comm_vote = CommentVote.objects.get(
                user__login=client.session.get('logged_in_as'), comment=comment)

    def test_comment_view_more_vote_down_if_logged_in(self):
        comment = Comment.objects.filter(
            parent_post__title=one_comment_post_title).first()
        comment_id = comment.id
        client = Client()
        login_client_for_tests(client)
        with self.assertRaises(CommentVote.DoesNotExist):
            comm_vote = CommentVote.objects.get(
                user__login=client.session.get('logged_in_as'), comment=comment)
        response = client.post('/post/vote_comment/2/',
                               {'sec_view': 'true', 'comm_id': comment_id})
        self.assertEqual(response.status_code, 200)
        comm_vote = CommentVote.objects.get(
            user__login=client.session.get('logged_in_as'), comment=comment)
        self.assertEqual(comm_vote.reaction, -1)
        response = client.post('/post/vote_comment/2/',
                               {'sec_view': 'true', 'comm_id': comment_id})
        self.assertEqual(response.status_code, 200)
        with self.assertRaises(CommentVote.DoesNotExist):
            comm_vote = CommentVote.objects.get(
                user__login=client.session.get('logged_in_as'), comment=comment)

    def test_comment_view_more_vote_down_to_up_if_logged_in(self):
        comment = Comment.objects.filter(
            parent_post__title=one_comment_post_title).first()
        comment_id = comment.id
        client = Client()
        login_client_for_tests(client)
        with self.assertRaises(CommentVote.DoesNotExist):
            comm_vote = CommentVote.objects.get(
                user__login=client.session.get('logged_in_as'), comment=comment)
        response = client.post('/post/vote_comment/2/',
                               {'sec_view': 'true', 'comm_id': comment_id})
        self.assertEqual(response.status_code, 200)
        comm_vote = CommentVote.objects.get(
            user__login=client.session.get('logged_in_as'), comment=comment)
        self.assertEqual(comm_vote.reaction, -1)
        response = client.post('/post/vote_comment/1/',
                               {'sec_view': 'true', 'comm_id': comment_id})
        self.assertEqual(response.status_code, 200)
        comm_vote = CommentVote.objects.get(
            user__login=client.session.get('logged_in_as'), comment=comment)
        self.assertEqual(comm_vote.reaction, 1)

    def test_comment_view_more_vote_up_to_down_if_logged_in(self):
        comment = Comment.objects.filter(
            parent_post__title=one_comment_post_title).first()
        comment_id = comment.id
        client = Client()
        login_client_for_tests(client)
        with self.assertRaises(CommentVote.DoesNotExist):
            comm_vote = CommentVote.objects.get(
                user__login=client.session.get('logged_in_as'), comment=comment)
        response = client.post('/post/vote_comment/1/',
                               {'sec_view': 'true', 'comm_id': comment_id})
        self.assertEqual(response.status_code, 200)
        comm_vote = CommentVote.objects.get(
            user__login=client.session.get('logged_in_as'), comment=comment)
        self.assertEqual(comm_vote.reaction, 1)
        response = client.post('/post/vote_comment/2/',
                               {'sec_view': 'true', 'comm_id': comment_id})
        self.assertEqual(response.status_code, 200)
        comm_vote = CommentVote.objects.get(
            user__login=client.session.get('logged_in_as'), comment=comment)
        self.assertEqual(comm_vote.reaction, -1)


class VoteTests(TestCase):
    @classmethod
    def setUp(cls):
        generate()

    def test_post_vote_up_if_post_not_exist(self):
        post_id = 0
        client = Client()
        response = client.post('/post/vote/1//all//', {'post_id': post_id})
        self.assertEqual(response.status_code, 404)

    def test_post_vote_down_if_post_not_exist(self):
        post_id = 0
        client = Client()
        response = client.post('/post/vote/2//all//', {'post_id': post_id})
        self.assertEqual(response.status_code, 404)

    def test_post_view_more_vote_down_if_not_logged_in(self):
        post = Post.objects.first()
        post_id = post.id
        client = Client()
        response = client.post('/post/vote/2/', {'post_id': post_id})
        self.assertEqual(response.status_code, 200)

    def test_post_view_more_vote_up_if_not_logged_in(self):
        post = Post.objects.first()
        post_id = post.id
        client = Client()
        response = client.post('/post/vote/1/', {'post_id': post_id})
        self.assertEqual(response.status_code, 200)

    def test_post_view_more_vote_up_if_logged_in(self):
        post = Post.objects.get(title=voteless_post_title)
        post_id = post.id
        client = Client()
        login_client_for_tests(client)
        with self.assertRaises(Vote.DoesNotExist):
            vote = Vote.objects.get(
                user__login=client.session.get('logged_in_as'), post=post)
        response = client.post('/post/vote/1/', {'post_id': post_id})
        self.assertEqual(response.status_code, 200)
        vote = Vote.objects.get(
            user__login=client.session.get('logged_in_as'), post=post)
        self.assertEqual(vote.reaction, 1)
        response = client.post('/post/vote/1/', {'post_id': post_id})
        self.assertEqual(response.status_code, 200)
        with self.assertRaises(Vote.DoesNotExist):
            vote = Vote.objects.get(
                user__login=client.session.get('logged_in_as'), post=post)

    def test_post_view_more_vote_down_if_logged_in(self):
        post = Post.objects.get(title=voteless_post_title)
        post_id = post.id
        client = Client()
        login_client_for_tests(client)
        with self.assertRaises(Vote.DoesNotExist):
            vote = Vote.objects.get(
                user__login=client.session.get('logged_in_as'), post=post)
        response = client.post('/post/vote/2/', {'post_id': post_id})
        self.assertEqual(response.status_code, 200)
        vote = Vote.objects.get(
            user__login=client.session.get('logged_in_as'), post=post)
        self.assertEqual(vote.reaction, -1)
        response = client.post('/post/vote/2/', {'post_id': post_id})
        self.assertEqual(response.status_code, 200)
        with self.assertRaises(Vote.DoesNotExist):
            vote = Vote.objects.get(
                user__login=client.session.get('logged_in_as'), post=post)

    def test_post_view_more_vote_down_to_up_if_logged_in(self):
        post = Post.objects.get(title=voteless_post_title)
        post_id = post.id
        client = Client()
        login_client_for_tests(client)
        with self.assertRaises(Vote.DoesNotExist):
            vote = Vote.objects.get(
                user__login=client.session.get('logged_in_as'), post=post)
        response = client.post('/post/vote/2/', {'post_id': post_id})
        self.assertEqual(response.status_code, 200)
        vote = Vote.objects.get(
            user__login=client.session.get('logged_in_as'), post=post)
        self.assertEqual(vote.reaction, -1)
        response = client.post('/post/vote/1/', {'post_id': post_id})
        self.assertEqual(response.status_code, 200)
        vote = Vote.objects.get(
            user__login=client.session.get('logged_in_as'), post=post)
        self.assertEqual(vote.reaction, 1)

    def test_post_view_more_vote_up_to_down_if_logged_in(self):
        post = Post.objects.get(title=voteless_post_title)
        post_id = post.id
        client = Client()
        login_client_for_tests(client)
        with self.assertRaises(Vote.DoesNotExist):
            vote = Vote.objects.get(
                user__login=client.session.get('logged_in_as'), post=post)
        response = client.post('/post/vote/1/', {'post_id': post_id})
        self.assertEqual(response.status_code, 200)
        vote = Vote.objects.get(
            user__login=client.session.get('logged_in_as'), post=post)
        self.assertEqual(vote.reaction, 1)
        response = client.post('/post/vote/2/', {'post_id': post_id})
        self.assertEqual(response.status_code, 200)
        vote = Vote.objects.get(
            user__login=client.session.get('logged_in_as'), post=post)
        self.assertEqual(vote.reaction, -1)

    def test_post_vote_up_if_not_logged_in(self):
        post = Post.objects.first()
        post_id = post.id
        client = Client()
        response = client.post('/post/vote/1/', {'post_id': post_id})
        self.assertEqual(response.status_code, 200)

    def test_post_vote_down_if_not_logged_in(self):
        post = Post.objects.first()
        post_id = post.id
        client = Client()
        response = client.post('/post/vote/2/', {'post_id': post_id})
        self.assertEqual(response.status_code, 200)

    def test_post_vote_up_if_logged_in(self):
        post = Post.objects.get(title=voteless_post_title)
        post_id = post.id
        client = Client()
        login_client_for_tests(client)
        with self.assertRaises(Vote.DoesNotExist):
            vote = Vote.objects.get(
                user__login=client.session.get('logged_in_as'), post=post)
        response = client.post('/post/vote/1/', {'post_id': post_id})
        self.assertEqual(response.status_code, 200)
        vote = Vote.objects.get(
            user__login=client.session.get('logged_in_as'), post=post)
        self.assertEqual(vote.reaction, 1)
        response = client.post('/post/vote/1/', {'post_id': post_id})
        self.assertEqual(response.status_code, 200)
        with self.assertRaises(Vote.DoesNotExist):
            vote = Vote.objects.get(
                user__login=client.session.get('logged_in_as'), post=post)

    def test_post_vote_down_if_logged_in(self):
        post = Post.objects.get(title=voteless_post_title)
        post_id = post.id
        client = Client()
        login_client_for_tests(client)
        with self.assertRaises(Vote.DoesNotExist):
            vote = Vote.objects.get(
                user__login=client.session.get('logged_in_as'), post=post)
        response = client.post('/post/vote/2/', {'post_id': post_id})
        self.assertEqual(response.status_code, 200)
        vote = Vote.objects.get(
            user__login=client.session.get('logged_in_as'), post=post)
        self.assertEqual(vote.reaction, -1)
        response = client.post('/post/vote/2/', {'post_id': post_id})
        self.assertEqual(response.status_code, 200)
        with self.assertRaises(Vote.DoesNotExist):
            vote = Vote.objects.get(
                user__login=client.session.get('logged_in_as'), post=post)

    def test_post_vote_up_to_down_if_logged_in(self):
        post = Post.objects.get(title=voteless_post_title)
        post_id = post.id
        client = Client()
        login_client_for_tests(client)
        with self.assertRaises(Vote.DoesNotExist):
            vote = Vote.objects.get(
                user__login=client.session.get('logged_in_as'), post=post)
        response = client.post('/post/vote/1/', {'post_id': post_id})
        self.assertEqual(response.status_code, 200)
        vote = Vote.objects.get(
            user__login=client.session.get('logged_in_as'), post=post)
        self.assertEqual(vote.reaction, 1)
        response = client.post('/post/vote/2/', {'post_id': post_id})
        self.assertEqual(response.status_code, 200)
        vote = Vote.objects.get(
            user__login=client.session.get('logged_in_as'), post=post)
        self.assertEqual(vote.reaction, -1)

    def test_post_vote_down_to_up_if_logged_in(self):
        post = Post.objects.get(title=voteless_post_title)
        post_id = post.id
        client = Client()
        login_client_for_tests(client)
        with self.assertRaises(Vote.DoesNotExist):
            vote = Vote.objects.get(
                user__login=client.session.get('logged_in_as'), post=post)
        response = client.post('/post/vote/2/', {'post_id': post_id})
        self.assertEqual(response.status_code, 200)
        vote = Vote.objects.get(
            user__login=client.session.get('logged_in_as'), post=post)
        self.assertEqual(vote.reaction, -1)
        response = client.post('/post/vote/1/', {'post_id': post_id})
        self.assertEqual(response.status_code, 200)
        vote = Vote.objects.get(
            user__login=client.session.get('logged_in_as'), post=post)
        self.assertEqual(vote.reaction, 1)


post_view_tests_post_title = 'Poszukiwani chętni do pozowania'
post_view_tests_user_downvoted_post_title = 'Move-constructor w C++11'


class PostViewTests(TestCase):
    @classmethod
    def setUp(cls):
        generate()

    def test_post_view_reachable(self):
        post = Post.objects.get(title=post_view_tests_post_title)
        post_id = post.id
        client = Client()
        response = client.get('/post/' + str(post_id) + '/')
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, post.title)
        self.assertContains(response, post.text)
        self.assertNotContains(response, 'Zobacz więcej')
        regex = re.compile(b'<i class="icon-heart"></i> <b>' +
                           bytes(str(post.count_votes(1)), 'utf-8') + b'</b>')
        self.assertTrue(bool(regex.search(response.content)))
        regex = re.compile(b'<i class="icon-heart-broken"></i> ' +
                           bytes(str(post.count_votes(-1)), 'utf-8'))
        self.assertTrue(bool(regex.search(response.content)))

    def test_post_view_reachable_when_logged_in(self):
        post = Post.objects.get(title=post_view_tests_post_title)
        post_id = post.id
        client = Client()
        login_client_for_tests(client)
        response = client.get('/post/' + str(post_id) + '/')
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, post.title)
        self.assertContains(response, post.text)
        self.assertNotContains(response, 'Zobacz więcej')
        regex = re.compile(b'<i class="icon-heart liked"></i> <b>' +
                           bytes(str(post.count_votes(1)), 'utf-8') + b'</b>')
        self.assertTrue(bool(regex.search(response.content)))
        regex = re.compile(b'<i class="icon-heart-broken"></i> ' +
                           bytes(str(post.count_votes(-1)), 'utf-8'))
        self.assertTrue(bool(regex.search(response.content)))

    def test_post_view_for_post_test_user_disliked(self):
        post = Post.objects.get(
            title=post_view_tests_user_downvoted_post_title)
        post_id = post.id
        client = Client()
        login_client_for_tests(client)
        response = client.get('/post/' + str(post_id) + '/')
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, post.title)
        self.assertNotContains(response, 'Zobacz więcej')
        regex = re.compile(b'<i class="icon-heart"></i> <b>' +
                           bytes(str(post.count_votes(1)), 'utf-8') + b'</b>')
        self.assertTrue(bool(regex.search(response.content)))
        regex = re.compile(b'<i class="icon-heart-broken disliked"></i> ' +
                           bytes(str(post.count_votes(-1)), 'utf-8'))
        self.assertTrue(bool(regex.search(response.content)))

    def test_post_view_post_not_exists(self):
        post = Post.objects.last()
        post_id = post.id + 1
        client = Client()
        response = client.get('/post/' + str(post_id) + '/')
        self.assertEquals(response.status_code, 404)


class Navigation(TestCase):
    long_post = None

    @classmethod
    def setUp(cls):
        generate()
        cls.long_post = Post.objects.get(title='Długi post o malowaniu')

    def test_see_more_takes_user_to_post_view(self):
        client = Client()
        response = client.get('/all/')
        self.assertEquals(response.status_code, 200)
        regex = re.compile(b'<a class="see-more"')
        self.assertIs(bool(regex.search(response.content)), False)

    def test_back_navigation(self):
        client = Client()
        response = client.get('/post/' + str(self.long_post.id) + '/')
        self.assertEquals(response.status_code, 200)
        regex = re.compile(
            b'<div id=\"goback\"> <p> <a href=\"javascript:history.back\\(\\);\"><i class="icon-angle-double-left"></i>Powr\xc3\xb3t</a> </p> </div>')
        self.assertIs(bool(regex.search(response.content)), True)


class GetSimpleCommentsListTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        generate()

    def test_get_simple_comments_list_with_no_comments(self):
        post = Post.objects.get(title=commentless_post_title)
        user = User.objects.first()
        result = []
        self.assertEquals(get_simple_comments_list(post, user), result)

    def test_get_simple_comments_list_with_one_top_lvl_comment(self):
        post = Post.objects.get(title=one_comment_post_title)
        user = User.objects.first()
        comment = Comment.objects.get(parent_post=post)
        result = [(comment, 0, 0, False, False)]
        self.assertEquals(get_simple_comments_list(post, user), result)

    def test_get_simple_comments_list_with_some_top_lvl_comment(self):
        post = Post.objects.get(title=commentless_post_title)
        user = User.objects.first()
        comment1 = Comment(parent_post=post)
        comment1.save()
        comment2 = Comment(parent_post=post)
        comment2.save()
        result = [(comment1, 0, 0, False, False),
                  (comment2, 0, 0, False, False)]
        self.assertEquals(get_simple_comments_list(post, user), result)

    def test_get_simple_comments_list_with_advanced_structure(self):
        post = Post.objects.get(title=commentless_post_title)
        user = User.objects.get(id=1)
        another_user = User.objects.get(id=2)

        comment1 = Comment(parent_post=post, author=user)
        comment1.save()
        comment2 = Comment(parent_post=post, author=user)
        comment2.save()
        comment3 = Comment(parent_post=post, author=user)
        comment3.save()
        comment4 = Comment(
            parent_post=post, parent_comment=comment1, author=user)
        comment4.save()

        comment_vote1 = CommentVote(user=user, comment=comment1, reaction=1)
        comment_vote2 = CommentVote(user=user, comment=comment3, reaction=-1)
        comment_vote3 = CommentVote(
            user=another_user, comment=comment1, reaction=1)
        comment_vote4 = CommentVote(
            user=another_user, comment=comment2, reaction=1)
        comment_vote5 = CommentVote(
            user=another_user, comment=comment3, reaction=1)
        comment_vote1.save()
        comment_vote2.save()
        comment_vote3.save()
        comment_vote4.save()
        comment_vote5.save()

        result = [
            (comment1, 2, 0, True, False),
            (comment2, 1, 0, False, False),
        ]
        self.assertEquals(get_simple_comments_list(post, user), result)

    def test_get_simple_comments_list_with_advanced_structure_and_no_user(self):
        post = Post.objects.get(title=commentless_post_title)
        user = User.objects.get(id=1)
        another_user = User.objects.get(id=2)

        comment1 = Comment(parent_post=post, author=user)
        comment1.save()
        comment2 = Comment(parent_post=post, author=user)
        comment2.save()
        comment3 = Comment(parent_post=post, author=user)
        comment3.save()
        comment4 = Comment(
            parent_post=post, parent_comment=comment1, author=user)
        comment4.save()

        comment_vote1 = CommentVote(user=user, comment=comment1, reaction=1)
        comment_vote2 = CommentVote(user=user, comment=comment3, reaction=-1)
        comment_vote3 = CommentVote(
            user=another_user, comment=comment1, reaction=1)
        comment_vote4 = CommentVote(
            user=another_user, comment=comment2, reaction=1)
        comment_vote5 = CommentVote(
            user=another_user, comment=comment3, reaction=1)
        comment_vote1.save()
        comment_vote2.save()
        comment_vote3.save()
        comment_vote4.save()
        comment_vote5.save()

        result = [
            (comment1, 2, 0, False, False),
            (comment2, 1, 0, False, False),
        ]
        self.assertEquals(get_simple_comments_list(post, None), result)


class GetPostsTests(TestCase):
    @classmethod
    def setUp(cls):
        generate()

    def single_test(self, posts=[], section_name=None, tag_name=None, user_name=None, logged=False, pv_counter=1):
        client = Client()
        if logged:
            login_client_for_tests(client)
        response = client.get("/login/")
        request = response.wsgi_request
        n = len(posts)

        self.assertEquals(PostVisit.objects.all().exists(), pv_counter != 1)

        if n == 0:
            new_posts = get_posts(request, section_name,
                                  tag_name, user_name, 1)
            self.assertEquals(len(new_posts), 0)
            self.assertEquals(
                PostVisit.objects.all().exists(), pv_counter != 1)
        else:
            x = 0
            for i in range(n):
                new_posts = get_posts(
                    request, section_name, tag_name, user_name, i)
                self.assertEquals(len(new_posts), min(i, n-x))
                for j in range(len(new_posts)):
                    self.assertEquals(new_posts[j][0].title, posts[x+j].title)

                    if logged:
                        pv = PostVisit.objects.filter(post=posts[x+j]).first()
                        self.assertEquals(pv.visit_counter, pv_counter)
                    else:
                        self.assertEquals(
                            PostVisit.objects.all().exists(), pv_counter != 1)

                x = x + len(new_posts)
                if x >= len(posts):
                    break

    def test_get_posts_for_all_for_not_logged_user(self):
        posts = []
        for title in post_titles:
            post = Post.objects.filter(title=title).first()
            posts.append(post)
        self.single_test(posts, section_name='all')

    def test_get_posts_for_all_for_logged_user(self):
        posts = []
        for title in post_titles_for_monika:
            post = Post.objects.filter(title=title).first()
            posts.append(post)
        self.single_test(posts, section_name='all', logged=True)

    def test_get_posts_for_programming_for_not_logged_user(self):
        section = Section.objects.filter(name='programming').first()
        posts = []
        for title in post_titles:
            post = Post.objects.filter(title=title).first()
            if post.section == section:
                posts.append(post)
        self.single_test(posts, section_name='programming')

    def test_get_posts_for_programming_for_logged_user(self):
        section = Section.objects.filter(name='programming').first()
        posts = []
        for title in post_titles_for_monika:
            post = Post.objects.filter(title=title).first()
            if post.section == section:
                posts.append(post)
        self.single_test(posts, section_name='programming', logged=True)

    def test_get_posts_for_soccer_for_not_logged_user(self):
        section = Section.objects.filter(name='soccer').first()
        posts = []
        for title in post_titles:
            post = Post.objects.filter(title=title).first()
            if post.section == section:
                posts.append(post)
        self.single_test(posts, section_name='soccer')

    def test_get_posts_for_soccer_for_logged_user(self):
        section = Section.objects.filter(name='soccer').first()
        posts = []
        for title in post_titles_for_monika:
            post = Post.objects.filter(title=title).first()
            if post.section == section:
                posts.append(post)
        self.single_test(posts, section_name='soccer', logged=True)

    def test_get_posts_for_painting_for_not_logged_user(self):
        section = Section.objects.filter(name='painting').first()
        posts = []
        for title in post_titles:
            post = Post.objects.filter(title=title).first()
            if post.section == section:
                posts.append(post)
        self.single_test(posts, section_name='painting')

    def test_get_posts_for_painting_for_logged_user(self):
        section = Section.objects.filter(name='painting').first()
        posts = []
        for title in post_titles_for_monika:
            post = Post.objects.filter(title=title).first()
            if post.section == section:
                posts.append(post)
        self.single_test(posts, section_name='painting', logged=True)

    def test_get_posts_for_programming_with_tag_cpp_for_not_logged_user(self):
        section_name = 'programming'
        tag_name = 'c++'

        section = Section.objects.filter(name=section_name).first()
        tag = Tag.objects.filter(name=tag_name, section=section).first()
        posts = []
        for title in post_titles:
            post = Post.objects.filter(title=title).first()
            if post.section == section and (tag in list(post.tags.all()) + list(post.implied_tags.all()) or tag_name in post.user_tags_as_list()):
                posts.append(post)

        self.single_test(posts, section_name=section_name, tag_name=tag_name)

    def test_get_posts_for_programming_with_tag_cpp_for_logged_user(self):
        section_name = 'programming'
        tag_name = 'c++'

        section = Section.objects.filter(name=section_name).first()
        tag = Tag.objects.filter(name=tag_name, section=section).first()
        posts = []
        for title in post_titles_for_monika:
            post = Post.objects.filter(title=title).first()
            if post.section == section and (tag in list(post.tags.all()) + list(post.implied_tags.all()) or tag_name in post.user_tags_as_list()):
                posts.append(post)

        self.single_test(posts, section_name=section_name,
                         tag_name=tag_name, logged=True)

    def test_get_posts_for_soccer_with_tag_spotkania_for_not_logged_user(self):
        section_name = 'soccer'
        tag_name = 'spotkania'

        section = Section.objects.filter(name=section_name).first()
        tag = Tag.objects.filter(name=tag_name, section=section).first()
        posts = []
        for title in post_titles:
            post = Post.objects.filter(title=title).first()
            if post.section == section and (tag in list(post.tags.all()) + list(post.implied_tags.all()) or tag_name in post.user_tags_as_list()):
                posts.append(post)

        self.single_test(posts, section_name=section_name, tag_name=tag_name)

    def test_get_posts_for_soccer_with_tag_spotkania_for_logged_user(self):
        section_name = 'soccer'
        tag_name = 'spotkania'

        section = Section.objects.filter(name=section_name).first()
        tag = Tag.objects.filter(name=tag_name, section=section).first()
        posts = []
        for title in post_titles_for_monika:
            post = Post.objects.filter(title=title).first()
            if post.section == section and (tag in list(post.tags.all()) + list(post.implied_tags.all()) or tag_name in post.user_tags_as_list()):
                posts.append(post)

        self.single_test(posts, section_name=section_name,
                         tag_name=tag_name, logged=True)

    def test_get_posts_for_painting_with_tag_torun_for_not_logged_user(self):
        section_name = 'painting'
        tag_name = 'toruń'

        section = Section.objects.filter(name=section_name).first()
        tag = Tag.objects.filter(name=tag_name).first()
        posts = []
        for title in post_titles:
            post = Post.objects.filter(title=title).first()
            if post.section == section and (tag in list(post.tags.all()) + list(post.implied_tags.all()) or tag_name in post.user_tags_as_list()):
                posts.append(post)

        self.single_test(posts, section_name=section_name, tag_name=tag_name)

    def test_get_posts_for_painting_with_tag_torun_for_logged_user(self):
        section_name = 'painting'
        tag_name = 'toruń'

        section = Section.objects.filter(name=section_name).first()
        tag = Tag.objects.filter(name=tag_name).first()
        posts = []
        for title in post_titles_for_monika:
            post = Post.objects.filter(title=title).first()
            if post.section == section and (tag in list(post.tags.all()) + list(post.implied_tags.all()) or tag_name in post.user_tags_as_list()):
                posts.append(post)

        self.single_test(posts, section_name=section_name,
                         tag_name=tag_name, logged=True)

    def test_get_posts_for_author_monika_for_not_logged_user(self):
        user_name = 'monika'

        user = User.objects.filter(login=user_name).first()
        posts = list(Post.objects.filter(
            author=user).order_by('-creation_time'))

        self.single_test(posts, user_name=user_name)

    def test_get_posts_for_author_monika_for_logged_user(self):
        user_name = 'monika'

        user = User.objects.filter(login=user_name).first()
        posts = list(Post.objects.filter(
            author=user).order_by('-creation_time'))

        self.single_test(posts, user_name=user_name, logged=True)

    def test_get_posts_for_author_norbert_for_not_logged_user(self):
        user_name = 'norbert'

        user = User.objects.filter(login=user_name).first()
        posts = list(Post.objects.filter(
            author=user).order_by('-creation_time'))

        self.single_test(posts, user_name=user_name)

    def test_get_posts_for_author_norbert_for_logged_user(self):
        user_name = 'norbert'

        user = User.objects.filter(login=user_name).first()
        posts = list(Post.objects.filter(
            author=user).order_by('-creation_time'))

        self.single_test(posts, user_name=user_name, logged=True)

    def test_get_posts_for_nonexistent_section(self):
        section_name = 'eluwina'

        with self.assertRaises(Http404):
            self.single_test(section_name=section_name)
            self.single_test(section_name=section_name, logged=True)

    def test_get_posts_for_existent_section_and_nonexisting_tag(self):
        section_name = 'programming'
        tag_name = 'nie_ma_takiego_tagu'

        self.single_test(section_name=section_name, tag_name=tag_name)
        self.single_test(section_name=section_name,
                         tag_name=tag_name, logged=True)

    def test_get_posts_for_nonexistent_section_with_tag(self):
        section_name = 'eluwina'
        tag_name = 'c++'

        with self.assertRaises(Http404):
            self.single_test(section_name=section_name, tag_name=tag_name)
            self.single_test(section_name=section_name,
                             tag_name=tag_name, logged=True)

    def test_get_posts_for_nonexistent_user(self):
        user_name = 'no_siema'

        with self.assertRaises(Http404):
            self.single_test(user_name=user_name)
            self.single_test(user_name=user_name, logged=True)

    def test_get_posts_with_no_arguments(self):
        with self.assertRaises(Http404):
            self.single_test()
            self.single_test(logged=True)

    def test_get_posts_many_times(self):
        posts = []
        for title in post_titles_for_monika:
            post = Post.objects.filter(title=title).first()
            posts.append(post)
        for i in range(10):
            self.single_test(posts, section_name='all',
                             logged=True, pv_counter=i+1)

    def test_update_tag_punctations_with_check_conditions(self):
        for tp in TagPunctation.objects.all():
            self.assertEquals(tp.punctation, 0)

        current_user = User.objects.filter(login='monika').first()
        update_tag_punctations(current_user)

        for tp in TagPunctation.objects.all():
            self.assertEquals(tp.punctation, 0)


class DisplayNewPosts(TestCase):
    @classmethod
    def setUp(cls):
        generate()

    def single_test(self, arguments, status_code, posts=[], logged=False):
        client = Client()
        if logged:
            login_client_for_tests(client)
        response = client.post('/post/display_new_posts/', arguments)
        self.assertEquals(response.status_code, status_code)

        if len(posts) == 0:
            if status_code != 404:
                self.assertEquals(response.content, b'\n')
        else:
            self.assertContains(response, 'Zobacz więcej')
            self.assertContains(response, 'alt="awatar autora"')
            self.assertContains(response, 'temu')
            self.assertContains(response, 'Skomentuj')

            for post in posts:
                self.assertContains(response, post.title)

            response = client.post('/post/display_new_posts/', arguments)
            self.assertEquals(response.status_code, status_code)
            self.assertEquals(response.content, b'\n')

    def test_display_posts_for_all(self):
        arguments = {'section_name': 'all',
                     'number_of_posts': 100}
        posts = get_posts_for_section(arguments['section_name'])

        self.single_test(arguments, 200, posts)

    def test_display_posts_for_programming(self):
        arguments = {'section_name': 'programming',
                     'number_of_posts': 100}
        posts = get_posts_for_section(arguments['section_name'])

        self.single_test(arguments, 200, posts)

    def test_display_posts_for_soccer(self):
        arguments = {'section_name': 'soccer',
                     'number_of_posts': 100}
        posts = get_posts_for_section(arguments['section_name'])

        self.single_test(arguments, 200, posts)

    def test_display_posts_for_painting(self):
        arguments = {'section_name': 'painting',
                     'number_of_posts': 100}
        posts = get_posts_for_section(arguments['section_name'])

        self.single_test(arguments, 200, posts)

    def test_display_posts_for_programming_with_tag_cpp(self):
        arguments = {'section_name': 'programming',
                     'tag_name': 'c++',
                     'number_of_posts': 100}
        posts = get_posts_with_tag(
            arguments['section_name'], arguments['tag_name'])

        self.single_test(arguments, 200, posts)

    def test_display_posts_for_soccer_with_tag_spotkania(self):
        arguments = {'section_name': 'soccer',
                     'tag_name': 'spotkania',
                     'number_of_posts': 100}
        posts = get_posts_with_tag(
            arguments['section_name'], arguments['tag_name'])

        self.single_test(arguments, 200, posts)

    def test_display_posts_for_painting_with_tag_torun(self):
        arguments = {'section_name': 'painting',
                     'tag_name': 'toruń',
                     'number_of_posts': 100}
        posts = get_posts_with_tag(
            arguments['section_name'], arguments['tag_name'])

        self.single_test(arguments, 200, posts)

    def test_display_posts_for_author_monika(self):
        arguments = {'user_name': 'monika',
                     'number_of_posts': 100}
        posts = get_posts_for_user(arguments['user_name'])

        self.single_test(arguments, 200, posts)

    def test_display_posts_for_author_norbert(self):
        arguments = {'user_name': 'monika',
                     'number_of_posts': 100}
        posts = get_posts_for_user(arguments['user_name'])

        self.single_test(arguments, 200, posts)

    def test_display_posts_for_logged_user(self):
        arguments = {'section_name': 'all',
                     'number_of_posts': 100}
        posts = get_posts_for_section(arguments['section_name'])

        self.single_test(arguments, 200, posts, logged=True)

    def test_display_posts_for_nonexistent_section(self):
        arguments = {'section_name': 'eluwina',
                     'number_of_posts': 100}

        self.single_test(arguments, 404)

    def test_display_posts_for_existent_section_and_nonexisting_tag(self):
        arguments = {'section_name': 'programming',
                     'tag_name': 'nie_ma_takiego_tagu',
                     'number_of_posts': 100}

        self.single_test(arguments, 200)

    def test_display_posts_for_nonexistent_section_with_tag(self):
        arguments = {'section_name': 'eluwina',
                     'tag_name': 'c++',
                     'number_of_posts': 100}

        self.single_test(arguments, 404)

    def test_display_posts_for_nonexistent_user(self):
        arguments = {'user_name': 'no_siema',
                     'number_of_posts': 100}

        self.single_test(arguments, 404)

    def test_display_posts_with_no_arguments(self):
        arguments = {}

        self.single_test(arguments, 404)

    def test_display_posts_only_with_number_of_posts(self):
        arguments = {'number_of_posts': 100}

        self.single_test(arguments, 404)

    def test_display_posts_only_with_negative_number_of_posts(self):
        arguments = {'section_name': 'all',
                     'number_of_posts': -1}

        self.single_test(arguments, 200)

    def test_display_posts_only_with_wrong_type_of_number_of_posts(self):
        arguments = {'section_name': 'all',
                     'number_of_posts': 'byczku'}

        self.single_test(arguments, 200)
