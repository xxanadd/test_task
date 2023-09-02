from dataclasses import dataclass


@dataclass
class DbParams:
    database: str
    user: str
    password: str
    host: str
    port: str


@dataclass
class ErrorDetailModel:
    error_type: str
    message: str


@dataclass
class Task:
    taxonname: str
    composition: str
    change_in_abundance: str
    frequency: str
    additive_type: str


@dataclass
class People:
    Blank: int
    ID_Article: int
    DOI: str
    ID_Group: int
    ID_SubGroup: float
    Control_Experimental: str
    ID_Disease: int
    ID_Drug: int
    IntakePeriod: str
    ID_Additive: int
    ID_Diet: int
    ID_Activity: int
    Physique_Level: str
    Sex: str
    Age_Min: float
    Age_Max: float
    Physique_stage: str
    Weight_Min: float
    Weight_Max: float
    BMI_Min: float
    BMI_Max: float
    Country: str
    Alcohol: str
    Smoking: str
    Pregnancy_Lactation: str
    Additional_information: str
    Author: str


@dataclass
class Microorganisms:
    Blank: int
    ID_microorganisms: int
    ID_Taxon: int
    TaxonName: str
    ID_Group: int
    ID_SubGroup: float
    Quantity: float
    Units: str
    Significance: float
    Type_Of_Value: str
    Change_In_Abundance: str
    Relative_Change: float


@dataclass
class Additives:
    Blank: int
    ID_Article: int
    DOI: str
    ID_Additive: int
    ID_Supplement: int
    Additive_Type: str
    Ad_Category: str
    Composition: str
    Dose: str
    Frequency: str
    Ad_Consumption_Time: str
