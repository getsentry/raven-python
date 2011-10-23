def get_data_from_request(request):
    if not request.POST and request.raw_post_data:
        data = request.raw_post_data
    else:
        data = dict(request.REQUEST.items())

    result = {
        'sentry.interfaces.Http': {
            'method': request.method,
            'url': request.build_absolute_uri(),
            'query_string': request.META.get('QUERY_STRING'),
            'data': data,
            'cookies': dict(request.COOKIES),
        }
    }

    if hasattr(request, 'user'):
        if request.user.is_authenticated():
            user_info = {
                'is_authenticated': True,
                'id': request.user.pk,
                'username': request.user.username,
                'email': request.user.email,
            }
        else:
            user_info = {
                'is_authenticated': False,
            }

        result['sentry.interfaces.User'] = user_info

    return result

def linebreak_iter(template_source):
    yield 0
    p = template_source.find('\n')
    while p >= 0:
        yield p+1
        p = template_source.find('\n', p+1)
    yield len(template_source) + 1

def get_data_from_template(source):
    origin, (start, end) = source
    template_source = origin.reload()

    lineno = None
    upto = 0
    source_lines = []
    for num, next in enumerate(linebreak_iter(template_source)):
        if start >= upto and end <= next:
            lineno = num
        source_lines.append((num, template_source[upto:next]))
        upto = next

    if not source_lines or lineno is None:
        return {}

    pre_context = source_lines[max(lineno-3, 0):lineno]
    post_context = source_lines[lineno+1:lineno+4]
    context_line = source_lines[lineno]

    return {
        'sentry.interfaces.Template': {
            'filename': origin.name,
            'pre_context': pre_context,
            'context_line': context_line[1],
            'lineno': lineno,
            'post_context': post_context,
        },
        'culprit': origin.loadname,
    }
