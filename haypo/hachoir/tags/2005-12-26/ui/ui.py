def loadInterface(hachoir):
    global ui 
    global window
    import os
    import pygtk
    try:
        pygtk.require ('2.0') # 2.2 for Clipboard
    except:
        raise Exception("Sorry, you need pyGTK version 2.0")	
    from ui_glade import GladeInterface    
    glade = os.path.join(os.path.dirname(__file__), 'hachoir.glade')
    ui = GladeInterface(glade, hachoir)
    window = ui.window
    hachoir.ui = ui 
    hachoir.ui.on_row_click = hachoir.onRowClick
    hachoir.ui.on_go_parent = hachoir.onGoParent

ui = None
window = None
