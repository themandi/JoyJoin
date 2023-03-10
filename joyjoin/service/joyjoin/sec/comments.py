from common.models import CommentVote
from common.models import max_comments_in_sec_view


def get_comments_list(post, user):
    """ Jest to funkcja, która pobiera listę komentarzy

    Args:
        post(src):pobiera dane o poście, z którego chcemy pobrać liste komentarzy
        user(src): pobiera dane o użytkowniku

    Returns:
        comments_to_display:zwraca liste komentarzy danego posta
    """
    comments_to_display = []
    for comment in post.get_top_level_comments(max_comments_in_sec_view):
        comm_is_liked = False
        comm_is_disliked = False
        if CommentVote.objects.filter(comment=comment, user=user, reaction=1).exists():
            comm_is_liked = True
        if CommentVote.objects.filter(comment=comment, user=user, reaction=-1).exists():
            comm_is_disliked = True

        comm_likes = comment.count_votes(1)
        comm_dislikes = comment.count_votes(-1)

        comments_to_display.append(
            (comment, comm_likes, comm_dislikes, comm_is_liked, comm_is_disliked))
    return comments_to_display
