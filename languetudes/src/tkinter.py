from Tkinter import *
import tkMessageBox
import common
    
class Application(common.Application, Frame, object):
    def __init__(self):
        common.Application.__init__(self)
        Frame.__init__(self)
        self.master.title("Languetudes")
        self.__langue = "aucune"
        self.dico = []
        self.pack()
        self.createWidgets()
        self.mainloop()
    
    def getLangue(self):
        return self.__langue
    def setLangue(self, langue):
        if langue != self.__langue:
            self.dico = []
        self.__langue = langue
        self.btnLangue["text"] = "Langue : %s" %self.__langue
    langue = property(getLangue, setLangue)
    
    def createWidgets(self):
        self.btnLangue = Button(self)
        self.btnLangue["text"] = "Langue : %s" %self.__langue
        self.btnLangue["command"] = self.choisirLangue
        self.btnLangue["fg"]   = "blue"
        self.btnLangue.pack({"side": "top", "fill": X})
        
        self.btnDico = Button(self)
        self.btnDico["text"] = "Dictionnaires"
        self.btnDico["command"] = self.dictionnaire
        self.btnDico["fg"]   = "darkgreen"
        self.btnDico.pack({"side": "top", "fill": X})
        
        self.btnVersion = Button(self)
        self.btnVersion["text"] = "Version"
        self.btnVersion["command"] = self.version
        self.btnVersion.pack({"side": "top", "fill": X})
        
        self.btnTheme = Button(self)
        self.btnTheme["text"] = "Theme"
        self.btnTheme["command"] = self.theme
        self.btnTheme.pack({"side": "top", "fill": X})
        
        self.btnQuit = Button(self)
        self.btnQuit["text"] = " " * 15 + "Sortie" + " " * 15
        self.btnQuit["fg"]   = "red"
        self.btnQuit["command"] =  self.quit
        self.btnQuit.pack({"side": "top", "fill": X})
        
    def choisirLangue(self):
        Langue(self)
        
    def dictionnaire(self):
        if self.langue == "aucune":
            tkMessageBox.showinfo("Aucune langue selectionnee", "Veuillez d'abord choisir une langue.")
            Langue(self)
        else:
            Dictionnaire(self, self.langue)
        
    def version(self):
        if self.langue == "aucune":
            tkMessageBox.showinfo("Aucune langue selectionnee", "Veuillez d'abord choisir une langue.")
            Langue(self)
        elif self.dico == []:
            tkMessageBox.showinfo("Aucun dictionnaire selectionne", "Veuillez d'abord choisir un ou plusieurs dictionnaires.")
            Dictionnaire(self, self.langue)
        else:
            Version(self, self.langue, self.dico)
    
    def theme(self):
        if self.langue == "aucune":
            tkMessageBox.showinfo("Aucune langue selectionnee", "Veuillez d'abord choisir une langue.")
            Langue(self)
        elif self.dico == []:
            tkMessageBox.showinfo("Aucun dictionnaire selectionne", "Veuillez d'abord choisir un ou plusieurs dictionnaires.")
            Dictionnaire(self, self.langue)
        else:
            Theme(self, self.langue, self.dico)
        
class Langue(Toplevel):
    def __init__(self, master):
        Toplevel.__init__(self, master)
        self.title("Choisir une langue")
        self.createWidgets()
        
    def createWidgets(self):
        self.btnQuit = Button(self)
        self.btnQuit["text"] = "Annuler"
        self.btnQuit["fg"]   = "red"
        self.btnQuit["command"] =  self.destroy
        self.btnQuit.pack({"side": "top", "fill": X})
        
        self.btn = []
        for langue in self.master.getLangues():
            button = Button(self)
            button["text"] = langue
            button.bind("<Button-1>", self.choisirLangue)
            button.pack({"side": "top", "fill": X})
            self.btn.append(button)
        
        self.txtAjouter = Entry(self)
        self.txtAjouter["text"] = ""
        self.txtAjouter["fg"]   = "blue"
        self.txtAjouter.bind("<Return>", self.addLangue)
        self.txtAjouter.pack({"side": "top", "fill": X})
        
        self.btnAjouter = Button(self)
        self.btnAjouter["text"] = "Ajouter"
        self.btnAjouter["fg"]   = "blue"
        self.btnAjouter["command"] =  self.addLangue
        self.btnAjouter.pack({"side": "top", "fill": X})
        
    def choisirLangue(self, event):
        self.master.langue = event.widget["text"]
        self.destroy()
        
    def addLangue(self, event=None):
        txt = self.txtAjouter.get().strip().lower()
        if txt == "":
            tkMessageBox.showwarning("Nom de langue incorrect", "Veuillez indiquer un nom de langue dans le champ de texte.")
            self.txtAjouter.focus()
            return
        self.master.addLangue(txt)
        self.master.langue = txt
        self.destroy()
        
