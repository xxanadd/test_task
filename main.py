from fastapi import FastAPI, UploadFile, HTTPException, Body
import os
import pandas as pd
from io import StringIO
from sqlalchemy import create_engine
from models import DbParams, People, Task, ErrorDetailModel, Microorganisms, Additives

app = FastAPI()


test_db_params = DbParams("test_task_db", "postgres", "4545qzqz", "localhost", "5433")
docker_db_params = DbParams("test_task_db", "postgres", "password", "postgres-sql", "5432")

# prod: bool отвечает за то какая база выбрана, перед созданием образа docker необходимо установить в True
prod = False
if prod:
    engine = create_engine(
        f"postgresql://{docker_db_params.user}:{docker_db_params.password}@{docker_db_params.host}:{docker_db_params.port}/{docker_db_params.database}")
else:
    engine = create_engine(
        f"postgresql://{test_db_params.user}:{test_db_params.password}@{test_db_params.host}:{test_db_params.port}/{test_db_params.database}")
# Создание подключения
db = engine.connect().connection


async def refresh_materialized_view(view: str) -> None:
    """
    Обновляет view на свежие данные
    :param view: название view
    :return: None
    """
    cursor = db.cursor()
    query = f"REFRESH MATERIALIZED VIEW {view}"
    cursor.execute(query)
    db.commit()
    cursor.close()


@app.post("/add/csv")
async def create_table_from_csv(file: UploadFile) -> dict[str, str]:
    """
    Загружает csv файлы в базу данных, название фаила должно соответствовать названию существующей таблицы.
    Если таблицы с названием как у фаила нет то создает новую таблицу с таким названием.
    :param file: csv фаил
    :return: сообщение о выполнении/ошибке
    """
    # Проверяем, что загруженный файл - это CSV-файл
    if file.filename.endswith(".csv"):
        # Извлекаем имя файла без расширения
        table_name = os.path.splitext(file.filename)[0]

        # Читаем данные из CSV-файла
        csv_data = await file.read()
        csv_data = csv_data.decode("utf-8")

        # Преобразуем CSV-данные в pandas DataFrame
        df = pd.read_csv(StringIO(csv_data))
        if "Unnamed: 0" in df.columns:
            # Переименовываем колонку
            df = df.rename(columns={"Unnamed: 0": "blank"})

        # Переводим все названия в нижний регистр
        df.columns = df.columns.str.lower()

        try:
            # Создаем/обновляем таблицу с именем файла (без расширения) и структурой данных из DataFrame
            df.to_sql(table_name, engine, if_exists='append', index=False)
            return {"message": f"Таблица {table_name} обновлена успешно"}
        except Exception as e:
            error_detail = ErrorDetailModel(error_type="DatabaseError", message=str(e))
            raise HTTPException(status_code=500, detail=error_detail.__dict__)
    else:
        return {"error": "Файл должен быть в формате CSV"}


@app.post("/add/str/{table_name}")
async def create_table_from_str(table_name: str, data: str = Body(media_type="text/plain")) -> dict[str, str]:
    """
    Создает баззу данных из строки с синтаксисом csv
    :param table_name: определяет название таблицы, если такой таблицы нет то создает новую с таким названием
    :param data: Строка с синтаксисом csv
    :return: сообщение о выполнении/ошибке
    """
    # Проверяем, что table_name не является пустой строкой
    if not table_name:
        return {"error": "Имя таблицы не может быть пустым"}

    try:
        # Преобразуем строку с данными в pandas DataFrame
        df = pd.read_csv(StringIO(data))
        if "Unnamed: 0" in df.columns:
            # Переименовываем колонку
            df = df.rename(columns={"Unnamed: 0": "blank"})

        # Переводим все названия столбцов в нижний регистр
        df.columns = df.columns.str.lower()

        # Создаем/обновляем таблицу с указанным именем и структурой данных из DataFrame
        df.to_sql(table_name, engine, if_exists='append', index=False)
        return {"message": f"Таблица {table_name} обновлена успешно"}
    except Exception as e:
        error_detail = ErrorDetailModel(error_type="DatabaseError", message=str(e))
        raise HTTPException(status_code=500, detail=error_detail.__dict__)


