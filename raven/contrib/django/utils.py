def linebreak_iter(template_source):
    yield 0
    p = template_source.find('\n')
    while p >= 0:
        yield p + 1
        p = template_source.find('\n', p + 1)
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
        source_lines.append(template_source[upto:next])
        upto = next

    if not source_lines or lineno is None:
        return {}

    pre_context = source_lines[max(lineno - 3, 0):lineno]
    post_context = source_lines[(lineno + 1):(lineno + 4)]
    context_line = source_lines[lineno]

    return {
        'sentry.interfaces.Template': {
            'filename': origin.loadname,
            'abs_path': origin.name,
            'pre_context': pre_context,
            'context_line': context_line,
            'lineno': lineno,
            'post_context': post_context,
        },
        'culprit': origin.loadname,
    }
