import os
from functools import partial
from uuid import uuid4



def upload_with_uuid(path):
    return partial(upload_extra_img, path=path)


def upload_extra_img(instance, filename, path):
    
    # hack to get slug for override save method
    from djbooks.models import Book
    if isinstance(instance, Book):
        slug = instance.slug
    else:
        slug = instance.book.slug
    # Shorter uuid as we may not have collisions
    uuid_part = str(uuid4())[:8]
    inner = f'libro_{slug}/extra_{uuid_part}'

    ext = os.path.splitext(filename)[-1].lower()
    return os.path.join(path, inner + ext)