class Dictionnaire(Toplevel):
    def __init__(self, master, langue):
        Toplevel.__init__(self, master)
        self.title("%s : dictionnaires" %langue)
        self.langue = langue
        self.createWidgets()
        
    def createWidgets(self):  
        self.btnQuit = Button(self)
        self.defCouleur = self.btnQuit["bg"]
        self.btnQuit["text"] = " " * 30 + "Fermer" + " " * 30
        self.btnQuit["fg"]   = "red"
        self.btnQuit["command"] =  self.destroy
        self.btnQuit.grid(row=0, columnspan=5)
        
        cptrow = 0
        self.dicos = []
        for dico in self.master.getDictionnaires(self.langue):
            cptrow = cptrow + 1
            label = Label(self)
            label["text"] = dico
            label.grid(row=cptrow, column=0)
            
            btnSelect = Button(self)
            btnSelect["text"] = "Sel"
            if dico in self.master.dico:
                btnSelect["bg"] = "green"
            btnSelect.bind("<Button-1>", self.choisirDico)
            btnSelect.grid(row=cptrow, column=1)
            
            btnEdit = Button(self)
            btnEdit["text"] = "Edit"
            btnEdit.bind("<Button-1>", self.editerDico)
            btnEdit.grid(row=cptrow, column=2)
            
            btnVoir = Button(self)
            btnVoir["text"] = "Voir"
            btnVoir.bind("<Button-1>", self.voirDico)
            btnVoir.grid(row=cptrow, column=3)
            
            btnSuppr = Button(self)
            btnSuppr["text"] = "Supp"
            btnSuppr.bind("<Button-1>", self.supprimerDico)
            btnSuppr.grid(row=cptrow, column=4)
            
            self.dicos.append((label, btnSelect, btnEdit, btnVoir, btnSuppr))
            
        self.txtAjouter = Entry(self)
        self.txtAjouter["text"] = ""
        self.txtAjouter["fg"]   = "blue"
        self.txtAjouter.bind("<Return>", self.ajouterDico)
        self.txtAjouter.grid(row=cptrow+1, columnspan=3)
        
        self.btnAjouter = Button(self)
        self.btnAjouter["text"] = "Ajouter"
        self.btnAjouter["fg"]   = "blue"
        self.btnAjouter["command"] =  self.ajouterDico
        self.btnAjouter.grid(row=cptrow+1, column=3, columnspan=2)
        
    def choisirDico(self, event):
        self.master.langue = self.langue
        for i in self.dicos:
            if i[1] == event.widget:
                if i[1]["bg"] == "green":
                    i[1]["bg"] = self.defCouleur
                else:
                    i[1]["bg"] = "green"
            if i[1]["bg"] == "green":
                    self.master.dico.append(i[0]["text"])
                
    def editerDico(self, event):
        for i in self.dicos:
            if i[2] == event.widget:
                Editer(self, self.langue, i[0]["text"])
                return
                
    def voirDico(self, event):
        for i in self.dicos:
            if i[3] == event.widget:
                Voir(self, self.langue, i[0]["text"])
                return
                
    def supprimerDico(self, event):
        for i in self.dicos:
            if i[4] == event.widget:
                if tkMessageBox.askquestion("Confirmation de la suppression", "Etes-vous certain de vouloir supprimer le dictionnaire intitule \"%s\" ?" %i[0]["text"])=="yes":
                    self.master.delDictionnaire(i[0]["text"], self.langue)
                    Dictionnaire(self.master, self.langue)
                    self.destroy()
                return
        
    def ajouterDico(self, event=None):
        txt = self.txtAjouter.get().strip().lower()
        if txt == "":
            tkMessageBox.showwarning("Nom de dictionnaire incorrect", "Veuillez indiquer un nom au dictionnaire dans le champ de texte.")
            self.txtAjouter.focus()
            return
        for b in self.dicos:
            if b[0]["text"] == txt:
                tkMessageBox.showwarning("Nom de dictionnaire incorrect", "Un dictionnaire existant porte deja ce nom. Veuillez en taper un autre.")
                self.txtAjouter.delete(0)
                self.txtAjouter.focus()
                return
        self.master.addDictionnaire(txt, self.langue)
        Dictionnaire(self.master, self.langue)
        Editer(self, self.langue, txt)
        self.destroy()
        
