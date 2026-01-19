BEGIN TRANSACTION;
DROP TABLE IF EXISTS "pastruns";
CREATE TABLE "pastruns" (
    "id"    INTEGER,
    "rotationID"    INTEGER NOT NULL DEFAULT 0,
    "site"    varchar(30) NOT NULL,
    "treatment"    varchar(50) NOT NULL,
    "weather"    varchar(50) NOT NULL,
    "soil"    varchar(50) NOT NULL,
    "stationtype"    TEXT NOT NULL,
    "startyear"    INTEGER NOT NULL,
    "endyear"    INTEGER NOT NULL,
    "odate"    INTEGER,
    "waterstress"    INTEGER,
    "nitrostress"    INTEGER,
	"tempVar"	INTEGER DEFAULT 0,
	"rainVar"	INTEGER DEFAULT 0,
	"CO2Var"	INTEGER DEFAULT 0,
    PRIMARY KEY("id" AUTOINCREMENT)
);
DROP TABLE IF EXISTS "InseaIrri";
CREATE TABLE "inSeaIrri" (
	"ID"	INTEGER,
	"inSeaDate"	TEXT,
	"inSea_irrAmt"	INTEGER,
	PRIMARY KEY("ID")
);

COMMIT;