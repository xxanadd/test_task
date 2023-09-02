create table if not exists microorganisms
(
    Blank int,
    ID_microorganisms int primary key,
    ID_Taxon int,
    TaxonName varchar(255),
    ID_Group int,
    ID_SubGroup float,
    Quantity float8,
    Units text,
    Significance float8,
    Type_Of_Value varchar(255),
    Change_In_Abundance varchar(255),
    Relative_Change float8
);