class Editer(Toplevel):
    def __init__(self, master, langue, dico):
        Toplevel.__init__(self, master)
        self.langue = langue
        self.dico = dico
        self.title("%s : %s" %(langue, dico))
        self.createWidgets()
        
    def createWidgets(self):
        self.btnQuit = Button(self)
        self.btnQuit["text"] = " " * 15 + "Fermer" + " " * 15
        self.btnQuit["fg"]   = "red"
        self.btnQuit["command"] =  self.destroy
        self.btnQuit.grid(row=0, columnspan=2)
        
        self.lblFrancais = Label(self)
        self.lblFrancais["text"] = "francais"
        self.lblFrancais.grid(row=1, column=0)
        
        self.txtFrancais = Entry(self)
        self.txtFrancais["text"] = ""
        self.txtFrancais["fg"]   = "blue"
        self.txtFrancais.bind("<Return>", self.valider)
        self.txtFrancais.grid(row=1, column=1)
        
        self.lblEtranger = Label(self)
        self.lblEtranger["text"] = self.langue
        self.lblEtranger.grid(row=2, column=0)
        
        self.txtEtranger = Entry(self)
        self.txtEtranger["text"] = ""
        self.txtEtranger["fg"]   = "blue"
        self.txtEtranger.bind("<Return>", self.valider)
        self.txtEtranger.grid(row=2, column=1)
        
        self.btnAjouter = Button(self)
        self.btnAjouter["text"] = "Ajouter"
        self.btnAjouter["fg"]   = "blue"
        self.btnAjouter["command"] =  self.valider
        self.btnAjouter.grid(row=3, columnspan=2)    
        
    def valider(self, event=None):
        francais = self.txtFrancais.get().strip().lower()
        etranger = self.txtEtranger.get().strip().lower()
        if francais=="":
            tkMessageBox.showwarning("Libelle incorrect", "Veuillez remplir tous les champs de cette boite de dialogue.")
            self.txtFrancais.focus()
            return
        if etranger=="":
            tkMessageBox.showwarning("Libelle incorrect", "Veuillez remplir tous les champs de cette boite de dialogue.")
            self.txtEtranger.focus()
            return
        (f, e, d) = self.master.master.verifierDoublons(self.langue, self.dico, francais, etranger)
        if d == True:
            tkMessageBox.showwarning("Doublons detectes", "Ce couple a deja ete entre. Vous ne pouvez pas faire de doublons.")
            self.txtEtranger.delete(0)
            self.txtFrancais.delete(0)
            self.txtFrancais.focus()
            return
        if f == True:
            if tkMessageBox.askquestion("Doublons detectes", "Le mot francais \"%s\" est deja dans le dictionnaire. Etes-vous certain de l'associer a un second mot %s ?" %(francais, self.langue))=="no":
                self.txtFrancais.delete(0)
                self.txtFrancais.focus()
                return
        if e == True:
            if tkMessageBox.askquestion("Doublons detectes", "Le mot %s \"%s\" est deja dans le dictionnaire. Etes-vous certain de l'associer a un second mot francais ?" %(self.langue, etranger))=="no":
                self.txtEtranger.delete(0)
                self.txtEtranger.focus()
                return
        self.master.master.addCouple(self.langue, self.dico, francais, etranger)
        Editer(self.master, self.langue, self.dico)
        self.destroy()
        