@app.get("/get/{taxonname}", response_model=list[Task])
async def get_data(taxonname: str) -> list[Task]:
    """
    Выдает все записи из созданного view по имени таксона
    :param taxonname: имя таксона
    :return: list объектов класса Task
    """
    # Обновляем view task_table на свежие данные
    await refresh_materialized_view("task_table")
    cursor = db.cursor()
    query = "SELECT * FROM task_table WHERE taxonname = %s"
    value = (taxonname,)
    try:
        cursor.execute(query, value)
        data = cursor.fetchall()
        if data:
            task_list = []
            for row in data:
                task_list.append(Task(*row))
            return task_list
        else:
            raise HTTPException(status_code=404, detail="Data not found")
    except Exception as e:
        error_detail = ErrorDetailModel(error_type="DatabaseError", message=str(e))
        raise HTTPException(status_code=500, detail=error_detail.__dict__)
    finally:
        cursor.close()


@app.get("/get-all", response_model=list[Task])
async def get_all_data() -> list[Task]:
    """
    Выдает все записи из созданного view
    :return: list объектов класса Task
    """
    # Обновляем view task_table на свежие данные
    await refresh_materialized_view("task_table")
    cursor = db.cursor()
    query = "SELECT * FROM task_table"
    try:
        cursor.execute(query)
        data = cursor.fetchall()
        if data:
            task_list = []
            for row in data:
                task_list.append(Task(*row))
            return task_list
        else:
            raise HTTPException(status_code=404, detail="Data not found")
    except Exception as e:
        error_detail = ErrorDetailModel(error_type="DatabaseError", message=str(e))
        raise HTTPException(status_code=500, detail=error_detail.__dict__)
    finally:
        cursor.close()


@app.get("/people/get/{id}", response_model=People)
async def get_from_people(id: int) -> People:
    """
    Возвращает запись из таблицы people по id_article
    :param id: id_article
    :return: Объект класса People
    """
    cursor = db.cursor()
    query = "SELECT * FROM people WHERE id_article = %s"
    value = (id,)
    try:
        cursor.execute(query, value)
        data = cursor.fetchone()
        if data:
            return People(*data)
        else:
            raise HTTPException(status_code=404, detail="Data not found")
    except Exception as e:
        error_detail = ErrorDetailModel(error_type="DatabaseError", message=str(e))
        raise HTTPException(status_code=500, detail=error_detail.__dict__)
    finally:
        cursor.close()


@app.get("/microorganisms/get/{id}", response_model=Microorganisms)
async def get_from_microorganisms(id: int) -> Microorganisms:
    """
    Возвращает запись из таблицы microorganisms по id_microorganisms
    :param id: id_microorganisms
    :return: Объект класса Microorganisms
    """
    cursor = db.cursor()
    query = "SELECT * FROM microorganisms WHERE id_microorganisms = %s"
    value = (id,)
    try:
        cursor.execute(query, value)
        data = cursor.fetchone()
        if data:
            return Microorganisms(*data)
        else:
            raise HTTPException(status_code=404, detail="Data not found")
    except Exception as e:
        error_detail = ErrorDetailModel(error_type="DatabaseError", message=str(e))
        raise HTTPException(status_code=500, detail=error_detail.__dict__)
    finally:
        cursor.close()


@app.get("/additives/get/{id}", response_model=Additives)
async def get_from_additives(id: int) -> Additives:
    """
    Возвращает запись из таблицы additives по id_additive
    :param id: id_additive
    :return: Объект класса Additives
    """
    cursor = db.cursor()
    query = "SELECT * FROM additives WHERE id_additive = %s"
    value = (id,)
    try:
        cursor.execute(query, value)
        data = cursor.fetchone()
        if data:
            return Additives(*data)
        else:
            raise HTTPException(status_code=404, detail="Data not found")
    except Exception as e:
        error_detail = ErrorDetailModel(error_type="DatabaseError", message=str(e))
        raise HTTPException(status_code=500, detail=error_detail.__dict__)
    finally:
        cursor.close()


@app.delete("/people/delete/{id}")
async def delete_from_people(id: int) -> dict[str, str]:
    """
    Удаляет запись из таблицы people по id_article
    :param id: id_article
    :return: сообщение о выполнении/ошибке
    """
    cursor = db.cursor()
    query = "DELETE FROM people WHERE id_article = %s"
    value = (id,)
    try:
        cursor.execute(query, value)
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Person not found")
        else:
            return {"message": "Data deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting person: {str(e)}")
    finally:
        cursor.close()


@app.delete("/microorganisms/delete/{id}")
async def delete_from_microorganisms(id: int) -> dict[str, str]:
    """
    Удаляет запись из таблицы microorganisms по id_microorganisms
    :param id: id_microorganisms
    :return: сообщение о выполнении/ошибке
    """
    cursor = db.cursor()
    query = "DELETE FROM microorganisms WHERE id_microorganisms = %s"
    value = (id,)
    try:
        cursor.execute(query, value)
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Microorganism not found")
        else:
            return {"message": "Data deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting microorganism: {str(e)}")
    finally:
        cursor.close()


