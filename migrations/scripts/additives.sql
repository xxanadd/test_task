create table if not exists additives
(
    blank int,
    ID_Article int,
    DOI text,
    ID_Additive int primary key,
    ID_Supplement int,
    Additive_Type varchar(255),
    Ad_Category varchar(255),
    Composition text,
    Dose varchar(255),
    Frequency varchar(255),
    Ad_Consumption_Time varchar(255)
);

