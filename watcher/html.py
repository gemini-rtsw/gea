class row:
  def __init__(self, heading = False, footing = False, clas = None, id = None):
    self.cols     = []
    self.heading  = heading
    self.footing  = footing
    self.clas     = clas 
    self.id       = id
    self.rowcount = None

  def col(self, content, clas = None, id = None, style = None, attr = None):
    c = col(clas = clas, id = id, style = style, attr = attr)
    self.cols += (c, )
    c.content  = content
    return c

class col:
  def __init__(self, content = "&nbsp;", clas = None, id = None, style = None, attr = None):
    self.content = content
    self.clas    = clas
    self.id      = id
    self.style   = style
    self.attr    = attr

class table:
  def __init__(self, clas = None, id = None, style = None):
    self.rows     = []
    self.clas     = clas
    self.id       = id
    self.style    = style
    self.rowcount = 0

  def row(self, heading = False, footing = False, clas = None, id = None):
    r = row(heading, footing, clas, id)
    self.rows += (r, )
    self.rowcount += 1
    r.rowcount = self.rowcount
    return r    
  
  def show(self, margin = 2, indent = 2):
    html = ""
    imsg = " " * margin
    tmsg = imsg + "<table"
    if self.clas:  tmsg += " class=\"" + self.clas + "\""
    if self.id:    tmsg += " id=\""    + self.id   + "\""
    if self.style: tmsg += " style=\"" + self.style   + "\""
    tmsg += ">"
    html += tmsg + "\n"

    rowlen = 0

    for r in self.rows:
      if len(r.cols) > rowlen:
        rowlen = len(r.cols)

    for r in self.rows:
      #if r.heading:   trt = "thead"
      #elif r.footing: trt = "tfoot"
      #else:           trt = "tr"
      trt = "tr"
      tmsg = imsg + " " * indent + "<" + trt
      if r.clas: tmsg += " class=\"" + r.clas + "\""
      if r.id:   tmsg += " id=\""    + r.id   + "\""
      tmsg += ">"
      html += tmsg + "\n"
      
      for i, c in enumerate(r.cols):
        tmsg = imsg + " " * (indent * 2) + "<td"
        if len(r.cols) < rowlen and i == len(r.cols) - 1:
          tmsg += " colspan=\"%d\"" % (rowlen - (len(r.cols) - 1))
        if c.clas:  tmsg += " class=\"" + c.clas + "\""
        if c.id:    tmsg += " id=\""    + c.id   + "\""
        if c.style: tmsg += " style=\""    + c.style   + "\""
        if c.attr:
          for key in c.attr:
            tmsg += " data-{0}=\"{1}\"".format(key, c.attr[key])
        tmsg += "> "
        tmsg += c.content
        tmsg += " </td>"
        html += tmsg + "\n"
      # html += " <td> %d </td>" % r.rowcount		# DEBUG

      html += (imsg + " " * indent + "</%s>\n" % trt)
    html += (imsg + "</table>\n")
    return html

if __name__ == '__main__':
  t = table(clas = "OINK", id = "DOG", style = "border: 1px solid black;")
  r = t.row(heading = True)
  c = r.col("pigs", id = "dick", clas = "john", style = "cows:black;")
  c = r.col("Bla, bla, bla, bla.")
  for rX in range(0, 4):
    r = t.row(clas = "BIG")
    for cX in range(0, 5):
      c = r.col("pig %d %d" % (rX, cX), clas = "DUCK", id = "ID%d" % cX)
  r = t.row(footing = True)
  c = r.col("MOO", attr={"foo":123})

  print(t.show())
