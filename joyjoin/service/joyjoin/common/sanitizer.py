import re


def is_sanitary(text):
    """
    Sprawdza czy podany text nie zawiera niedozwolonych tagów HTML.
    Zwraca True jeśli nie zawiera.
    """
    accepted_tags_re = re.compile('<br>|<p>|</p>|<h1>|</h1>|<h2>|</h2>|<strong>|</strong>|<em>|</em>|<pre class="ql-syntax" spellcheck="false">|</pre>|<ol>|</ol>|<ul>|</ul>|<li>|</li>|<a href="(.+)" target="_blank">|</a>|<img src="(.+)">|<iframe class="ql-video" frameborder="0" allowfullscreen="true" src="(.+)">|</iframe>')
    tags_re = re.compile('<.*?>')
    # usuwa dozwolone tagi
    cleaned = re.sub(accepted_tags_re, '', text)
    # sprawdza czy tekst zawiera inne tagi
    result = tags_re.search(cleaned)
    if result is None:
        return True
    print("is_sanitary: bad string detected with match {}".format(result))
    return False
