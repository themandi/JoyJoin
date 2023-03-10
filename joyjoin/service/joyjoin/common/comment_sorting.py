# sposoby sortowania komentarzy (po czym mają być sortowane)
comment_sorting_keys = {
    "najnowsze": (lambda x: x.creation_time, 'reverse'),
    "najstarsze": (lambda x: x.creation_time, 'not_reverse'),
    "najbardziej popularne": (lambda x: x.count_votes(1) + x.count_votes(-1), 'reverse'),
    "najlepiej oceniane": (lambda x: x.count_votes(1) - x.count_votes(-1), 'reverse'),
    "najgorzej oceniane": (lambda x: x.count_votes(-1) - x.count_votes(1), 'reverse'),
}


def sort_comments(comments, sort_type):
    if sort_type not in comment_sorting_keys:
        sort_type = "najnowsze"
    to_reverse = (comment_sorting_keys[sort_type][1] == 'reverse')

    return sorted(comments, key=comment_sorting_keys[sort_type][0], reverse=to_reverse)