class Voir(Toplevel):
    def __init__(self, master, langue, dico, ordre="francais ASC", debut=0):
        Toplevel.__init__(self, master)
        self.langue = langue
        self.dico = dico
        self.ordre = ordre
        self.debut = debut
        self.longueur = 20
        self.title("%s : %s" %(langue, dico))
        self.createWidgets()
        
    def createWidgets(self):
        self.btnQuit = Button(self)
        self.btnQuit["text"] = " " * 15 + "Fermer" + " " * 15
        self.btnQuit["fg"]   = "red"
        self.btnQuit["command"] =  self.destroy
        self.btnQuit.grid(row=0, columnspan=4)
        
        self.btnFrancais = Button(self)
        self.btnFrancais["text"] = "francais"
        self.btnFrancais["fg"]   = "blue"
        self.btnFrancais.bind("<Button-1>", self.changerOrdre)
        self.btnFrancais.grid(row=1, column=0, columnspan=2)
        
        self.btnEtranger = Button(self)
        self.btnEtranger["text"] = self.langue
        self.btnEtranger["fg"]   = "blue"
        self.btnEtranger.bind("<Button-1>", self.changerOrdre)
        self.btnEtranger.grid(row=1, column=2, columnspan=2)
        
        rowcpt = 1
        self.couples = []
        for i in self.master.master.getCouples(self.langue, self.dico, self.ordre, self.longueur, self.debut):
            rowcpt = rowcpt + 1
            
            lblFr = Label(self)
            lblFr["text"] = i["francais"]
            lblFr.grid(row=rowcpt, column=0, columnspan=2)
            
            lblEtr = Label(self)
            lblEtr["text"] = i["etranger"]
            lblEtr.grid(row=rowcpt, column=2, columnspan=2)
            
            btnSuppr = Button(self)
            btnSuppr["text"] = "x"
            btnSuppr["fg"]   = "red"
            btnSuppr.bind("<Button-1>", self.supprimerCouple)
            btnSuppr.grid(row=rowcpt, column=4)
        
            self.couples.append((lblFr, lblEtr, btnSuppr))
        
        self.btnRAZ = Button(self)
        self.btnRAZ["text"] = "| <"
        self.btnRAZ["fg"]   = "blue"
        self.btnRAZ["command"] = self.remettreAZero
        self.btnRAZ.grid(row=rowcpt+1, column=0)
        
        self.btnPrec = Button(self)
        self.btnPrec["text"] = "< <"
        self.btnPrec["fg"]   = "blue"
        self.btnPrec["command"] = self.precedent
        self.btnPrec.grid(row=rowcpt+1, column=1)
        
        self.btnSuiv = Button(self)
        self.btnSuiv["text"] = "> >"
        self.btnSuiv["fg"]   = "blue"
        self.btnSuiv["command"] = self.suivant
        self.btnSuiv.grid(row=rowcpt+1, column=2)
        
        self.btnMAJ = Button(self)
        self.btnMAJ["text"] = "M.A.J"
        self.btnMAJ["fg"]   = "blue"
        self.btnMAJ["command"] = self.mettreAJour
        self.btnMAJ.grid(row=rowcpt+1, column=3)
        
    def changerOrdre(self, event):
        nvOrdre = self.ordre
        if event.widget == self.btnFrancais:
            if self.ordre in ("francais ASC", "etranger DESC"):
                nvOrdre = "francais DESC"
            else:
                nvOrdre = "francais ASC"
        if event.widget == self.btnEtranger:
            if self.ordre in ("etranger ASC", "francais DESC"):
                nvOrdre = "etranger DESC"
            else:
                nvOrdre = "etranger ASC"
        Voir(self.master, self.langue, self.dico, ordre=nvOrdre, debut=self.debut)
        self.destroy()

    def supprimerCouple(self, event):
        for i in self.couples:
            if i[2] == event.widget:
                if tkMessageBox.askquestion("Confirmation suppression", "Etes-vous certain de vouloir supprimer le couple de mot \"%s\" / \"%s\"" %(i[0]["text"], i[1]["text"]))=="yes":
                    self.master.master.delCouple(self.langue, self.dico, i[0]["text"], i[1]["text"])
                self.mettreAJour()
                break
        
    def remettreAZero(self):
        Voir(self.master, self.langue, self.dico, ordre=self.ordre)
        self.destroy()
        
    def precedent(self):
        nvDebut = self.debut - self.longueur
        if nvDebut < 0:
            nvDebut = 0
        Voir(self.master, self.langue, self.dico, ordre=self.ordre, debut=nvDebut)
        self.destroy()
        
    def suivant(self):
        nvDebut = self.debut + self.longueur
        Voir(self.master, self.langue, self.dico, ordre=self.ordre, debut=nvDebut)
        self.destroy()
        
    def mettreAJour(self):
        Voir(self.master, self.langue, self.dico, ordre=self.ordre, debut=self.debut)
        self.destroy()
        
