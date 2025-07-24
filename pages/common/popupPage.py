#!/usr/bin/python
        
from pages.geaBasePage import GeaBasePage
from GEAHtml import HTMLCont
import GEAVars

class PopupPage(GeaBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """
        #For now just write out straight html.
        GeaBasePage._assemblePage(self, topMenuList=topMenuList)
        
        html=self.html
        contents="""
<html>

<head>
<title>GEA - Popup</title>

</head>

<body>
<script type="text/javascript">
var text=document.location.search.substring(1)
document.writeln(text)
</script>

</body>

</html>
"""
        html.doc.append(contents)
        
def main(outStream=GEAVars.outStream, standAlone=False):

    PopupPage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
