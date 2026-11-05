from django.template import Context, Engine

label = '<script>alert("receipt")</script>'
template = Engine(debug=False).from_string("<h2>{{ label }}</h2>")
rendered = template.render(Context({"label": label}, autoescape=True))
print("literal script tag:", "<script>" in rendered)
print("escaped tag:", "&lt;script&gt;" in rendered)
print("original preserved:", label.startswith("<script>"))
