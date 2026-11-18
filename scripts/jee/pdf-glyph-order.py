"""Compare MathJax SVG glyphs in the PDF painter order; preserve token identity and option order."""
import re,xml.etree.ElementTree as ET
from html.parser import HTMLParser

def pdf_order(s):
 out=[]
 def walk(e):
  if e.tag=='use':
   code=int(e.get('href','').rsplit('-',1)[-1],16)
   if code!=0x2061:out.append(chr(code)) # U+2061 function application has no painted glyph.
   return
  children=list(e)
  # MathJax's root consists of a radical, radicand and horizontal rule.
  # The PDF SVG renderer paints the radicand before the radical path.
  if len(children) in (3,4) and children[-1].tag=='rect' and all(c.tag=='g' for c in children[:-1]):
   uses=list(children[0].iter('use'))
   if len(uses)==1 and uses[0].get('href','').endswith('-221A') and len(list(children[0]))==1:
    children=([children[1],children[0],children[2]] if len(children)==3 else [children[2],children[1],children[0],children[3]])
  for child in children:walk(child)
 class SVGs(HTMLParser):
  def __init__(self):super().__init__(convert_charrefs=True);self.stack=[];self.roots=[]
  def handle_starttag(self,tag,attrs):
   if tag!='svg' and not self.stack:return
   e=ET.Element(tag,dict(attrs))
   if self.stack:self.stack[-1].append(e)
   else:self.roots.append(e)
   self.stack.append(e)
  def handle_endtag(self,tag):
   if self.stack and self.stack[-1].tag==tag:self.stack.pop()
  def handle_startendtag(self,tag,attrs):self.handle_starttag(tag,attrs);self.handle_endtag(tag)
 parser=SVGs();parser.feed(s)
 if parser.stack:return '?'
 for root in parser.roots:walk(root)
 return ''.join(out)

if __name__=='__main__':
 root='<svg><g><g><use href="/math.svg#MJX-TEX-N-221A" /></g><g><use href="/math.svg#MJX-TEX-N-32" /></g><rect width="500" /></g></svg>'
 assert pdf_order(root)=='2√'
 assert pdf_order(root.replace('221A','2B'))=='+2', 'Do not reorder ordinary operators'
 assert pdf_order('<svg><use href="/math.svg#MJX-TEX-N-2061" /></svg>')==''
 indexed=root.replace('<g><use href="/math.svg#MJX-TEX-N-32" /></g>', '<g><use href="/math.svg#MJX-TEX-N-33" /></g><g><use href="/math.svg#MJX-TEX-N-32" /></g>')
 assert pdf_order(indexed)=='23√', 'Indexed roots paint radicand, index, then radical'
 nested=root.replace('<use href="/math.svg#MJX-TEX-N-32" />', root)
 assert pdf_order(nested)=='2√√'
 assert pdf_order('<svg><svg><use href="/math.svg#MJX-TEX-N-28" /></svg><use href="/math.svg#MJX-TEX-N-29" /></svg>')=='()'
 assert pdf_order('<svg><use href="/math.svg#MJX-TEX-N-32" />')=='?'
 print('Root drawing-order checks passed')
