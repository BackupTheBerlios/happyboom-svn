import ConfigParser

class Application:
    dico_id_sql = """SELECT __dictionnaire.id AS id
FROM __langue, __dictionnaire
WHERE __dictionnaire.langue=__langue.id
  AND __langue.intitule='%s'
  AND __dictionnaire.intitule='%s'"""
    
    def __init__(self):
        # Chargement du fichier de configuration
        self.conf = ConfigParser.ConfigParser()
        #fichConf = __file__[:-2] + "conf"
        self.conf.read("languetudes.conf")
        # import de module de base de donnees compatible API-DB
        bdd = __import__(self.conf.get("Base","type"), globals())
        bdd = __import__(self.conf.get("Base","type")+".cursors", globals())
        
        # recuperation des parametres de connexion
        params = {"host":"", "user":"", "passwd":"", "db":"", "port":0}
        if self.conf.has_option("Base","hote"):
                params["host"] = self.conf.get("Base","hote")
        if self.conf.has_option("Base","utilisateur"):
                params["user"] = self.conf.get("Base","utilisateur")
        if self.conf.has_option("Base","motpasse"):
                params["passwd"] = self.conf.get("Base","motpasse")
        if self.conf.has_option("Base","nombase"):
                params["db"] = self.conf.get("Base","nombase")
        if self.conf.has_option("Base","port"):
                params["port"] = int(self.conf.get("Base","port"))
        # connexion a la base de donnees
        self.connexion = bdd.connect(**params)
        # creation d'un curseur de parcours de resultat SQL
        self.curseur = self.connexion.cursor(bdd.cursors.DictCursor)
        self.curseur.execute("SHOW tables")
        result = []
        for i in self.curseur.fetchall():
            result.extend(i.values())
        # Creation des tables
        if "__langue" not in result:
            self.curseur.execute("""CREATE TABLE __dictionnaire (
    id INT(9) primary key auto_increment,
    intitule VARCHAR(63),
    langue INT(9) REFERENCES __langue(id),
    INDEX(langue, intitule)
    )""")
            self.curseur.execute("""CREATE TABLE __langue (
    id INT(9) PRIMARY KEY AUTO_INCREMENT,
    intitule VARCHAR(31) NOT NULL,
    INDEX(intitule)
    )""")
        
    def getLangues(self):
        self.curseur.execute("SELECT intitule FROM __langue ORDER BY intitule")
        result = []
        for i in self.curseur.fetchall():
            result.append(i["intitule"])
        return result
        
    def addLangue(self, langue):
        self.curseur.execute("INSERT INTO __langue(intitule) VALUES('%s')" %langue.lower())

    def getDictionnaires(self, langue):
        self.curseur.execute("SELECT __dictionnaire.intitule FROM __langue, __dictionnaire WHERE __dictionnaire.langue = __langue.id AND __langue.intitule = '%s' ORDER BY __dictionnaire.intitule" %langue)
        result = []
        for i in self.curseur.fetchall():
            result.append(i["intitule"].replace("\\\\", "\\").replace("\\'", "'").replace('\\"', '"'))
        return result
        
    def addDictionnaire(self, nom, langue):
        self.curseur.execute("SELECT id FROM __langue WHERE intitule='%s'" %langue)
        langue_id = self.curseur.fetchall()[0]["id"]
        nom = nom.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
        self.curseur.execute("INSERT INTO __dictionnaire(intitule, langue) VALUES('%s', %s)" %(nom, langue_id))
        self.curseur.execute("SELECT id FROM __dictionnaire WHERE langue=%s AND intitule='%s'" %(langue_id, nom))
        dico_id = self.curseur.fetchall()[0]["id"]
        self.curseur.execute("""CREATE TABLE dico%s(
id INT(9) PRIMARY KEY AUTO_INCREMENT,
francais VARCHAR(63) NOT NULL,
etranger VARCHAR(63) NOT NULL,
INDEX(francais, etranger),
INDEX(etranger, francais)
)""" %dico_id)
        
    def delDictionnaire(self, nom, langue):
        nom = nom.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
        self.curseur.execute(self.dico_id_sql %(langue, nom))
        dico_id = self.curseur.fetchall()[0]["id"]
        self.curseur.execute("DELETE FROM __dictionnaire WHERE id=%s" %dico_id)
        self.curseur.execute("DROP TABLE dico%s" %dico_id)
        
    def verifierDoublons(self, langue, nom, francais, etranger):
        nom = nom.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
        francais = francais.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
        etranger = etranger.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
        self.curseur.execute(self.dico_id_sql %(langue, nom))
        dico_id = self.curseur.fetchall()[0]["id"]
        self.curseur.execute("SELECT francais, etranger FROM dico%s WHERE francais='%s' OR etranger='%s'" %(dico_id, francais, etranger))
        f, e = (False, False)
        for i in self.curseur.fetchall():
            if i["francais"] == francais and i["etranger"] == etranger:
                return (True, True, True)
            if i["francais"] == francais:
                f = True
            if i["etranger"] == etranger:
                e = True
        return (f, e, False)
        
    def addCouple(self, langue, nom, francais, etranger):
        nom = nom.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
        francais = francais.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
        etranger = etranger.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
        self.curseur.execute(self.dico_id_sql %(langue, nom))
        dico_id = self.curseur.fetchall()[0]["id"]
        self.curseur.execute("INSERT INTO dico%s(francais, etranger) VALUES ('%s', '%s')" %(dico_id, francais, etranger))
        
    def delCouple(self, langue, nom, francais, etranger):
        nom = nom.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
        francais = francais.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
        etranger = etranger.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
        self.curseur.execute(self.dico_id_sql %(langue, nom))
        dico_id = self.curseur.fetchall()[0]["id"]
        self.curseur.execute("DELETE FROM dico%s WHERE francais='%s' AND etranger='%s'" %(dico_id, francais, etranger))
        
    def getCouples(self, langue, nom, ordre="francais ASC", longueur=None, debut=0):
        nom = nom.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
        self.curseur.execute(self.dico_id_sql %(langue, nom))
        dico_id = self.curseur.fetchall()[0]["id"]
        limit = ""
        if longueur != None:
            limit = " LIMIT %s, %s" %(debut, longueur)
        self.curseur.execute("SELECT francais, etranger FROM dico%s ORDER BY %s%s" %(dico_id, ordre, limit))
        result = self.curseur.fetchall()
        for i in range(len(result)):
            result[i]["francais"] = result[i]["francais"].replace("\\\\", "\\").replace("\\'", "'").replace('\\"', '"')
            result[i]["etranger"] = result[i]["etranger"].replace("\\\\", "\\").replace("\\'", "'").replace('\\"', '"')
        return result
        
    def getAleatoire(self, langue, dicos):
        requete = ""
        for nom in dicos:
            nom = nom.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
            self.curseur.execute(self.dico_id_sql %(langue, nom))
            dico_id = self.curseur.fetchall()[0]["id"]
            requete = requete + "SELECT francais, etranger FROM dico%s UNION " %dico_id
        self.curseur.execute("%s ORDER BY RAND() LIMIT 1" %(requete[:-7]))
        result = self.curseur.fetchall()[0]
        result["francais"] = result["francais"].replace("\\\\", "\\").replace("\\'", "'").replace('\\"', '"')
        result["etranger"] = result["etranger"].replace("\\\\", "\\").replace("\\'", "'").replace('\\"', '"')
        return (result["francais"], result["etranger"])
        
    def corriger(self, langue, dicos, francais, etranger, type):
        francais = francais.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
        etranger = etranger.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
        if type == "version":
            test = "etranger='%s'" %etranger
        else:
            test = "francais='%s'" %francais
        requete = ""
        for nom in dicos:
            nom = nom.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
            self.curseur.execute(self.dico_id_sql %(langue, nom))
            dico_id = self.curseur.fetchall()[0]["id"]
            requete = requete + "SELECT francais, etranger FROM dico%s WHERE %s UNION " %(dico_id, test)
        self.curseur.execute(requete[:-7])
        result = self.curseur.fetchall()
        if type == "version":
            for i in result:
                if i["francais"] == francais:
                    return True
            return False
        else:
            for i in result:
                if i["etranger"] == etranger:
                    return True
            return False
        
    def __del__(self):
        # fermeture du curseur
        self.curseur.close()
        # fermeture de la connexion
        self.connexion.close()