@app.delete("/additives/delete/{id}")
async def delete_from_additives(id: int) -> dict[str, str]:
    """
    Удаляет запись из таблицы additives по id_additive
    :param id: id_additive
    :return: сообщение о выполнении/ошибке
    """
    cursor = db.cursor()
    query = "DELETE FROM additives WHERE id_additive = %s"
    value = (id,)
    try:
        cursor.execute(query, value)
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Additive not found")
        else:
            return {"message": "Data deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting additive: {str(e)}")
    finally:
        cursor.close()


@app.put("/people/update")
async def update_people(people: People) -> dict[str, str]:
    """
    Обновляет таблицу people по id_article
    :param people: Объект класса People
    :return: сообщение о выполнении/ошибке
    """
    cursor = db.cursor()
    query = ("UPDATE people SET blank = %s,doi = %s,id_group = %s,id_subgroup = %s,"
             "control_experimental = %s,id_disease = %s,id_drug = %s,intakeperiod = %s,id_additive = %s,id_diet = %s,"
             "id_activity = %s,physique_level = %s,sex = %s,age_min = %s,age_max = %s,physique_stage = %s,weight_min "
             "= %s,weight_max = %s,bmi_min = %s,bmi_max = %s,country = %s,alcohol = %s,smoking = %s,"
             "pregnancy_lactation = %s,additional_information = %s,author = %s WHERE id_article = %s")
    value = (people.Blank, people.DOI, people.ID_Group, people.ID_SubGroup,
             people.Control_Experimental, people.ID_Disease, people.ID_Drug, people.IntakePeriod, people.ID_Additive,
             people.ID_Diet, people.ID_Activity, people.Physique_Level, people.Sex, people.Age_Min, people.Age_Max,
             people.Physique_stage, people.Weight_Min, people.Weight_Max, people.BMI_Min, people.BMI_Max,
             people.Country, people.Alcohol, people.Smoking, people.Pregnancy_Lactation, people.Additional_information,
             people.Author, people.ID_Article)
    try:
        cursor.execute(query, value)
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Person not found")
        else:
            return {"message": "Data updated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating people: {str(e)}")
    finally:
        cursor.close()


@app.put("/microorganisms/update")
async def update_microorganisms(microorganisms: Microorganisms) -> dict[str, str]:
    """
    Обновляет таблицу microorganisms по id_microorganisms
    :param microorganisms: Объект класса Microorganisms
    :return: сообщение о выполнении/ошибке
    """
    cursor = db.cursor()
    query = ("UPDATE microorganisms SET blank = %s, id_taxon = %s, taxonname = %s, id_group = %s, id_subgroup = %s,"
             "quantity = %s, units = %s, significance = %s, type_of_value = %s, change_in_abundance = %s,"
             "relative_change = %s WHERE  id_microorganisms = %s")
    value = (microorganisms.Blank, microorganisms.ID_Taxon, microorganisms.TaxonName, microorganisms.ID_Group,
             microorganisms.ID_SubGroup, microorganisms.Quantity, microorganisms.Units, microorganisms.Significance,
             microorganisms.Type_Of_Value, microorganisms.Change_In_Abundance, microorganisms.Relative_Change,
             microorganisms.ID_microorganisms)
    try:
        cursor.execute(query, value)
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Microorganism not found")
        else:
            return {"message": "Data updated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating microorganisms: {str(e)}")
    finally:
        cursor.close()


@app.put("/additives/update")
async def update_additives(additives: Additives) -> dict[str, str]:
    """
    Обновляет таблицу additives по id_additive
    :param additives: Объект класса Additives
    :return: сообщение о выполнении/ошибке
    """
    cursor = db.cursor()
    query = ("UPDATE additives SET blank = %s, id_article = %s, doi = %s, id_supplement = %s,"
             "additive_type = %s, ad_category = %s, composition = %s, dose = %s, frequency = %s,"
             "ad_consumption_time = %s WHERE id_additive = %s")
    value = (additives.Blank, additives.ID_Article, additives.DOI, additives.ID_Supplement, additives.Additive_Type,
             additives.Ad_Category, additives.Composition, additives.Dose, additives.Frequency,
             additives.Ad_Consumption_Time, additives.ID_Additive)
    try:
        cursor.execute(query, value)
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Additive not found")
        else:
            return {"message": "Data updated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating additives: {str(e)}")
    finally:
        cursor.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
