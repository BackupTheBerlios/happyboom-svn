-- MySQL dump 9.11
--
-- Host: localhost    Database: languetudes
-- ------------------------------------------------------
-- Server version	4.0.23_Debian-3ubuntu2-log

--
-- Table structure for table `__dictionnaire`
--

DROP TABLE IF EXISTS `__dictionnaire`;
CREATE TABLE `__dictionnaire` (
  `id` int(9) NOT NULL auto_increment,
  `intitule` varchar(63) default NULL,
  `langue` int(9) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `langue` (`langue`,`intitule`)
) TYPE=MyISAM;

--
-- Dumping data for table `__dictionnaire`
--


/*!40000 ALTER TABLE `__dictionnaire` DISABLE KEYS */;
LOCK TABLES `__dictionnaire` WRITE;
INSERT INTO `__dictionnaire` VALUES (13,'nombres',5),(7,'test',7),(12,'lecon no1',8),(10,'test2',7),(11,'nombres',6);
UNLOCK TABLES;
/*!40000 ALTER TABLE `__dictionnaire` ENABLE KEYS */;

--
-- Table structure for table `__langue`
--

DROP TABLE IF EXISTS `__langue`;
CREATE TABLE `__langue` (
  `id` int(9) NOT NULL auto_increment,
  `intitule` varchar(31) NOT NULL default '',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `intitule` (`intitule`)
) TYPE=MyISAM;

--
-- Dumping data for table `__langue`
--


/*!40000 ALTER TABLE `__langue` DISABLE KEYS */;
LOCK TABLES `__langue` WRITE;
INSERT INTO `__langue` VALUES (5,'roumain'),(6,'anglais'),(7,'esperanto'),(8,'chinois');
UNLOCK TABLES;
/*!40000 ALTER TABLE `__langue` ENABLE KEYS */;

--
-- Table structure for table `dico10`
--

DROP TABLE IF EXISTS `dico10`;
CREATE TABLE `dico10` (
  `id` int(9) NOT NULL auto_increment,
  `francais` varchar(63) NOT NULL default '',
  `etranger` varchar(63) NOT NULL default '',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `francais` (`francais`,`etranger`),
  KEY `etranger` (`etranger`,`francais`)
) TYPE=MyISAM;

--
-- Dumping data for table `dico10`
--


/*!40000 ALTER TABLE `dico10` DISABLE KEYS */;
LOCK TABLES `dico10` WRITE;
INSERT INTO `dico10` VALUES (1,'un','unu'),(2,'deux','du'),(3,'trois','tri'),(4,'quatre','kvar'),(5,'cinq','kvin'),(6,'six','ses'),(7,'sept','sep'),(8,'huit','ok'),(9,'neuf','naux'),(10,'dix','dek');
UNLOCK TABLES;
/*!40000 ALTER TABLE `dico10` ENABLE KEYS */;

--
-- Table structure for table `dico11`
--

DROP TABLE IF EXISTS `dico11`;
CREATE TABLE `dico11` (
  `id` int(9) NOT NULL auto_increment,
  `francais` varchar(63) NOT NULL default '',
  `etranger` varchar(63) NOT NULL default '',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `francais` (`francais`,`etranger`),
  KEY `etranger` (`etranger`,`francais`)
) TYPE=MyISAM;

--
-- Dumping data for table `dico11`
--


/*!40000 ALTER TABLE `dico11` DISABLE KEYS */;
LOCK TABLES `dico11` WRITE;
INSERT INTO `dico11` VALUES (1,'un','one'),(2,'deux','two'),(3,'trois','three'),(4,'quatre','four'),(5,'cinq','five'),(6,'six','six'),(7,'sept','seven'),(8,'huit','eight'),(9,'neuf','nine'),(10,'dix','ten');
UNLOCK TABLES;
/*!40000 ALTER TABLE `dico11` ENABLE KEYS */;

--
-- Table structure for table `dico12`
--

DROP TABLE IF EXISTS `dico12`;
CREATE TABLE `dico12` (
  `id` int(9) NOT NULL auto_increment,
  `francais` varchar(63) NOT NULL default '',
  `etranger` varchar(63) NOT NULL default '',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `francais` (`francais`,`etranger`),
  KEY `etranger` (`etranger`,`francais`)
) TYPE=MyISAM;

--
-- Dumping data for table `dico12`
--


/*!40000 ALTER TABLE `dico12` DISABLE KEYS */;
LOCK TABLES `dico12` WRITE;
INSERT INTO `dico12` VALUES (1,'tu','ni'),(2,'bien','hao'),(3,'vieux','lao'),(4,'roi','wang'),(5,'cheval','ma'),(6,'je','wo'),(7,'assez','hen'),(8,'petit','xiao'),(9,'il','ta'),(10,'et ... ?','ne'),(11,'elle','ta'),(12,'aussi','ye'),(13,'et','he'),(14,'demander','wen');
UNLOCK TABLES;
/*!40000 ALTER TABLE `dico12` ENABLE KEYS */;

--
-- Table structure for table `dico13`
--

DROP TABLE IF EXISTS `dico13`;
CREATE TABLE `dico13` (
  `id` int(9) NOT NULL auto_increment,
  `francais` varchar(63) NOT NULL default '',
  `etranger` varchar(63) NOT NULL default '',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `francais` (`francais`,`etranger`),
  KEY `etranger` (`etranger`,`francais`)
) TYPE=MyISAM;

--
-- Dumping data for table `dico13`
--


/*!40000 ALTER TABLE `dico13` DISABLE KEYS */;
LOCK TABLES `dico13` WRITE;
INSERT INTO `dico13` VALUES (1,'un','unu'),(2,'deux','doi'),(3,'trois','trei'),(4,'quatre','patru'),(5,'cinq','cinci'),(6,'six','sase'),(7,'sept','sapte'),(8,'huit','opt'),(9,'neuf','noua'),(10,'dix','zece');
UNLOCK TABLES;
/*!40000 ALTER TABLE `dico13` ENABLE KEYS */;

--
-- Table structure for table `dico7`
--

DROP TABLE IF EXISTS `dico7`;
CREATE TABLE `dico7` (
  `id` int(9) NOT NULL auto_increment,
  `francais` varchar(63) NOT NULL default '',
  `etranger` varchar(63) NOT NULL default '',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `francais` (`francais`,`etranger`),
  KEY `etranger` (`etranger`,`francais`)
) TYPE=MyISAM;

--
-- Dumping data for table `dico7`
--


/*!40000 ALTER TABLE `dico7` DISABLE KEYS */;
LOCK TABLES `dico7` WRITE;
INSERT INTO `dico7` VALUES (1,'eau','akvo'),(2,'tasse','taso'),(3,'cafe','kafo'),(4,'homme','viro'),(5,'fils','filo'),(6,'garcon','knabo'),(7,'the','teo'),(8,'ami','amiko'),(9,'etre','esti'),(10,'nouveau','nova'),(11,'en bonne sante','sana'),(12,'je','mi'),(13,'tu','vi'),(14,'il','li'),(15,'elle','sxi'),(16,'nous','ni'),(17,'vous','vi'),(19,'ils','ili'),(20,'elles','ili'),(21,'on','oni'),(22,'soi-meme','si');
UNLOCK TABLES;
/*!40000 ALTER TABLE `dico7` ENABLE KEYS */;

