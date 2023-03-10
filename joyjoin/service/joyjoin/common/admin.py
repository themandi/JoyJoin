from django.contrib import admin

from .models import Comment, CommentVote, Post, PostVisit, Section
from .models import Tag, TagImplication, TagPunctation, User, Vote


models = [
    Comment,
    CommentVote,
    Post,
    PostVisit,
    Section,
    Tag,
    TagImplication,
    TagPunctation,
    User,
    Vote,
]

for model in models:
    admin.site.register(model)