class Version(Toplevel):
    def __init__(self, master, langue, dicos, total=0, points=0):
        Toplevel.__init__(self, master)
        self.langue = langue
        self.dicos = dicos
        self.total = total
        self.points = points
        self.title("%s : version" %(langue))
        self.createWidgets()
        
    def createWidgets(self):
        self.btnQuit = Button(self)
        self.btnQuit["text"] = " " * 15 + "Terminer" + " " * 15
        self.btnQuit["fg"]   = "red"
        self.btnQuit["command"] =  self.terminer
        self.btnQuit.grid(row=0, columnspan=2)
        
        self.lblScore = Label(self)
        self.lblScore["text"] = "Score : %s / %s" %(self.points, self.total)
        self.lblScore["fg"] = "blue"
        self.lblScore.grid(row=1, columnspan=2)
        
        self.lblEtranger = Label(self)
        self.lblEtranger["text"] = self.langue
        self.lblEtranger.grid(row=2, column=0)
        
        self.txtEtranger = Label(self)
        self.reponse, self.txtEtranger["text"] = self.master.getAleatoire(self.langue, self.dicos)
        self.txtEtranger["bg"]   = "green"
        self.txtEtranger.grid(row=2, column=1, sticky=W+E)
        
        self.lblFrancais = Label(self)
        self.lblFrancais["text"] = "francais"
        self.lblFrancais.grid(row=3, column=0)
        
        self.txtFrancais = Entry(self)
        self.txtFrancais["text"] = ""
        self.txtFrancais["fg"]   = "darkgreen"
        self.txtFrancais.bind("<Return>", self.valider)
        self.txtFrancais.grid(row=3, column=1)
        
        self.btnAjouter = Button(self)
        self.btnAjouter["text"] = "Valider"
        self.btnAjouter["fg"]   = "blue"
        self.btnAjouter["command"] =  self.valider
        self.btnAjouter.grid(row=4, columnspan=2)
        
    def valider(self, event=None):
        if self.master.corriger(self.langue, self.dicos, self.txtFrancais.get(), self.txtEtranger["text"], "version"):
            Version(self.master, self.langue, self.dicos, self.total+1, self.points+1)
        else:
            tkMessageBox.showinfo("Mauvaise reponse", "Faux. La bonne traduction est : \"%s\"" %self.reponse)
            Version(self.master, self.langue, self.dicos, self.total+1, self.points)
        self.destroy()
        
    def terminer(self):
        self.destroy()
        
class Theme(Toplevel):
    def __init__(self, master, langue, dicos, total=0, points=0):
        Toplevel.__init__(self, master)
        self.langue = langue
        self.dicos = dicos
        self.total = total
        self.points = points
        self.title("%s : theme" %(langue))
        self.createWidgets()
        
    def createWidgets(self):
        self.btnQuit = Button(self)
        self.btnQuit["text"] = " " * 15 + "Terminer" + " " * 15
        self.btnQuit["fg"]   = "red"
        self.btnQuit["command"] =  self.terminer
        self.btnQuit.grid(row=0, columnspan=2)
        
        self.lblScore = Label(self)
        self.lblScore["text"] = "Score : %s / %s" %(self.points, self.total)
        self.lblScore["fg"] = "blue"
        self.lblScore.grid(row=1, columnspan=2)
        
        self.lblFrancais = Label(self)
        self.lblFrancais["text"] = "francais"
        self.lblFrancais.grid(row=2, column=0)
        
        self.txtFrancais = Label(self)
        self.txtFrancais["text"], self.reponse = self.master.getAleatoire(self.langue, self.dicos)
        self.txtFrancais["bg"]   = "green"
        self.txtFrancais.grid(row=2, column=1, sticky=W+E)
        
        self.lblEtranger = Label(self)
        self.lblEtranger["text"] = self.langue
        self.lblEtranger.grid(row=3, column=0)
        
        self.txtEtranger = Entry(self)
        self.txtEtranger["text"] = ""
        self.txtEtranger["fg"]   = "darkgreen"
        self.txtEtranger.bind("<Return>", self.valider)
        self.txtEtranger.grid(row=3, column=1)
        
        self.btnAjouter = Button(self)
        self.btnAjouter["text"] = "Valider"
        self.btnAjouter["fg"]   = "blue"
        self.btnAjouter["command"] =  self.valider
        self.btnAjouter.grid(row=4, columnspan=2)
        
    def valider(self, event=None):
        if self.master.corriger(self.langue, self.dicos, self.txtFrancais["text"], self.txtEtranger.get(), "theme"):
            Theme(self.master, self.langue, self.dicos, self.total+1, self.points+1)
        else:
            tkMessageBox.showinfo("Mauvaise reponse", "Faux. La bonne traduction est : \"%s\"" %self.reponse)
            Theme(self.master, self.langue, self.dicos, self.total+1, self.points)
        self.destroy()
        
    def terminer(self):
        self.destroy()