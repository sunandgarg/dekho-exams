from html import escape
from string.templatelib import Interpolation

def render_text_nodes(template):
    fragments = []
    for part in template:
        if isinstance(part, Interpolation):
            fragments.append(escape(str(part.value), quote=True))
        else:
            fragments.append(part)
    return "".join(fragments)

invoice_id = "inv-47"
customer_note = "<admin>& overdue"
markup = render_text_nodes(t"<p>{invoice_id}: {customer_note}</p>")
print(markup)
