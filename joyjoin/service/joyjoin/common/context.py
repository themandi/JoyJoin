from .models import Section, User


def get_user_from_session(request):
    user = None
    logged_in_as = request.session.get('logged_in_as', default=None)
    try:
        user = User.objects.get(login=logged_in_as)
    except (User.DoesNotExist):
        return None
    return user


def set_common_context(request, context):
    logged_user = get_user_from_session(request)
    set_user_context(request, context, logged_user)
    set_section_context(request, context, logged_user)
    set_current_section_name_context(request, context)


def set_user_context(request, context, user):
    logged_in_as = request.session.get('logged_in_as', default=None)
    context['current_user'] = None
    if logged_in_as:
        try:
            current_user = User.objects.get(login=logged_in_as)
            context['current_user'] = current_user
        except (User.DoesNotExist):
            pass


def set_current_section_name_context(request, context):
    context['current_section_name'] = request.session.get(
        'current_section_name')


def set_section_context(request, context, user):
    sections = Section.objects.all()
    if user:
        user_sections = []
        recommended_sections = []
        for sec in sections:
            if sec.users.filter(login=user.login):
                user_sections.append(sec)
            else:
                recommended_sections.append(sec)
        context['user_sections'] = user_sections
        context['recommended_sections'] = recommended_sections
    else:
        popular_sections = []
        for sec in sections:
            popular_sections.append(sec)
        context['popular_sections'] = popular_sections
